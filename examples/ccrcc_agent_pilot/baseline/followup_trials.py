#!/usr/bin/env python3
"""Two bounded registry concepts; cached responses reused on rerun."""
import json,hashlib,datetime,urllib.request,urllib.parse,concurrent.futures
from pathlib import Path
P=Path(__file__).resolve().parent;S=P/'followup_sources';S.mkdir(exist_ok=True)
queries={'CA9':{'query.cond':'kidney cancer','query.term':'CA9 OR girentuximab'},'NNMT':{'query.cond':'kidney cancer','query.term':'NNMT OR "nicotinamide N-methyltransferase"'}}
def fetch(item):
 name,params=item;params.update(pageSize=50,countTotal='true',format='json');url='https://clinicaltrials.gov/api/v2/studies?'+urllib.parse.urlencode(params);f=S/f'trials_{name}.json';pr=S/f'trials_{name}.provenance.json'
 if f.exists() and pr.exists():return json.loads(pr.read_text())
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ccRCC-exploratory-study/1.0'}),timeout=35) as r: b=r.read();status=r.status
 except Exception as exc:b=json.dumps({'error':str(exc)}).encode();status='error'
 f.write_bytes(b);rec={'concept':name,'url':url,'retrieved_utc':now,'status':status,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'file':str(f.relative_to(P))};pr.write_text(json.dumps(rec,indent=2));return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: requests=list(pool.map(fetch,queries.items()))
records=[];searches=[]
for req in requests:
 d=json.loads((P/req['file']).read_text());searches.append({**req,'total_count':d.get('totalCount'),'returned':len(d.get('studies',[])),'truncated':bool(d.get('nextPageToken'))})
 for s in d.get('studies',[]):
  p=s['protocolSection'];i=p['identificationModule'];status=p['statusModule'];design=p.get('designModule',{});inter=p.get('armsInterventionsModule',{}).get('interventions',[])
  records.append({'concept':req['concept'],'nct_id':i['nctId'],'title':i['briefTitle'],'url':'https://clinicaltrials.gov/study/'+i['nctId'],'status':status.get('overallStatus'),'last_update_posted':status.get('lastUpdatePostDateStruct'),'last_verified':status.get('statusVerifiedDate'),'start':status.get('startDateStruct'),'completion':status.get('completionDateStruct'),'phases':design.get('phases',[]),'study_type':design.get('studyType'),'primary_purpose':design.get('designInfo',{}).get('primaryPurpose'),'conditions':p.get('conditionsModule',{}).get('conditions',[]),'interventions':inter,'brief_summary':p.get('descriptionModule',{}).get('briefSummary'),'has_results':s.get('hasResults'),'retrieved_utc':req['retrieved_utc'],'source_file':req['file']})
old=json.loads((P/'sources/source_manifest.json').read_text())
for r in old:
 assert hashlib.sha256((P/r['file']).read_bytes()).hexdigest()==r['sha256']
context={'new_requests':searches,'trial_records':records,'reused_source_manifest':old,'reused_annotations':['sources/annotations.json','sources/target_evidence_matrix.json','sources/evidence_records.json'],'concept_provenance':{'CA9':'Gene from original shortlist; girentuximab agent-target association verified in cached sources/opentargets_CA9.json and sources/ca9_zircon.json. No invented agent aliases.','NNMT':'Gene and nicotinamide N-methyltransferase name verified in cached sources/uniprot_NNMT.json. No verified targeting agent supplied, so none invented.'},'bounds':'Two kidney-cancer concepts, one request each, maximum 50 records per concept, no pagination; query.term searches all record fields and relevance must be reviewed. Search failure or zero hits does not establish absence of trials.','interpretation':'Registry phase/status and posted results availability are not efficacy estimates. New status/date fields are read from retrieved registry records; sponsor-reported and potentially stale.'}
(P/'context_sources.json').write_text(json.dumps(context,indent=2));print(json.dumps({'searches':searches,'trials':[{k:r[k] for k in ['nct_id','title','status','phases','primary_purpose','last_update_posted']} for r in records]},indent=2))
