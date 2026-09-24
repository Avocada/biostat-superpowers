#!/usr/bin/env python3
"""Offline follow-up. Run with supplied Python and runtime PYTHONPATH; no original outputs overwritten."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['MPLCONFIGDIR']=os.path.abspath('.mplconfig')
import ast,json,hashlib,base64,warnings,platform
from pathlib import Path
from dataclasses import asdict
import numpy as np,pandas as pd,sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from biostat_workflow.memory import MemoryStore
from biostat_workflow.controller import WorkflowState,Goal,Stage,Outcome,Result,Policy,route,advance,settle
ROOT=Path(__file__).resolve().parent;os.chdir(ROOT)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v)))
manifest=json.loads(Path('artifact-manifest.json').read_text())
checks={p:sha(p)==m['sha256'] for p,m in manifest.items() if p!='project-memory.sqlite3'}
assert all(checks.values()),[p for p,v in checks.items() if not v]
protected={p:sha(p) for p in ['report.html','results.json']+[str(p) for p in Path('figures').glob('*')]}
contract=json.loads(Path('analysis-contract.json').read_text());fp=contract.pop('input_fingerprint');contract.pop('run_id')
actual=hashlib.sha256((sha('input/rhc.csv')+sha('input/rhc_dictionary.html')+sha('input/legacy_analysis.py')+json.dumps(contract,sort_keys=True)).encode()).hexdigest();assert actual==fp
with MemoryStore(Path('project-memory.sqlite3'),'rhc-upgraded-pilot') as mem:
 retrieval=mem.retrieve(goal=Goal.INFERENTIAL,stage=Stage.ANALYSIS,input_fingerprint=fp,required_keys=('scope','timing','profile','source'),max_units=12000,count=lambda s:len(s.encode('utf-8')))
 assert retrieval.usable,retrieval.issues
old=json.loads(Path('results.json').read_text());prior=json.loads(Path('workflow-transitions.json').read_text())
d=pd.read_csv('input/rhc.csv');assert len(d)==5735 and d.ptid.notna().all() and d.ptid.is_unique
assert set(d.swang1)=={'RHC','No RHC'} and set(d.dth30)=={'Yes','No'}
t=(d.swang1=='RHC').to_numpy().astype(int);y=(d.dth30=='Yes').to_numpy().astype(int)
# Reuse only reviewed pure function definitions and original exclusion-list AST; never execute analysis.py top level.
tree=ast.parse(Path('analysis.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('design','fit','calc')]
assert len(nodes)==3
exec(compile(ast.Module(body=nodes,type_ignores=[]),'analysis.py:reused-functions','exec'))
drop=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='drop' for t in n.targets))
original_cov=[c for c in d if c not in drop];reduced_cov=[c for c in original_cov if c not in ['adld3p','urin1']]
assert 'cat2' in reduced_cov and len(original_cov)-len(reduced_cov)==2
cov=original_cov
full_x,full_xs=design(d)
rows=[];models={};balance_rows=[]
den=np.sqrt((full_xs[t==1].var(axis=0)+full_xs[t==0].var(axis=0))/2)
for label,cols in [('original',original_cov),('reduced',reduced_cov)]:
 cov=cols
 with warnings.catch_warnings(record=True) as caught:
  warnings.simplefilter('always');x,xs,ps,iters=fit(d,t)
 assert iters<5000 and np.isfinite(ps).all()
 models[label]={'adjustment_variables':cols,'encoded_terms':list(x.columns),'iterations':iters,'warnings':[str(w.message) for w in caught],'ps_range':[float(ps.min()),float(ps.max())],'ps_quantiles_by_group':{str(g):np.quantile(ps[t==g],[0,.01,.1,.5,.9,.99,1]).tolist() for g in [0,1]}}
 for cut in [.01,.02,.05]:
  est,w=calc(y,t,ps,cut)
  smd=np.divide(np.abs(np.average(full_xs[t==1],axis=0,weights=w[t==1])-np.average(full_xs[t==0],axis=0,weights=w[t==0])),den,out=np.zeros_like(den),where=den>0)
  for term,v in zip(full_x.columns,smd):balance_rows.append(dict(specification=label,clip=cut,term=term,abs_smd=float(v)))
  row=dict(specification=label,clip=cut,n=len(d),**est,rd_ci=None,rr_ci=None,clipped_n=int(((ps<cut)|(ps>1-cut)).sum()),max_weight=float(w.max()),ess={str(g):float(w[t==g].sum()**2/(w[t==g]**2).sum()) for g in [0,1]},max_abs_smd_all_original_terms=float(smd.max()),terms_above_01=int((smd>.1).sum()),omitted_term_smd={c:float(smd[list(full_x.columns).index(c)]) for c in ['adld3p','urin1']})
  rows.append(row)
comparison=[]
for cut in [.01,.02,.05]:
 a=next(r for r in rows if r['specification']=='original' and r['clip']==cut);b=next(r for r in rows if r['specification']=='reduced' and r['clip']==cut)
 saved=next(r for r in old['sensitivity'] if r['label']==f'PS clip {cut:g}')
 for key in ['rd','rr','risk_rhc','risk_no_rhc']:assert abs(a[key]-saved[key])<1e-10,(key,a[key],saved[key])
 comparison.append(dict(clip=cut,rd_change_percentage_points=100*(b['rd']-a['rd']),rr_change=b['rr']-a['rr']))
missing={c:{'n':int(d[c].isna().sum()),'percent':100*float(d[c].isna().mean())} for c in ['adld3p','urin1','cat2']}
profile=json.loads(Path('mcp_artifacts/c74883de0afd431daa369af1a4814b22/profile.json').read_text())
assert profile['data_sha256']==sha('input/rhc.csv') and profile['rows']==len(d)
for c,m in missing.items():assert next(v['missing'] for v in profile['variables'] if v['name']==c)==m['n']
Path('followup_figures').mkdir(exist_ok=True)
pd.DataFrame(balance_rows).to_csv('followup_balance.csv',index=False)
# Point-only plot; paired rows keep all annotations legible. Nulls displayed on both scales.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(12,5.6),sharey=True)
for ax,key,mul,null,title in [(axs[0],'rd',100,0,'Risk difference (percentage points)'),(axs[1],'rr',1,1,'Risk ratio (linear scale)')]:
 for j,cut in enumerate([.01,.02,.05]):
  for spec,off,color,marker in [('original',.13,'#176B86','o'),('reduced',-.13,'#B95D20','s')]:
   row=next(r for r in rows if r['specification']==spec and r['clip']==cut);v=row[key]*mul
   ax.scatter(v,2-j+off,s=65,color=color,marker=marker,label=spec.title() if j==0 else None)
   ax.annotate(f'{v:+.3f}' if key=='rd' else f'{v:.4f}',(v,2-j+off),xytext=(8,0),textcoords='offset points',va='center',color=color)
 ax.axvline(null,color='#77838B',ls='--',lw=1)
 ax.set(xlabel=title,yticks=[2,1,0],yticklabels=['Clip 0.01','Clip 0.02','Clip 0.05'],ylim=(-.5,2.5))
 ax.text(null,2.36,'Null',ha='center',fontsize=9,color='#65717A')
 ax.grid(axis='y',alpha=.2)
axs[0].set_xlim(-.35,7.1);axs[1].set_xlim(.99,1.235)
axs[1].legend(loc='upper left', bbox_to_anchor=(.10,.96));fig.suptitle('RHC and supplied 30-day mortality: adjustment sensitivity',fontweight='bold',fontsize=16)
fig.text(.5,.91,'All 5,735 patients • Reduced excludes only adld3p and urin1; cat2 retained',ha='center',fontsize=11)
fig.text(.5,.025,'Point estimates only; no intervals recalculated. Deleting potential confounders does not establish causal validity.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.07,1,.87),w_pad=3)
for ext in ['png','svg']:fig.savefig('followup_figures/adjustment_comparison.'+ext,dpi=170)
plt.close(fig)
# New bounded inferential sensitivity run; never resume or clear the stopped causal branch.
tr=[];s=WorkflowState(Goal.INFERENTIAL);pol=Policy(no_progress_limit=1)
for result in [Result(Outcome.COMPLETE,'User follow-up: compare two exploratory weighting specifications at 0.01, 0.02, 0.05; point estimates only.'),Result(Outcome.COMPLETE,'Input fingerprints and unique IDs/complete labels rechecked; all 5735 retained. Legacy single-imputation encoding is a fixed computational sensitivity, not an accepted causal missing-data plan.',missing_data_required=False),Result(Outcome.COMPLETE,'followup_results.json, followup_balance.csv: two propensity refits, six weighted estimates; original reproduced within 1e-10.'),Result(Outcome.BLOCKED,'Self-audit only; independent reviewer pending per user. No scientific approval or causal readiness.')]:
 s=settle(s,pol);r=route(s);a=advance(s,result,pol);tr.append({'before':asdict(s),'route':asdict(r),'result':asdict(result),'after':asdict(a)});s=a
save('followup_workflow.json',{'run_id':'rhc-followup-sparse-two-20260924','transitions':tr,'terminal':asdict(s),'prior_causal_terminal_preserved':prior['causal']['terminal'],'unresolved':prior['causal']['unresolved']})
result={'run_id':'rhc-followup-sparse-two-20260924','input_sha256':sha('input/rhc.csv'),'input_fingerprint':fp,'n':len(d),'n_rhc':int(t.sum()),'n_no_rhc':int((1-t).sum()),'missingness':missing,'specifications':models,'estimates':rows,'reduced_minus_original':comparison,'intervals':'Not calculated; no bootstrap or prior intervals reused','methods':'Original design/fit/calc functions reused from AST. pd.get_dummies(drop_first=True,dummy_na=False); numeric median then zero fill; StandardScaler; LogisticRegression(C=1,max_iter=5000), existing defaults; stabilized weights normalized within exposure groups; PS clipped to [c,1-c], no trimming.','model_parameters':LogisticRegression(max_iter=5000,C=1.0).get_params(),'causal_ready':False,'human_scientific_approval':False,'independent_review':'pending','prior_original_point_estimates_reproduced_tolerance':1e-10,'software':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__,'matplotlib':matplotlib.__version__}}
save('followup_results.json',result)
# Record honest analyst attribution; user requested sensitivity, not scientific confirmation.
with MemoryStore(Path('project-memory.sqlite3'),'rhc-upgraded-pilot') as mem:
 key='followup_exclude_adld3p_urin1'
 if not any(i.key==key for i in mem.inspect()):
  item=mem.record(run_id=result['run_id'],key=key,value='User requested exploratory sensitivity excluding only adld3p and urin1, retaining all 5735 and all other original choices including cat2. Two PS refits and six point estimates completed; no new intervals. Confounder deletion is not causal repair; timing, missingness, identification and independent review gates remain unresolved.',source='User follow-up request; followup_analysis.py; followup_results.json; followup_workflow.json',confirmed_by='Codex analyst: implementation and numerical checks reviewed; not user scientific approval or independent review',goal=Goal.INFERENTIAL,stages=(Stage.ANALYSIS,Stage.EVALUATION,Stage.REPORTING),input_fingerprint=fp,dependencies=tuple(i.item_id for i in retrieval.items))
 else:item=next(i for i in mem.inspect() if i.key==key)
 save('followup_memory_append.json',asdict(item))
assert all(sha(p)==h for p,h in protected.items())
files=['AGENTS.md','input/SOURCE.md','input/rhc.csv','input/rhc_dictionary.html','input/legacy_analysis.py','analysis-contract.json','analysis.py','results.json','decision-log.md','workflow-transitions.json','method-evaluation.json','validation.json','artifact-manifest.json','mcp_artifacts/c74883de0afd431daa369af1a4814b22/profile.json','mcp_artifacts/c74883de0afd431daa369af1a4814b22/manifest.json','mcp_artifacts/bfde5f6401c24b459b16d2c4258926ec/literature.json','mcp_artifacts/bfde5f6401c24b459b16d2c4258926ec/manifest.json','mcp_artifacts/3160fbf4c1c04a6b9240f701bb6582a7/source.json']
save('context_sources.json',{'input_sha256':result['input_sha256'],'composite_fingerprint':fp,'memory_log':'followup_memory_retrieval.json','selected_records':[{'key':i.key,'item_id':i.item_id,'source':i.source} for i in retrieval.items],'retrieved_context_utf8_bytes':retrieval.units,'not_model_tokens':True,'files_read':[{'path':p,'sha256':sha(p),'read_mode':'hash for fingerprint only' if p in ['input/rhc_dictionary.html','input/legacy_analysis.py'] else 'content'} for p in files],'hash_only_manifest_checks':checks,'protected_outputs_before_after':protected,'mcp':'Reused local MCP profile/literature/source artifacts; hashes matched original manifest; no network refetch or new MCP call. Host-staged source reference remains not independently verified.','memory_issues':'Initial raw-checksum lookup unavailable; resolved by reconstructing original composite fingerprint. Final required retrieval has no missing, stale, conflicting or omitted keys.','new_record':'followup_memory_append.json','policy_and_runtime_read':['/Users/amiee/.codex/skills/biostat-workflow/SKILL.md','/Users/amiee/.codex/skills/causal-inference/SKILL.md','/Users/amiee/.codex/skills/statistical-analysis/SKILL.md','/Users/amiee/.codex/skills/method-evaluation/SKILL.md','/Users/amiee/Projects_code/biostat-superpowers/docs/modernization/WORKFLOW_CONTROLLER.md','/Users/amiee/Projects_code/biostat-superpowers/docs/modernization/MEMORY.md','/Users/amiee/Projects_code/biostat-superpowers/biostat_workflow/memory.py']})
print(json.dumps({'estimates':rows,'changes':comparison,'missingness':missing},indent=2))
