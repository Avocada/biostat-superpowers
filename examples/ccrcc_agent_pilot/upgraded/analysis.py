#!/usr/bin/env python3
"""Local paired CPTAC analysis; run with supplied Python, no network required."""
import os,sys,json,hashlib,platform,warnings
from pathlib import Path
from dataclasses import asdict
os.environ['MPLCONFIGDIR']=str(Path('.mplcache').resolve())
sys.path.insert(0,'/Users/amiee/Projects_code/biostat-superpowers')
import numpy as np,pandas as pd,scipy
from scipy import stats
from biostat_workflow.memory import MemoryStore
from biostat_workflow.controller import Goal,Stage,WorkflowState,Result,Outcome,route,advance,settle
import matplotlib
matplotlib.use('Agg')
# Bound font discovery to avoid stalled host fc-list/system_profiler; bundled fonts remain available.
import subprocess
_original_check_output = subprocess.check_output
def _bounded_font_query(args, *a, **kw):
    if isinstance(args, (list, tuple)) and args and args[0] in ('fc-list', 'system_profiler'):
        raise FileNotFoundError('External font discovery disabled for reproducible local figures')
    return _original_check_output(args, *a, **kw)
subprocess.check_output = _bounded_font_query
import matplotlib.pyplot as plt
subprocess.check_output = _original_check_output
P=Path('.'); (P/'tables').mkdir(exist_ok=True);(P/'figures').mkdir(exist_ok=True)
def save(p,o): Path(p).write_text(json.dumps(o,indent=2,default=str,allow_nan=False))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
man=json.loads(Path('input/manifest.json').read_text()); fp=man['input_fingerprint']
for f,v in man['files'].items(): assert sha('input/'+f)==v['sha256'] and Path('input/'+f).stat().st_size==v['bytes'],f
exclude=['C3L-00359','C3N-00313','C3N-00435','C3N-00492','C3N-00832','C3N-01175','C3N-01180']
config={'estimand':'mean within-case tumor-minus-normal difference for each gene/layer','exclude_histology':exclude,'exclude_normal':'C3N-00314','cohort':'intersection of case IDs in all four assays after tissue-specific exclusions','scales':{'protein':'processed TMT log2 reference ratios','rna':'supplied log2 FPKM'},'min_pairs':20,'imputation':False,'extra_log':False,'alpha':0.05,'ci':0.95,'prespecified':['CA9','NNMT','VEGFA','MTOR'],'selection':'Among non-prespecified protein genes with n >= 90% of common cohort and q < 0.05, select two largest absolute protein mean differences; ties alphabetical. RNA does not determine selection.','seed':20260924}
# Memory is established and retrieved BEFORE fitting; retrieved decisions drive configuration.
decisions={'cohort':{k:config[k] for k in ['exclude_histology','exclude_normal','cohort']},'scales':{k:config[k] for k in ['scales','extra_log']},'missingness':{k:config[k] for k in ['min_pairs','imputation']},'model':{k:config[k] for k in ['estimand','alpha','ci']},'shortlist':{k:config[k] for k in ['prespecified','selection']},'source interpretation':{'source_policy':'Native MCP snapshots are annotations and bounded all-indication target records, not enrichment or kidney efficacy. Original Clark cohort is not independent replication. Independent review pending.'}}
with MemoryStore(Path('project-memory.sqlite3'),'ccrcc-pilot') as m:
 if not m.inspect():
  for k,v in decisions.items():m.record(run_id='initial',key=k,value=json.dumps(v),source='input/manifest.json sha256='+sha('input/manifest.json')+'; input/SOURCE.md sha256='+sha('input/SOURCE.md')+'; user analysis contract; analysis.py',confirmed_by='Codex analyst review, not human approval',goal=Goal.INFERENTIAL,stages=(Stage.ANALYSIS,Stage.EVALUATION),input_fingerprint=fp)
 r=m.retrieve(goal=Goal.INFERENTIAL,stage=Stage.ANALYSIS,input_fingerprint=fp,required_keys=tuple(decisions),max_units=8000,count=lambda text:len(text.encode("utf-8")))
 assert r.usable,r.issues
 for item in r.items:
  if item.key!='source interpretation':config.update(json.loads(item.value))
 save('memory_retrieval.json',{'usable':r.usable,'issues':r.issues,'bytes':r.units,'selected_keys':[i.key for i in r.items],'records':json.loads(r.text)})
save('analysis_config.json',config);save('runtime_context.json',{'project_id':'ccrcc-pilot','run_id':'initial','input_fingerprint':fp,'memory':'project-memory.sqlite3','controller':'controller_audit.json','review':'independent evaluation pending'})
state=WorkflowState(goal=Goal.INFERENTIAL); transitions=[]
def step(evidence,missing=None,blocked=False):
 global state
 state=settle(state); before=state; rr=route(state); res=Result(outcome=Outcome.BLOCKED if blocked else Outcome.COMPLETE,evidence=evidence,missing_data_required=missing);state=advance(state,res); transitions.append({'before':asdict(before),'route':asdict(rr),'result':asdict(res),'after':asdict(state)});save('controller_audit.json',transitions)
step('User-defined paired, cross-sectional associational estimand; analysis_config.json sha256='+sha('analysis_config.json'))
cli=pd.read_csv('input/clinical_annotation.csv').set_index('Case_ID');assert cli.index.is_unique
assert set(cli.index[cli.Histologic_Type!='Clear cell renal cell carcinoma'])==set(config['exclude_histology'])
meta=pd.read_csv('input/cptac_metadata.csv.gz');bad=meta[meta['Specimen.Label']=='CPT0012090003'];assert len(bad)==1 and bad['Case.ID'].iloc[0]==config['exclude_normal'] and bad['Type'].iloc[0]=='Normal'
data={}
for layer,stem in [('protein','proteome'),('rna','RNAseq_fpkm_log2')]:
 for tissue in ['Tumor','Normal']:
  d=pd.read_csv(f'input/HS_CPTAC_CCRCC_{stem}_{tissue}.cct',sep='\t',index_col=0);assert d.index.is_unique and d.columns.is_unique;assert set(d.columns)<=set(cli.index);data[(layer,tissue)]=d
sets={k:set(d.columns)-set(exclude)-({config['exclude_normal']} if k[1]=='Normal' else set()) for k,d in data.items()};common=sorted(set.intersection(*sets.values())); N=len(common)
availability=[{'layer':k[0],'tissue':k[1],'downloaded':len(data[k].columns),'eligible':len(v),'common':N} for k,v in sets.items()]
cohort={'downloaded_tumors':110,'histology_excluded':7,'ccRCC_tumors':103,'contaminated_normals_excluded':1,'common_cases':N,'assay_availability':availability,'layer_pairs':{l:len(sets[(l,'Tumor')]&sets[(l,'Normal')]) for l in ['protein','rna']}}
save('cohort.json',cohort);save('cohort_case_ids.json',common)
profile={}
for k,d in data.items():
 a=d[common].to_numpy(float);profile['_'.join(k)]={'genes':len(d),'cases':N,'nonfinite':int((~np.isfinite(a)).sum()),'nonfinite_fraction':float((~np.isfinite(a)).mean()),'infinite':int(np.isinf(a).sum()),'finite_range':[float(np.nanmin(np.where(np.isfinite(a),a,np.nan))),float(np.nanmax(np.where(np.isfinite(a),a,np.nan)))]}
save('data_profile.json',profile);step('Verified all input hashes, authoritative 7 exclusions, contaminated normal map, unique gene/case keys; cohort.json and data_profile.json',True)
step('No imputation as requested; finite pairs per gene, minimum 20. Missingness may be abundance-dependent/MNAR; complete observed-pair inference cannot establish full-cohort unbiasedness. data_profile.json')
results={};diffs={}
def fit(t,n):
 a=t.to_numpy(float);b=n.to_numpy(float);mask=np.isfinite(a)&np.isfinite(b);d=np.where(mask,a-b,np.nan);count=mask.sum(1)
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');mean=np.nanmean(d,axis=1);sd=np.nanstd(d,axis=1,ddof=1);median=np.nanmedian(d,axis=1)
 valid=(count>=config['min_pairs'])&np.isfinite(sd)&(sd>0)&np.isfinite(mean);se=sd/np.sqrt(np.maximum(count,1));pv=np.full(len(d),np.nan);lo=pv.copy();hi=pv.copy();q=pv.copy();pv[valid]=2*stats.t.sf(np.abs(mean[valid]/se[valid]),count[valid]-1);crit=stats.t.ppf(.975,count[valid]-1);lo[valid]=mean[valid]-crit*se[valid];hi[valid]=mean[valid]+crit*se[valid]
 ids=np.flatnonzero(valid);order=ids[np.argsort(pv[ids])];q[order]=np.minimum(1,np.minimum.accumulate((pv[order]*len(order)/np.arange(1,len(order)+1))[::-1])[::-1])
 status=np.where(count<config['min_pairs'],'insufficient_pairs',np.where(sd==0,'zero_variance',np.where(valid,'tested','nonfinite_failure')))
 out=pd.DataFrame({'gene':t.index,'n':count,'mean_difference':mean,'ci_low':lo,'ci_high':hi,'p_value':pv,'q_value':q,'sd_difference':sd,'median_difference':median,'missing_pairs':N-count,'status':status}).set_index('gene')
 return out,d
for layer in ['protein','rna']:
 t=data[(layer,'Tumor')][common];n=data[(layer,'Normal')].reindex(t.index)[common];r,d=fit(t,n);results[layer]=r;diffs[layer]=d;r.to_csv(f'tables/{layer}_all_genes.csv')
p=results['protein'];candidates=p[(p.n>=np.ceil(.9*N))&(p.q_value<.05)&(~p.index.isin(config['prespecified']))].assign(abs_effect=lambda x:x.mean_difference.abs()).sort_values(['abs_effect','gene'],ascending=[False,True]).head(2).index.tolist();short=config['prespecified']+candidates
joint=results['protein'].join(results['rna'],lsuffix='_protein',rsuffix='_rna',how='inner');both=joint[(joint.status_protein=='tested')&(joint.status_rna=='tested')].copy();both['same_direction']=np.sign(both.mean_difference_protein)==np.sign(both.mean_difference_rna);both.to_csv('tables/rna_protein_comparison.csv')
# Exact same finite cases within each gene, as a descriptive cross-layer sensitivity.
sens=[]
for g in both.index:
 tp=data[('protein','Tumor')].loc[g,common].to_numpy(float);np_=data[('protein','Normal')].loc[g,common].to_numpy(float);tr=data[('rna','Tumor')].loc[g,common].to_numpy(float);nr=data[('rna','Normal')].loc[g,common].to_numpy(float);ok=np.isfinite(tp)&np.isfinite(np_)&np.isfinite(tr)&np.isfinite(nr)
 if ok.sum()>=20:sens.append({'gene':g,'n_four_finite':int(ok.sum()),'protein_mean':float(np.mean(tp[ok]-np_[ok])),'rna_mean':float(np.mean(tr[ok]-nr[ok]))})
sens=pd.DataFrame(sens);sens['same_direction']=np.sign(sens.protein_mean)==np.sign(sens.rna_mean);sens.to_csv('tables/common_finite_sensitivity.csv',index=False)
shortrows=[];diagnostics=[]
for layer,r in results.items():
 for g in short:
  if g not in r.index:shortrows.append({'gene':g,'layer':layer,'status':'unavailable'});continue
  shortrows.append({'gene':g,'layer':layer,**{k:(None if pd.isna(v) else (v.item() if isinstance(v,np.generic) else v)) for k,v in r.loc[g].to_dict().items()}});v=diffs[layer][r.index.get_loc(g)];v=v[np.isfinite(v)]
  if len(v)>1:
   loo=(v.sum()-v)/(len(v)-1); diagnostics.append({'gene':g,'layer':layer,'n':len(v),'median':float(np.median(v)),'skew':float(stats.skew(v)),'loo_mean_min':float(loo.min()),'loo_mean_max':float(loo.max()),'max_abs_standardized_difference':float(np.max(np.abs((v-v.mean())/v.std(ddof=1))))})
pd.DataFrame(shortrows).to_csv('tables/shortlist.csv',index=False);save('diagnostics.json',diagnostics)
summary={'cohort':cohort,'assays':{l:{'rows':len(r),'tested':int((r.status=='tested').sum()),'q_below_005':int((r.q_value<.05).sum()),'up':int(((r.q_value<.05)&(r.mean_difference>0)).sum()),'down':int(((r.q_value<.05)&(r.mean_difference<0)).sum()),'status_counts':r.status.value_counts().to_dict()} for l,r in results.items()},'concordance':{'both_tested':len(both),'same_direction':int(both.same_direction.sum()),'fraction':float(both.same_direction.mean()),'spearman_descriptive':float(stats.spearmanr(both.mean_difference_protein,both.mean_difference_rna).statistic),'same_finite_case_genes':len(sens),'same_finite_direction_fraction':float(sens.same_direction.mean())},'shortlist':shortrows,'data_driven_candidates':candidates,'limitations':['Observed pairs can be selected by abundance-dependent missingness.','Processed reference-ratio protein and log2 FPKM RNA scales are not interchangeable.','Paired t inference assumes independent cases and sufficiently regular mean differences; gene correlation affects BH guarantees.','Processing, TMT compression, batch, purity and adjacent-tissue composition remain unresolved.','Data-driven selection has winner bias; nominal CIs are not selection adjusted.','Independent evaluation pending; this is an exploratory draft.']}
save('results.json',summary);step('Executed paired t estimates, separate BH families, explicit failure states, same-finite-case cross-layer sensitivity and shortlist influence diagnostics; results.json sha256='+sha('results.json'))
step('Independent artifact evaluation intentionally deferred per user; same-session checks are not independent approval.',blocked=True)
save('software_versions.json',{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__})
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
fig,axs=plt.subplots(1,2,figsize=(12,4.5));x=np.arange(4);axs[0].bar(x-.18,[a['downloaded'] for a in availability],.36,label='Downloaded',color='#8b98aa');axs[0].bar(x+.18,[a['eligible'] for a in availability],.36,label='Eligible',color='#0072B2');axs[0].axhline(N,color='#D55E00',ls='--',label=f'Common cohort: {N}');axs[0].set_xticks(x,[a['layer']+'\n'+a['tissue'] for a in availability]);axs[0].set_ylabel('Cases');axs[0].legend(fontsize=8);axs[0].set_title('Availability after histology / tissue exclusions')
for l,col in [('protein','#0072B2'),('rna','#D55E00')]:axs[1].hist(results[l].n,bins=np.arange(-.5,N+1.5),histtype='step',linewidth=2,label=l,color=col)
axs[1].axvline(20,color='black',ls=':');axs[1].set_xlabel('Finite pairs per gene');axs[1].set_ylabel('Genes');axs[1].legend();axs[1].set_title('Gene-wise availability in common cohort');fig.tight_layout();fig.savefig('figures/availability_missingness.png');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5));ok=p.status=='tested';ax.scatter(p.loc[ok,'mean_difference'],-np.log10(p.loc[ok,'q_value'].clip(lower=1e-300)),s=4,alpha=.35,color='#65788a');
for g in short:
 if g in p.index and p.loc[g,'status']=='tested':v=p.loc[g];ax.scatter(v.mean_difference,-np.log10(max(v.q_value,1e-300)),color='#D55E00');ax.annotate(g,(v.mean_difference,-np.log10(max(v.q_value,1e-300))),xytext=(5,5),textcoords='offset points')
ax.axhline(-np.log10(.05),ls='--',color='#0072B2');ax.set(xlabel='Mean paired tumor − normal: protein TMT log2 reference-ratio scale',ylabel='−log10(BH q)',title=f'Paired differential proteins • {N} common cases');fig.tight_layout();fig.savefig('figures/protein_differential.png');plt.close(fig)
fig,ax=plt.subplots(figsize=(7,5));ax.hexbin(both.mean_difference_rna,both.mean_difference_protein,gridsize=50,mincnt=1,cmap='Blues',bins='log');ax.axhline(0,c='gray',lw=.7);ax.axvline(0,c='gray',lw=.7)
for g in short:
 if g in both.index: v=both.loc[g];ax.scatter(v.mean_difference_rna,v.mean_difference_protein,c='#D55E00',s=20);ax.annotate(g,(v.mean_difference_rna,v.mean_difference_protein),xytext=(4,4),textcoords='offset points')
ax.set(xlabel='RNA mean difference (supplied log2 FPKM)',ylabel='Protein mean difference (TMT log2 reference ratio)',title='Direction concordance • distinct assay scales');fig.tight_layout();fig.savefig('figures/concordance.png');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4.5))
for ax,l in zip(axs,['protein','rna']):
 r=results[l].reindex(short);x=r.mean_difference.where(r.status=='tested').to_numpy();ax.errorbar(x,np.arange(len(short)),xerr=np.array([x-r.ci_low,r.ci_high-x]),fmt='o',color='#0072B2',capsize=3);ax.set_yticks(np.arange(len(short)),short);ax.axvline(0,c='gray',ls='--');ax.set_title(l+' • nominal paired t 95% CI');
 if l=='protein':ax.text(0.98,2,'VEGFA: n=1, not tested',transform=ax.get_yaxis_transform(),ha='right',va='center',fontsize=9,color='#8b4c00')
 ax.set_xlabel(config['scales'][l]+' difference')
fig.tight_layout();fig.savefig('figures/shortlist_intervals.png');plt.close(fig)
print(json.dumps({'common_cases':N,'summary':summary['assays'],'candidates':candidates,'concordance':summary['concordance']},indent=2))
