"""Publish aggregate pilot artifacts without patient rows or raw model transcripts."""
import argparse, collections, hashlib, html, json, shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('study',type=Path);p.add_argument('destination',type=Path);args=p.parse_args()
r=args.study;out=args.destination;out.mkdir(parents=True,exist_ok=True)
metrics=[];calls=[]
for arm in ['baseline','upgraded']:
 dest=out/arm;dest.mkdir(exist_ok=True)
 for phase in ['initial','followup']:
  log=r/f'{arm}_{phase}.jsonl'
  events=[json.loads(s) for s in log.read_text().splitlines() if s.strip()]
  completed=[e['usage'] for e in events if e['type']=='turn.completed']
  ex=json.loads((r/f'{arm}_{phase}_execution.json').read_text())
  counts=collections.Counter(e.get('item',{}).get('type') for e in events if e['type']=='item.completed')
  row={'arm':arm,'phase':phase,'seconds':ex['seconds'],'returncode':ex['returncode'],'timeout':ex['timeout'],'usage':completed[-1] if completed else None,'completed_items':dict(counts)}
  if row['usage']:row['usage']['uncached_input_tokens']=row['usage']['input_tokens']-row['usage'].get('cached_input_tokens',0)
  metrics.append(row)
  for e in events:
   item=e.get('item',{})
   if e['type']=='item.completed' and item.get('type')=='mcp_tool_call':calls.append({'arm':arm,'phase':phase,**{k:item.get(k) for k in ['server','tool','arguments','status']}})
 # Files are aggregate output or code; never copy input, SQLite, raw JSONL or MCP data snapshots.
 for f in (r/arm).iterdir():
  if f.is_file() and f.suffix in ['.html','.md','.json','.py','.txt','.png','.svg','.csv'] and f.name not in ['AGENTS.md']:
   shutil.copy2(f,dest/f.name)
 shutil.copytree(r/arm/'figures',dest/'figures',dirs_exist_ok=True)
 for directory in ['followup_figures','tables']:
  if (r/arm/directory).exists():shutil.copytree(r/arm/directory,dest/directory,dirs_exist_ok=True)
 # The MCP histogram is an aggregate image, and its provenance is safe to publish.
 if arm=='upgraded':
  for d in (r/arm/'mcp_artifacts').iterdir():
   if (d/'figure.png').exists():
    shutil.copy2(d/'figure.png',dest/'figures/mcp_age_histogram.png')
    shutil.copy2(d/'provenance.json',dest/'mcp_chart_provenance.json')
for f in r.glob('*prompt.txt'):shutil.copy2(f,out/f.name)
for name in ['protocol.json','independent_review.md']:
 if (r/name).exists():shutil.copy2(r/name,out/name)
(out/'telemetry.json').write_text(json.dumps(metrics,indent=2)+'\n')
(out/'mcp_calls.json').write_text(json.dumps(calls,indent=2)+'\n')
# Verify that a followup did not alter the initial primary outputs.
preserved={}
for arm in ['baseline','upgraded']:
 snap=r/(arm+'_initial_snapshot');checks={}
 for f in [snap/'report.html',snap/'results.json',*list((snap/'figures').glob('*'))]:
  current=r/arm/f.relative_to(snap)
  checks[str(f.relative_to(snap))]=current.exists() and hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256(current.read_bytes()).digest()
 preserved[arm]=checks
(out/'initial_preservation.json').write_text(json.dumps(preserved,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
print('initial preserved:',all(all(v.values()) for v in preserved.values()))
