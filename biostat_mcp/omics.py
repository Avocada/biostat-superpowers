"""Bounded reviewed-human protein annotation; no participant data are uploaded."""
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from urllib.error import URLError
from .core import ServiceError, NoRedirect, download_bounded, json_bytes

UNIPROT = 'https://rest.uniprot.org/uniprotkb/search'
OT = 'https://api.platform.opentargets.org/api/v4/graphql'
LIMIT = 2 * 1024 * 1024

def fetch_json(url, body=None):
    if body is None:
        if not url.startswith(UNIPROT + '?'):
            raise ServiceError('invalid_source', 'Unsupported source')
        return download_bounded(url, 'UniProt', LIMIT)
    if url != OT:
        raise ServiceError('invalid_source', 'Unsupported source')
    try:
        request=Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','User-Agent':'biostat-superpowers/0.2.0'})
        with build_opener(NoRedirect).open(request,timeout=20) as r:
            raw=r.read(LIMIT+1)
        if len(raw)>LIMIT:raise ServiceError('size_limit','Open Targets response exceeds limit')
        return raw
    except (URLError,TimeoutError,OSError) as e:
        raise ServiceError('source_unavailable','Open Targets request failed',True) from e

class OmicsService:
    def __init__(self, toolkit, fetch=fetch_json):
        self.tk,self.fetch=toolkit,fetch

    def _json(self,url,body=None):
        if self.tk.offline:raise ServiceError('offline','Network disabled')
        raw=self.fetch(url,body)
        if len(raw)>LIMIT:raise ServiceError('size_limit','Response too large')
        try:
            obj=json.loads(raw)
            if not isinstance(obj,dict) or obj.get('errors'):raise ValueError('invalid envelope')
        except (ValueError,TypeError) as e:raise ServiceError('malformed_source','Invalid provider response') from e
        return raw,obj

    def proteins(self,symbols):
        if (not isinstance(symbols,list) or not 1<=len(symbols)<=10 or
            any(not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,29}',s) for s in symbols)):
            raise ServiceError('invalid_request','Provide 1–10 plain human gene symbols')
        symbols=list(dict.fromkeys(symbols));records=[];payloads={};queries=[]
        for symbol in symbols:
            url=UNIPROT+'?'+urlencode({'query':f'gene_exact:{symbol} AND organism_id:9606 AND reviewed:true','format':'json','size':5,'fields':'accession,gene_names,protein_name,xref_ensembl,xref_reactome'})
            raw,obj=self._json(url);payloads[symbol+'.json']=raw;queries.append(url)
            entries=obj.get('results')
            if not isinstance(entries,list):raise ServiceError('malformed_source','UniProt results missing')
            matches=[]
            for e in entries:
                refs=e.get('uniProtKBCrossReferences',[]);gene_ids=set();pathways=[]
                for ref in refs:
                    if ref.get('database')=='Ensembl':
                        gene_ids.update(p['value'].split('.')[0] for p in ref.get('properties',[]) if p.get('key')=='GeneId')
                    if ref.get('database')=='Reactome':
                        pathways.append({'id':ref['id'],'name':next((p['value'] for p in ref.get('properties',[]) if p.get('key')=='PathwayName'),'')})
                matches.append({'accession':e.get('primaryAccession'),'gene_names':[g.get('geneName',{}).get('value') for g in e.get('genes',[])],
                    'protein':e.get('proteinDescription',{}).get('recommendedName',{}).get('fullName',{}).get('value'),
                    'ensembl_gene_ids':sorted(gene_ids),'reactome_pathways':pathways[:20],'pathway_count':len(pathways)})
            records.append({'query_symbol':symbol,'matches':matches,'ambiguous':len(matches)!=1,'possibly_truncated':len(matches)==5})
        payloads['summary.json']=json_bytes(records)
        artifact=self.tk._save('omics_evidence',payloads,{'provider':'UniProt','source_urls':queries,'notice':'Human reviewed entries; mappings can be ambiguous. Reactome cross-references are annotations, not enrichment tests. Response is capped at five entries per symbol and twenty pathways per entry; retain raw snapshot for complete returned annotations.'})
        return {'artifact':artifact,'records':records}

    def target(self,ensembl_id):
        if not isinstance(ensembl_id,str) or not re.fullmatch(r'ENSG[0-9]{11}',ensembl_id):
            raise ServiceError('invalid_request','Expected an unversioned human Ensembl gene ID')
        query='''query($id:String!){target(ensemblId:$id){id approvedSymbol tractability{label modality value} drugAndClinicalCandidates{count rows{id maxClinicalStage drug{id name}}}}}'''
        body={'query':query,'variables':{'id':ensembl_id}};raw,obj=self._json(OT,body)
        data=obj.get('data',{}).get('target')
        if data is None:raise ServiceError('not_found','No Open Targets target returned')
        artifact=self.tk._save('omics_evidence',{'response.json':raw,'query.json':json_bytes(body)},
            {'provider':'Open Targets','source_urls':[OT],'ensembl_id':ensembl_id,'notice':'First ten drug records across all indications, not kidney-specific efficacy. Count may exceed returned rows. Evidence may overlap literature. Retrieval date/hash pins snapshot, not database release.'})
        summary=dict(data)
        candidates=data.get('drugAndClinicalCandidates')
        if candidates is not None:
            summary['drugAndClinicalCandidates']={**candidates,'rows':candidates.get('rows',[])[:10]}
        return {'artifact':artifact,'target':summary}
