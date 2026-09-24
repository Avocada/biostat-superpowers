import json, tempfile, unittest
from pathlib import Path
from biostat_mcp.core import Toolkit, ServiceError
from biostat_mcp.omics import OmicsService, LIMIT

class OmicsTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.tk=Toolkit(Path(self.t.name))
    def tearDown(self):self.t.cleanup()
    def test_mapping_and_provenance(self):
        entry={'primaryAccession':'Q1','genes':[{'geneName':{'value':'TEST'}}],'uniProtKBCrossReferences':[{'database':'Ensembl','id':'ENST00000000001','properties':[{'key':'GeneId','value':'ENSG00000000001.2'}]},{'database':'Reactome','id':'R-HSA-1','properties':[{'key':'PathwayName','value':'Test'}]}]}
        s=OmicsService(self.tk,lambda u,b:json.dumps({'results':[entry,entry]}).encode());r=s.proteins(['TEST'])
        self.assertTrue(r['records'][0]['ambiguous']);self.assertEqual(r['records'][0]['matches'][0]['ensembl_gene_ids'],['ENSG00000000001'])
        self.assertEqual(r['artifact']['kind'],'omics_evidence');self.assertIn(b'Q1',self.tk._read(r['artifact']['artifact_id'],'TEST.json'))
    def test_validation_and_offline(self):
        s=OmicsService(self.tk,lambda *a:self.fail('network should not run'))
        for genes in [[],['x OR *'],['../x'],['X']*11]:
            with self.assertRaises(ServiceError):s.proteins(genes)
        with self.assertRaises(ServiceError):s.target('ENSG1')
        self.tk.offline=True
        with self.assertRaises(ServiceError):s.proteins(['CA9'])
    def test_bad_responses(self):
        for raw in [b'bad',b'[]',b'{"errors":["bad"]}',b'x'*(LIMIT+1),b'{}']:
            with self.subTest(raw=raw[:30]),self.assertRaises(ServiceError):OmicsService(self.tk,lambda u,b:raw).proteins(['CA9'])
    def test_target_snapshot(self):
        s=OmicsService(self.tk,lambda u,b:json.dumps({'data':{'target':{'id':b['variables']['id'],'approvedSymbol':'CA9','drugAndClinicalCandidates':{'count':11,'rows':[]}}}}).encode())
        r=s.target('ENSG00000107159');self.assertEqual(r['target']['drugAndClinicalCandidates']['count'],11)
        self.assertIn('query.json',r['artifact']['files'])
    def test_actual_protocol_offline_guard(self):
        import asyncio,sys
        from mcp import Client,StdioServerParameters
        async def run():
            async with Client(StdioServerParameters(command=sys.executable,args=['-m','biostat_mcp.server','--offline','--artifact-dir',self.t.name])) as c:
                r=await c.call_tool('annotate_proteins',{'symbols':['CA9']});self.assertTrue(r.is_error)
                body=r.structured_content or json.loads(r.content[0].text);self.assertEqual(body['error']['code'],'offline')
        asyncio.run(run())
