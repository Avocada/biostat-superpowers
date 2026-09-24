#!/usr/bin/env python3
"""Rebuild aggregate paired analyses locally; no participant values exported."""
import os,json,hashlib,sys,platform,warnings
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'.mplcache')
import numpy as np,pandas as pd,scipy
from scipy import stats
import matplotlib
matplotlib.use('Agg')
# Avoid slow OS font discovery; bundled Matplotlib fonts suffice for this report.
import subprocess
_original_check_output=subprocess.check_output
def _font_safe_output(cmd,*a,**kw):
 if isinstance(cmd,(list,tuple)) and any(str(x) in ('fc-list','system_profiler') for x in cmd): return b''
 return _original_check_output(cmd,*a,**kw)
subprocess.check_output=_font_safe_output
import matplotlib.pyplot as plt
subprocess.check_output=_original_check_output
P=Path(__file__).resolve().parent; I=P/'input'; O=P/'outputs'; O.mkdir(exist_ok=True)
def dump(obj,path):
 Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False,default=lambda x: x.item() if hasattr(x,'item') else str(x)))
def bh(p):
 p=np.asarray(p); order=np.argsort(p); q=np.empty(len(p)); q[order]=np.minimum(1,np.minimum.accumulate((p[order]*len(p)/np.arange(1,len(p)+1))[::-1])[::-1]);return q
manifest=json.loads((I/'manifest.json').read_text()); checks=[]
for f,v in manifest['files'].items():
 b=(I/f).read_bytes(); actual=hashlib.sha256(b).hexdigest(); assert actual==v['sha256'] and len(b)==v['bytes'];checks.append(dict(file=f,sha256=actual,bytes=len(b),verified=True))
fp=hashlib.sha256(json.dumps(manifest['files'],sort_keys=True).encode()).hexdigest();assert fp==manifest['input_fingerprint'];dump(dict(files=checks,input_fingerprint=fp),O/'fingerprint_verification.json')
cli=pd.read_csv(I/'clinical_annotation.csv');assert not cli.Case_ID.duplicated().any()
excluded=set(cli.loc[cli.Histologic_Type!='Clear cell renal cell carcinoma','Case_ID']); assert excluded==set('C3L-00359 C3N-00313 C3N-00435 C3N-00492 C3N-00832 C3N-01175 C3N-01180'.split())
meta=pd.read_csv(I/'cptac_metadata.csv.gz'); match=meta.loc[meta['Specimen.Label'].eq('CPT0012090003')]; assert len(match)==1 and match['Case.ID'].iloc[0]=='C3N-00314'
eligible=set(cli.loc[cli.Histologic_Type.eq('Clear cell renal cell carcinoma'),'Case_ID']); D={}; avail=[]
for layer,tag in [('protein','proteome'),('rna','RNAseq_fpkm_log2')]:
 for tissue in ['Tumor','Normal']:
  d=pd.read_csv(I/f'HS_CPTAC_CCRCC_{tag}_{tissue}.cct',sep='\t',index_col=0); assert d.index.is_unique and d.columns.is_unique
  assert set(d.columns)<=set(cli.Case_ID)
  keep=set(d.columns)&eligible
  if tissue=='Normal':keep-={'C3N-00314'}
  D[layer,tissue]=d.loc[:,sorted(keep)].apply(pd.to_numeric,errors='raise')
  avail.append(dict(layer=layer,tissue=tissue,downloaded=d.shape[1],after_histology=len(set(d.columns)&eligible),after_contamination=len(keep)))
common=sorted(set.intersection(*(set(d.columns) for d in D.values())));N=len(common); assert 'C3N-00314' not in common
config=dict(goal='Exploratory paired tissue associations; not causal or efficacy',estimand='Mean within-case tumor-minus-normal difference on supplied layer log2 scale',scales={'protein':'processed TMT log2 reference ratio','rna':'supplied log2 FPKM'},min_finite_pairs=20,primary_cohort='Authoritative ccRCC histology; uncontaminated NAT; all four assays',cohort_n=N,excluded_non_ccrcc=sorted(excluded),excluded_normal='C3N-00314 (CPT0012090003); tumor retained in availability counts',missingness='Available finite pairs per gene, no imputation',inference='Two-sided one-sample t test of paired differences; pointwise t 95% CI; BH separately over finite valid p-values per layer',zero_variance='Flag; mean retained; CI/p/q undefined, excluded from tested family',selection_rule='Up to two non-prespecified genes with protein q<0.05, >=90% finite pairs, RNA test available; rank descending absolute protein mean difference, tie by gene. No RNA direction or drug filter.',seed=20260924,input_fingerprint=fp,sensitivity='Layer-specific eligible paired cohorts; shortlist leave-one-pair-out means and bootstrap mean CIs; same-case cross-layer direction summaries',versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__))
dump(config,P/'analysis_config.json')
def analyze(t,n,cases):
 genes=t.index.union(n.index);t=t.reindex(genes).loc[:,cases].to_numpy(float); n=n.reindex(genes).loc[:,cases].to_numpy(float)
 finite=np.isfinite(t)&np.isfinite(n); diff=np.where(finite,t-n,np.nan); count=finite.sum(axis=1)
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');mean=np.nanmean(diff,axis=1);sd=np.nanstd(diff,axis=1,ddof=1)
 out=pd.DataFrame(dict(gene=genes,n=count,mean_difference=mean,sd_difference=sd,tumor_nonfinite=(~np.isfinite(t)).sum(axis=1),normal_nonfinite=(~np.isfinite(n)).sum(axis=1)))
 out['status']=np.where(count<20,'insufficient_pairs',np.where(sd==0,'zero_variance',np.where(np.isfinite(mean)&np.isfinite(sd),'tested','nonfinite_failure')))
 for c in ['ci95_low','ci95_high','t','p','q']:out[c]=np.nan
 ix=out.status.eq('tested'); se=sd[ix]/np.sqrt(count[ix]); tt=mean[ix]/se; pv=2*stats.t.sf(abs(tt),count[ix]-1); crit=stats.t.ppf(.975,count[ix]-1)
 out.loc[ix,'ci95_low']=mean[ix]-crit*se;out.loc[ix,'ci95_high']=mean[ix]+crit*se;out.loc[ix,'t']=tt;out.loc[ix,'p']=pv
 fail=ix&~np.isfinite(out.p);out.loc[fail,'status']='nonfinite_failure';ix=out.status.eq('tested');out.loc[ix,'q']=bh(out.loc[ix,'p'])
 return out,diff
R={};diffs={};summary={};sens={}
for l in ['protein','rna']:
 r,df=analyze(D[l,'Tumor'],D[l,'Normal'],common);R[l]=r.set_index('gene');diffs[l]=df;r.to_csv(O/f'{l}_all_genes.csv',index=False)
 cases=sorted(set(D[l,'Tumor'].columns)&set(D[l,'Normal'].columns));sr,_=analyze(D[l,'Tumor'],D[l,'Normal'],cases);sr.to_csv(O/f'{l}_layer_cohort_sensitivity.csv',index=False);sens[l]=sr.set_index('gene')
 summary[l]=dict(genes=len(r),status_counts=r.status.value_counts().to_dict(),q_lt_005=int((r.q<.05).sum()),up_q_lt_005=int(((r.q<.05)&(r.mean_difference>0)).sum()),down_q_lt_005=int(((r.q<.05)&(r.mean_difference<0)).sum()),paired_n_quantiles=r.n.quantile([0,.25,.5,.75,1]).to_dict(),tumor_nonfinite_fraction=float(r.tumor_nonfinite.sum()/(N*len(r))),normal_nonfinite_fraction=float(r.normal_nonfinite.sum()/(N*len(r))),layer_specific_cohort_n=len(cases))
pre=['CA9','NNMT','VEGFA','MTOR'];cand=R['protein'].loc[lambda x:(x.q<.05)&(x.n>=np.ceil(.9*N))].copy();cand=cand.loc[cand.index.isin(R['rna'].query("status == 'tested'").index)&~cand.index.isin(pre)];cand['absdiff']=abs(cand.mean_difference);extra=cand.reset_index().sort_values(['absdiff','gene'],ascending=[False,True]).gene.head(2).tolist();short=pre+extra
shortrows=[];rng=np.random.default_rng(config['seed'])
for g in short:
 for l in R:
  if g not in R[l].index:shortrows.append(dict(gene=g,layer=l,status='unavailable'));continue
  row=R[l].loc[g].to_dict(); row.update(gene=g,layer=l,selection='prespecified' if g in pre else 'exploratory')
  v=diffs[l][R[l].index.get_loc(g)];v=v[np.isfinite(v)]
  if len(v)>1:
   loo=(v.sum()-v)/(len(v)-1); row.update(loo_mean_min=loo.min(),loo_mean_max=loo.max(),median_difference=np.median(v),skewness=stats.skew(v),bootstrap_ci_low=np.quantile(np.mean(rng.choice(v,(3000,len(v))),axis=1),.025),bootstrap_ci_high=np.quantile(np.mean(rng.choice(v,(3000,len(v))),axis=1),.975))
  row['layer_cohort_mean']=sens[l].loc[g,'mean_difference'];row['layer_cohort_n']=sens[l].loc[g,'n'];shortrows.append(row)
sdf=pd.DataFrame(shortrows);sdf.to_csv(O/'shortlist.csv',index=False)
a=R['protein'].add_prefix('protein_').join(R['rna'].add_prefix('rna_'),how='inner');a['same_direction']=np.sign(a.protein_mean_difference)==np.sign(a.rna_mean_difference)
# Re-estimate both directions on identical finite cases per gene as a diagnostic.
matched=[]
for g,row in a.iterrows():
 p=diffs['protein'][R['protein'].index.get_loc(g)];r=diffs['rna'][R['rna'].index.get_loc(g)];ok=np.isfinite(p)&np.isfinite(r);nn=int(ok.sum());matched.append((nn,np.mean(p[ok]) if nn else np.nan,np.mean(r[ok]) if nn else np.nan))
a[['joint_pair_n','joint_protein_mean','joint_rna_mean']]=matched;a.to_csv(O/'rna_protein_concordance.csv')
b=a.loc[(a.protein_status=='tested')&(a.rna_status=='tested')];joint=a.query('joint_pair_n>=20');con=dict(both_tested=len(b),same_direction=int(b.same_direction.sum()),fraction_same_direction=float(b.same_direction.mean()),spearman_mean_differences=float(stats.spearmanr(b.protein_mean_difference,b.rna_mean_difference).statistic),joint_finite_genes=len(joint),joint_fraction_same_direction=float((np.sign(joint.joint_protein_mean)==np.sign(joint.joint_rna_mean)).mean()),warning='Descriptive gene-level association; correlated genes are not independent replicates. No test of raw cross-layer effect differences.')
results=dict(cohort_n=N,availability=avail,summary=summary,concordance=con,shortlist=short,shortlist_results=json.loads(sdf.to_json(orient='records')),input_fingerprint=fp)
dump(results,P/'results.json')
# Aggregate plots only.
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#ffffff'})
fig,ax=plt.subplots(figsize=(9,4.6));labels=[x['layer']+' '+x['tissue'] for x in avail];x=np.arange(4);ax.bar(x-.22,[v['downloaded'] for v in avail],.22,label='Downloaded',color='#8d99ae');ax.bar(x,[v['after_histology'] for v in avail],.22,label='ccRCC',color='#0072B2');ax.bar(x+.22,[v['after_contamination'] for v in avail],.22,label='Clean tissue',color='#009E73');ax.axhline(N,color='#b04a00',ls='--',label=f'Primary common cases: {N}');ax.set(xticks=x,xticklabels=labels,ylabel='Cases',title='Availability and eligibility by assay');ax.legend(fontsize=8,ncol=2);fig.tight_layout();fig.savefig(O/'availability.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.6));
for l,col in [('protein','#0072B2'),('rna','#D55E00')]:ax.hist(R[l].n,bins=np.arange(-.5,N+2.5,2),histtype='step',lw=2,label=l,color=col)
ax.set_yscale('symlog',linthresh=1);ax.axvline(20,color='black',ls='--',label='Minimum 20');ax.set(xlabel=f'Finite paired observations per gene (maximum {N})',ylabel='Number of genes (log scale above 1)',title='Gene-level pair availability');ax.legend();fig.tight_layout();fig.savefig(O/'missingness.png',dpi=150);plt.close(fig)
p=R['protein'].query("status=='tested'");fig,ax=plt.subplots(figsize=(8,5));ax.scatter(p.mean_difference,-np.log10(p.q.clip(lower=1e-300)),s=6,c=np.where(p.q<.05,'#0072B2','#8d99ae'),alpha=.4)
for g in short:
 if g in p.index:ax.annotate(g,(p.loc[g,'mean_difference'],-np.log10(max(p.loc[g,'q'],1e-300))),fontsize=9)
ax.set(xlabel='Mean paired difference: protein TMT log2 reference ratio',ylabel='−log10(BH q)',title='Paired protein differential abundance');fig.tight_layout();fig.savefig(O/'protein_differential.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(7,5.4));ax.scatter(b.rna_mean_difference,b.protein_mean_difference,s=5,alpha=.22,color='#0072B2');ax.axhline(0,color='gray',lw=.7);ax.axvline(0,color='gray',lw=.7)
for g in short:
 if g in b.index:ax.annotate(g,(b.loc[g,'rna_mean_difference'],b.loc[g,'protein_mean_difference']),fontsize=9)
ax.set(xlabel='RNA: mean paired difference, supplied log2 FPKM',ylabel='Protein: mean paired difference, TMT log2 ratio',title=f'Direction agreement: {con["fraction_same_direction"]:.1%} of {len(b):,} genes');fig.tight_layout();fig.savefig(O/'concordance.png',dpi=150);plt.close(fig)
print(json.dumps({k:results[k] for k in ['cohort_n','availability','summary','concordance','shortlist']},indent=2))
