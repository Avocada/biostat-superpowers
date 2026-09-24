"""Collect aggregate paired-agent results, without raw matrices or model transcripts."""
from pathlib import Path
import argparse,json,shutil,collections,hashlib
p=argparse.ArgumentParser();p.add_argument('study',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=a.study;o=a.output;o.mkdir(parents=True,exist_ok=True)
metrics=[];calls=[];copied=[]
for arm in ['baseline','upgraded']:
 d=o/arm;d.mkdir(exist_ok=True)
 for phase in ['initial','followup']:
  events=[json.loads(s) for s in (r/f'{arm}_{phase}.jsonl').read_text().splitlines()]
  usages=[e['usage'] for e in events if e['type']=='turn.completed'];usage=usages[-1] if usages else None
  if usage:usage['uncached_input_tokens']=usage['input_tokens']-usage.get('cached_input_tokens',0)
  ex=json.loads((r/f'{arm}_{phase}_execution.json').read_text())
  metrics.append({'arm':arm,'phase':phase,'seconds':ex['seconds'],'returncode':ex['returncode'],'timeout':ex['timeout'],'usage':usage,'completed_items':dict(collections.Counter(e.get('item',{}).get('type') for e in events if e['type']=='item.completed'))})
  for e in events:
   i=e.get('item',{})
   if e['type']=='item.completed' and i.get('type')=='mcp_tool_call':calls.append({'arm':arm,'phase':phase,**{k:i.get(k) for k in ['server','tool','arguments','status']},'ok':(i.get('result',{}).get('structured_content') or {}).get('ok')})
 for f in (r/arm).rglob('*'):
  rel=f.relative_to(r/arm)
  if not f.is_file() or any(x in rel.parts for x in ['input','sources','followup_sources','source_snapshots','mcp_artifacts','.mplcache','__pycache__','.git']):continue
  if f.suffix not in ['.html','.md','.json','.csv','.tsv','.py','.js','.png','.svg','.txt']:continue
  if f.name=='AGENTS.md' or 'preview' in f.name:continue
  if f.suffix in ['.csv','.tsv'] and any(x in f.read_text(errors='ignore') for x in ['C3N-','C3L-']):continue
  dst=d/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst);copied.append(str(Path(arm)/rel))
for pattern in ['*prompt.txt','protocol.json','review_protocol.md','independent_review.md','source_guide.md','common_environment.md','runtime_quickstart.md','setup_corrections.json','parent_preflight.json']:
 for f in r.glob(pattern):shutil.copy2(f,o/f.name)
(o/'telemetry.json').write_text(json.dumps(metrics,indent=2)+'\n');(o/'mcp_calls.json').write_text(json.dumps(calls,indent=2)+'\n')
preserved={}
for arm in ['baseline','upgraded']:
 snap=r/(arm+'_initial_snapshot');checks={}
 files=[snap/'report.html',snap/'results.json']+[f for f in snap.rglob('*') if f.suffix in ['.png','.svg'] and '.mplcache' not in f.parts]
 for f in files:
  if f.is_file():
   cur=r/arm/f.relative_to(snap);checks[str(f.relative_to(snap))]=cur.exists() and hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256(cur.read_bytes()).digest()
 preserved[arm]=checks
(o/'initial_preservation.json').write_text(json.dumps(preserved,indent=2)+'\n');print(json.dumps(metrics,indent=2));print('preserved',all(all(v.values()) for v in preserved.values()))
