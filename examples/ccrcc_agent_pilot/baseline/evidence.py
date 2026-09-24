"""Bounded public API retrieval, raw byte cache and provenance; reruns use cache."""
import json,hashlib,datetime,urllib.request,urllib.parse,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
P=Path(__file__).resolve().parent;S=P/'sources';S.mkdir(exist_ok=True)
records=[]
def fetch(name,url,payload=None):
 path=S/(name+'.json'); metap=S/(name+'.provenance.json')
 if path.exists() and metap.exists():
  raw=path.read_bytes();meta=json.loads(metap.read_text());records.append(meta)
  try:return json.loads(raw)
  except:return None
 data=json.dumps(payload).encode() if payload else None
 req=urllib.request.Request(url,data=data,headers={'User-Agent':'ccRCC-exploratory-research/1.0','Content-Type':'application/json','Accept':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=35) as r:raw=r.read();status=r.status
 except Exception as e:
  raw=json.dumps({'retrieval_error':str(e)}).encode();status='error'
 path.write_bytes(raw);meta=dict(name=name,url=url,method='POST' if data else 'GET',request=payload,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status=status,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),file=str(path.relative_to(P)));metap.write_text(json.dumps(meta,indent=2));records.append(meta)
 try:return json.loads(raw)
 except:return None
res=json.loads((P/'results.json').read_text());genes=res['shortlist']
def uni(g):
 q=urllib.parse.urlencode(dict(query=f'gene_exact:{g} AND organism_id:9606 AND reviewed:true',format='json',size=5,fields='accession,gene_names,protein_name,xref_ensembl,xref_reactome'))
 return g,fetch('uniprot_'+g,'https://rest.uniprot.org/uniprotkb/search?'+q)
ann={}
with ThreadPoolExecutor(max_workers=3) as pool:
 for g,d in pool.map(uni,genes):
  rr=(d or {}).get('results',[]); exact=[r for r in rr if any((x.get('geneName',{}).get('value')==g or any(y.get('value')==g for y in x.get('synonyms',[]))) for x in r.get('genes',[]))]
  if len(exact)!=1:ann[g]={'status':'unresolved or ambiguous','hit_count':len(exact)};continue
  r=exact[0];xrefs=r.get('uniProtKBCrossReferences',[]); ens=sorted(set(p['value'].split('.')[0] for x in xrefs if x['database']=='Ensembl' for p in x.get('properties',[]) if p['key']=='GeneId'))
  ann[g]=dict(status='unique reviewed human primary-symbol or synonym match',current_symbol=r.get('genes',[{}])[0].get('geneName',{}).get('value'),accession=r['primaryAccession'],protein=r.get('proteinDescription',{}),ensembl_gene_ids=ens,reactome=[x for x in xrefs if x['database']=='Reactome'])
query='query($id:String!){target(ensemblId:$id){id approvedSymbol tractability{label modality value} drugAndClinicalCandidates{count rows{id maxClinicalStage drug{id name}}}}}'
for g in ['CA9','VEGFA','MTOR']:
 ids=ann.get(g,{}).get('ensembl_gene_ids',[])
 if len(ids)==1:ann[g]['open_targets']=fetch('opentargets_'+g,'https://api.platform.opentargets.org/api/v4/graphql',dict(query=query,variables={'id':ids[0]}))
queries={
 'ca9_independent':'TITLE_ABS:(girentuximab AND ZIRCON)',
 'nnmt_independent':'TITLE_ABS:(NNMT AND renal AND carcinoma)',
 'mtor_independent':'EXT_ID:17476008 AND SRC:MED',
 'vegf_independent':'EXT_ID:17215529 AND SRC:MED'
}
for name,q in queries.items():
 fetch(name,'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode(dict(query=q,format='json',pageSize=3,resultType='core',sort='RELEVANCE')))
(S/'annotations.json').write_text(json.dumps(ann,indent=2));(S/'source_manifest.json').write_text(json.dumps(sorted(records,key=lambda x:x['name']),indent=2))
print(json.dumps({'annotations':{g:{k:v for k,v in a.items() if k in ['status','accession','ensembl_gene_ids']} for g,a in ann.items()},'retrievals':[{'name':r['name'],'status':r['status'],'bytes':r['bytes']} for r in records]},indent=2))
