import asyncio
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from biostat_mcp.core import Toolkit, ServiceError, digest

class LocalCSVTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.inputs=self.root/'inputs'; self.inputs.mkdir()
        self.raw=b'group,value\nA,1\nB,2\n'
        (self.inputs/'summary.csv').write_bytes(self.raw)
        self.tk=Toolkit(self.root/'artifacts',offline=True,input_dir=self.inputs)
    def tearDown(self): self.temp.cleanup()
    def test_disabled_without_directory(self):
        with self.assertRaises(ServiceError) as cm: Toolkit(self.root/'other').import_local_csv('summary.csv')
        self.assertEqual(cm.exception.code,'local_import_disabled')
    def test_snapshot_provenance(self):
        d=self.tk.import_local_csv('summary.csv','https://example.org/public-source')
        self.assertEqual(d['data_sha256'],digest(self.raw)); self.assertFalse(d['synthetic'])
        self.assertEqual(self.tk._read(d['artifact_id'],'data.csv'),self.raw)
        (self.inputs/'summary.csv').write_text('group,value\nA,99\n')
        self.assertEqual(self.tk.profile_dataset(d['artifact_id'])['profile']['rows'],2)
        self.assertFalse(json.loads(self.tk._read(d['artifact_id'],'source.json'))['reference_verified'])
    def test_traversal_symlink_and_bad_csv(self):
        (self.inputs/'link.csv').symlink_to(self.inputs/'summary.csv')
        for name in ['../summary.csv','/tmp/summary.csv','sub/summary.csv','link.csv','missing.csv']:
            with self.subTest(name=name),self.assertRaises(ServiceError): self.tk.import_local_csv(name)
        (self.inputs/'bad.csv').write_text(',x\n1,2\n')
        with self.assertRaises(ServiceError): self.tk.import_local_csv('bad.csv')
    def test_size_bound(self):
        from unittest.mock import patch
        with patch('biostat_mcp.core.MAX_BYTES',5),self.assertRaises(ServiceError): self.tk.import_local_csv('summary.csv')
    @unittest.skipUnless(importlib.util.find_spec('vl_convert'),'renderer required')
    def test_profile_render(self):
        d=self.tk.import_local_csv('summary.csv'); p=self.tk.profile_dataset(d['artifact_id'])['artifact']
        c=self.tk.render_chart(d['artifact_id'],p['artifact_id'],'bar','group','value')
        self.assertEqual(c['rows_used'],2)
        self.assertTrue(self.tk._read(c['artifact_id'],'figure.png').startswith(b'\x89PNG'))
    @unittest.skipUnless(importlib.util.find_spec('mcp'),'MCP required')
    def test_stdio_import(self):
        async def run():
            from mcp import Client,StdioServerParameters
            import sys
            async with Client(StdioServerParameters(command=sys.executable,args=['-m','biostat_mcp.server','--offline','--artifact-dir',str(self.root/'protocol'),'--input-dir',str(self.inputs)])) as client:
                r=await client.call_tool('import_local_csv',{'filename':'summary.csv'}); self.assertFalse(r.is_error)
                body=r.structured_content or json.loads(r.content[0].text)
                self.assertEqual(body['result']['data_sha256'],digest(self.raw))
        asyncio.run(run())
