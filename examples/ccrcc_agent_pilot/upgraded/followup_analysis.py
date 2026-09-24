#!/usr/bin/env python3
"""Offline sensitivity; revalidates input and retrieves original memory before fitting."""
import os,sys,json,hashlib,warnings,platform
from pathlib import Path
from dataclasses import asdict
os.environ['MPLCONFIGDIR']=str(Path('.mplcache').resolve())
sys.path.insert(0,'/Users/amiee/Projects_code/biostat-superpowers')
import numpy as np,pandas as pd,scipy
from scipy import stats
from biostat_workflow.memory import MemoryStore
from biostat_workflow.controller import Goal,Stage,WorkflowState,Result,Outcome,route,advance,settle
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False,default=str))
man=json.loads(Path('input/manifest.json').read_text());ctx=json.loads(Path('runtime_context.json').read_text());assert man['input_fingerprint']==ctx['input_fingerprint']
for f,v in man['files'].items():assert sha('input/'+f)==v['sha256'] and Path('input/'+f).stat().st_size==v['bytes']
cfg=json.loads(Path('analysis_config.json').read_text())
with MemoryStore(Path(ctx['memory']),ctx['project_id']) as m:
 r=m.retrieve(goal=Goal.INFERENTIAL,stage=Stage.ANALYSIS,input_fingerprint=ctx['input_fingerprint'],required_keys=('cohort','scales','missingness','model','shortlist','source interpretation'),max_units=8000,count=lambda x:len(x.encode('utf-8')))
 assert r.usable,r.issues
 for item in r.items:
  if item.key in ('cohort','scales','missingness','model','shortlist'):
   for k,v in json.loads(item.value).items():assert cfg[k]==v;cfg[k]=v
 # Original retrieval audit is immutable; record the current execution retrieval separately.
 save('followup_execution_memory.json',{'usable':r.usable,'issues':r.issues,'context_bytes':r.units,'records':json.loads(r.text)})
cfg.update(finite_fraction=.8,stage_source='input/clinical_annotation.csv',run_id='followup_stage');save('followup_config.json',cfg)
assert cfg['imputation'] is False and cfg['extra_log'] is False and cfg['min_pairs']==20
for d in ('followup_tables','followup_figures'):Path(d).mkdir(exist_ok=True)
cli=pd.read_csv(cfg['stage_source']).set_index('Case_ID');assert cli.index.is_unique
original=json.loads(Path('cohort_case_ids.json').read_text());assert len(original)==len(set(original))==72
stage=cli.loc[original,'Tumor_Stage_Pathological'];early=stage.index[stage.isin(['Stage I','Stage II'])].tolist()
cohorts={'all_stage':original,'stage_I_II':early};save('followup_cohorts.json',cohorts)
state=WorkflowState(goal=Goal.INFERENTIAL);audit=[]
def step(evidence,missing=None,blocked=False):
 global state
 state=settle(state);before=state;rr=route(state);res=Result(outcome=Outcome.BLOCKED if blocked else Outcome.COMPLETE,evidence=evidence,missing_data_required=missing);state=advance(state,res);audit.append({'before':asdict(before),'route':asdict(rr),'result':asdict(res),'after':asdict(state)});save('followup_controller_audit.json',audit)
step('Mean paired tumor-minus-normal observed-pair contrast in original cohort and its pathological Stage I/II subset. Retrieved decisions agree with original config; followup_config.json sha256='+sha('followup_config.json'))
data={}
for l,stem in [('protein','proteome'),('rna','RNAseq_fpkm_log2')]:
 for tissue in ['Tumor','Normal']:
  d=pd.read_csv(f'input/HS_CPTAC_CCRCC_{stem}_{tissue}.cct',sep='\t',index_col=0);assert d.index.is_unique and d.columns.is_unique;data[l,tissue]=d
sets=[set(d.columns)-set(cfg['exclude_histology'])-({cfg['exclude_normal']} if tissue=='Normal' else set()) for (l,tissue),d in data.items()];assert set.intersection(*sets)==set(original)
assert set(cli.index[cli.Histologic_Type!='Clear cell renal cell carcinoma'])==set(cfg['exclude_histology'])
step('Verified all nine input hashes/sizes; revalidated saved original 72-case intersection; authoritative stage exact match, 37 early cases. followup_cohorts.json',True)
step('No imputation. Per cohort/layer require >=ceil(0.8*N) finite tumor/normal pairs and >=20. Observed pairs may be abundance selected; MNAR remains unresolved.')
results={};diffs={};summary={};short=[];diagnostics=[];comparisons={};concordance={};checks=[]
for name,ids in cohorts.items():
 summary[name]={'cases':len(ids),'stage_counts':cli.loc[ids,'Tumor_Stage_Pathological'].value_counts(dropna=False).to_dict(),'threshold':max(20,int(np.ceil(.8*len(ids)))),'layers':{}}
 for l in ['protein','rna']:
  t=data[l,'Tumor'].loc[:,ids];n=data[l,'Normal'].reindex(t.index).loc[:,ids];a=t.to_numpy(float);b=n.to_numpy(float);ok=np.isfinite(a)&np.isfinite(b);d=np.where(ok,a-b,np.nan);num=ok.sum(1)
  with warnings.catch_warnings():
   warnings.simplefilter('ignore');mean=np.nanmean(d,1);sd=np.nanstd(d,axis=1,ddof=1)
  eligible=num>=summary[name]['threshold'];valid=eligible&(sd>0)&np.isfinite(sd)&np.isfinite(mean);se=sd/np.sqrt(np.maximum(num,1));pv=np.full(len(d),np.nan);lo=pv.copy();hi=pv.copy();q=pv.copy()
  pv[valid]=2*stats.t.sf(abs(mean[valid]/se[valid]),num[valid]-1);crit=stats.t.ppf((1+cfg['ci'])/2,num[valid]-1);lo[valid]=mean[valid]-crit*se[valid];hi[valid]=mean[valid]+crit*se[valid]
  idx=np.flatnonzero(valid);order=idx[np.argsort(pv[idx])];q[order]=np.minimum(1,np.minimum.accumulate((pv[order]*len(order)/np.arange(1,len(order)+1))[::-1])[::-1]);np.testing.assert_allclose(q[valid],stats.false_discovery_control(pv[valid]),rtol=1e-12)
  status=np.where(~eligible,'insufficient_pairs',np.where(sd==0,'zero_variance',np.where(valid,'tested','nonfinite_failure')))
  out=pd.DataFrame({'gene':t.index,'n':num,'finite_fraction':num/len(ids),'mean_difference':mean,'sd_difference':sd,'ci_low':lo,'ci_high':hi,'p_value':pv,'q_value':q,'status':status}).set_index('gene')
  out['absolute_effect_rank']=out.mean_difference.abs().where(valid).rank(ascending=False,method='min');out.to_csv(f'followup_tables/{name}_{l}.csv');results[name,l]=out;diffs[name,l]=d
  summary[name]['layers'][l]={'input_genes':len(out),'coverage_eligible':int(eligible.sum()),'tested':int(valid.sum()),'q_below_005':int((q<.05).sum()),'status_counts':out.status.value_counts().to_dict()}
  if name=='all_stage':
   old=pd.read_csv(f'tables/{l}_all_genes.csv').set_index('gene').loc[out.index];np.testing.assert_allclose(out.mean_difference,old.mean_difference,equal_nan=True,atol=1e-12);checks.append(l+': all-stage means identical to original; BH recomputed on restricted family')
  for g in cfg['prespecified']+cfg['selected_exploratory']:
   row=out.loc[g];short.append({'cohort':name,'layer':l,'gene':g,**row.to_dict()});v=d[out.index.get_loc(g)];v=v[np.isfinite(v)]
   if row.status=='tested':
    test=stats.ttest_1samp(v,0);ci=test.confidence_interval();np.testing.assert_allclose([row.p_value,row.ci_low,row.ci_high],[test.pvalue,ci.low,ci.high],rtol=1e-10,atol=1e-14)
    loo=(v.sum()-v)/(len(v)-1);diagnostics.append({'cohort':name,'layer':l,'gene':g,'skew':float(stats.skew(v)),'median':float(np.median(v)),'loo_min':float(loo.min()),'loo_max':float(loo.max()),'loo_direction_stable':bool(np.all(np.sign(loo)==np.sign(row.mean_difference)))})
 p=results[name,'protein'];sel=p[(p.n>=np.ceil(.9*len(ids)))&(p.q_value<.05)&(~p.index.isin(cfg['prespecified']))].assign(abs_effect=lambda x:x.mean_difference.abs()).sort_values(['abs_effect','gene'],ascending=[False,True]);summary[name]['reselected_exploratory']=sel.head(2).index.tolist();summary[name]['original_candidate_selection_ranks']={g:int(sel.index.get_loc(g)+1) if g in sel.index else None for g in cfg['selected_exploratory']}
 both=p[p.status=='tested'].join(results[name,'rna'].query('status=="tested"'),lsuffix='_protein',rsuffix='_rna',how='inner');concordance[name]={'both_tested':len(both),'same_direction_fraction':float((np.sign(both.mean_difference_protein)==np.sign(both.mean_difference_rna)).mean()),'spearman':float(stats.spearmanr(both.mean_difference_protein,both.mean_difference_rna).statistic)}
 # RNA complete: descriptive exact-four-finite paired contrasts remove gene-wise case imbalance.
 tp=data['protein','Tumor'].loc[both.index,ids].to_numpy(float);pn=data['protein','Normal'].loc[both.index,ids].to_numpy(float);tr=data['rna','Tumor'].loc[both.index,ids].to_numpy(float);rn=data['rna','Normal'].loc[both.index,ids].to_numpy(float);mask=np.isfinite(tp)&np.isfinite(pn)&np.isfinite(tr)&np.isfinite(rn);pm=np.nanmean(np.where(mask,tp-pn,np.nan),axis=1);rm=np.nanmean(np.where(mask,tr-rn,np.nan),axis=1);concordance[name]['same_finite_case_direction_fraction']=float((np.sign(pm)==np.sign(rm)).mean())
for l in ['protein','rna']:
 a=results['all_stage',l];b=results['stage_I_II',l];aa=set(a.index[a.status=='tested']);bb=set(b.index[b.status=='tested']);common=sorted(aa&bb);x=a.loc[common];y=b.loc[common];topa=set(x.mean_difference.abs().nlargest(100).index);topb=set(y.mean_difference.abs().nlargest(100).index)
 comparisons[l]={'shared_tested':len(common),'all_only':len(aa-bb),'early_only':len(bb-aa),'same_direction_n':int((np.sign(x.mean_difference)==np.sign(y.mean_difference)).sum()),'same_direction_fraction':float((np.sign(x.mean_difference)==np.sign(y.mean_difference)).mean()),'signed_effect_spearman':float(stats.spearmanr(x.mean_difference,y.mean_difference).statistic),'absolute_effect_spearman':float(stats.spearmanr(x.mean_difference.abs(),y.mean_difference.abs()).statistic),'top100_absolute_shared_universe_overlap':len(topa&topb),'both_q005':int(((x.q_value<.05)&(y.q_value<.05)).sum()),'all_only_q005':int(((x.q_value<.05)&(y.q_value>=.05)).sum()),'early_only_q005':int(((x.q_value>=.05)&(y.q_value<.05)).sum())}
 pd.DataFrame([{'gene':g,'family':'all_stage_only' if g in aa else 'stage_I_II_only'} for g in sorted(aa^bb)]).to_csv(f'followup_tables/{l}_changed_testing_family.csv',index=False)
sf=pd.DataFrame(short);sf.to_csv('followup_tables/shortlist.csv',index=False)
res={'input_fingerprint':ctx['input_fingerprint'],'cohorts':summary,'comparisons':comparisons,'cross_modal_concordance':concordance,'shortlist':json.loads(sf.to_json(orient='records',double_precision=15)),'diagnostics':diagnostics,'interpretation':'Exploratory overlapping-cohort sensitivity, not independent replication or an interaction test. Nominal paired t intervals are not selection-adjusted.','software':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__}}
# pandas JSON rounds tiny p values; retain native values with null missingness.
res['shortlist']=[{k:None if pd.isna(v) else v for k,v in row.items()} for row in short];save('followup_results.json',res)
step('Four cohort/layer paired t families recalculated with BH and explicit excluded/zero-variance states; followup_results.json sha256='+sha('followup_results.json'))
step('Independent review remains pending. Same-session checks cannot resolve MNAR, batch/purity, selection bias or scientific readiness.',blocked=True)
save('followup_validation.json',{'checks':checks+['All four BH families checked against scipy; all testable shortlist paired t CIs/p values independently checked','Original cohort reconstructed exactly; early subset selected only using pathological Stage I/II','No original analysis code executed; no original scientific outputs written'],'independent_review':'pending; blocked','figure_inspection':'pending'})
import matplotlib
matplotlib.use('Agg')
import subprocess
orig=subprocess.check_output
def bound(args,*a,**kw):
 if isinstance(args,(list,tuple)) and args and args[0] in ('fc-list','system_profiler'):raise FileNotFoundError()
 return orig(args,*a,**kw)
subprocess.check_output=bound
import matplotlib.pyplot as plt
subprocess.check_output=orig
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
genes=cfg['prespecified']+cfg['selected_exploratory'];fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,l in zip(axs,['protein','rna']):
 for i,(name,label,color) in enumerate([('all_stage','All stages (72)','#0072B2'),('stage_I_II','Stage I/II (37)','#D55E00')]):
  r=results[name,l].loc[genes];x=r.mean_difference.where(r.status=='tested');ax.errorbar(x,np.arange(6)+(i-.5)*.2,xerr=[x-r.ci_low,r.ci_high-x],fmt='o',capsize=3,label=label,color=color)
 ax.set_yticks(range(6),genes);ax.invert_yaxis();ax.axvline(0,color='gray',ls=':');ax.set_title(l+' • paired mean and nominal 95% CI');ax.set_xlabel(cfg['scales'][l]+'\ntumor − normal');ax.legend(loc='lower right',fontsize=9)
 if l=='protein':ax.text(.98,2,f"VEGFA: n={int(results['all_stage',l].loc['VEGFA','n'])} / {int(results['stage_I_II',l].loc['VEGFA','n'])}; not tested",transform=ax.get_yaxis_transform(),ha='right',fontsize=9)
fig.suptitle('Original shortlist under stage restriction • overlapping cohorts');fig.tight_layout();fig.savefig('followup_figures/shortlist_comparison.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,5))
for ax,l in zip(axs,['protein','rna']):
 a=results['all_stage',l].query('status=="tested"');b=results['stage_I_II',l].query('status=="tested"');g=a.index.intersection(b.index);x=a.loc[g,'mean_difference'];y=b.loc[g,'mean_difference'];ax.hexbin(x,y,gridsize=55,bins='log',mincnt=1,cmap='Blues');lo=min(x.min(),y.min());hi=max(x.max(),y.max());ax.plot([lo,hi],[lo,hi],color='gray',ls='--');ax.set(xlabel='All-stage paired mean difference',ylabel='Stage I/II paired mean difference',title=f'{l}: {len(g):,} shared tested genes\nSigned rank ρ={comparisons[l]["signed_effect_spearman"]:.3f}')
 for gene in genes:
  if gene in g:ax.scatter(x[gene],y[gene],s=15,color='#D55E00');ax.annotate(gene,(x[gene],y[gene]),xytext=(3,4),textcoords='offset points',fontsize=8)
fig.suptitle('Descriptive agreement; overlap induces correlation');fig.tight_layout();fig.savefig('followup_figures/effect_comparison.png');plt.close(fig)
print(json.dumps({'cohorts':summary,'comparisons':comparisons,'concordance':concordance},indent=2))
