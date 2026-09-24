#!/usr/bin/env python3
"""Stage sensitivity only. Run with shared environment; does not execute initial analysis."""
import os, ast, json, hashlib, warnings, math, platform
from pathlib import Path
P=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(P/'.mplcache')
import numpy as np, pandas as pd, scipy
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=P/'followup_outputs'; O.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(x,p): p.write_text(json.dumps(x,indent=2,allow_nan=False,default=str))
# Record all original files before reuse; follow-up names and caches are excluded.
preserve=O/'original_hashes.json'
if not preserve.exists():
 files=[p for p in P.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.git','.mplcache','__pycache__','followup_outputs','followup_sources']) and not p.name.startswith(('followup','FOLLOWUP','context_sources'))]
 dump({str(p.relative_to(P)):sha(p) for p in files},preserve)
original=json.loads(preserve.read_text())
assert all(sha(P/f)==v for f,v in original.items())
m=json.loads((P/'input/manifest.json').read_text());checks=[]
for f,v in m['files'].items():
 p=P/'input'/f; assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes'];checks.append(f)
fp=hashlib.sha256(json.dumps(m['files'],sort_keys=True).encode()).hexdigest()
cfg=json.loads((P/'analysis_config.json').read_text());old=json.loads((P/'results.json').read_text())
assert fp==m['input_fingerprint']==cfg['input_fingerprint']==old['input_fingerprint']
dump(dict(input_fingerprint=fp,verified_files=checks),O/'fingerprint_verification.json')
# Reuse exact original numerical functions through AST, with no top-level execution.
tree=ast.parse((P/'analysis.py').read_text()); nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['bh','analyze']]
assert len(nodes)==2
exec(compile(ast.Module(body=nodes,type_ignores=[]),'analysis.py:functions','exec'))
cli=pd.read_csv(P/'input/clinical_annotation.csv').set_index('Case_ID'); assert cli.index.is_unique
eligible=set(cli.index[cli.Histologic_Type.eq('Clear cell renal cell carcinoma')]);D={}
for layer,tag in [('protein','proteome'),('rna','RNAseq_fpkm_log2')]:
 for tissue in ['Tumor','Normal']:
  d=pd.read_csv(P/'input'/f'HS_CPTAC_CCRCC_{tag}_{tissue}.cct',sep='\t',index_col=0)
  assert d.index.is_unique and d.columns.is_unique
  keep=set(d.columns)&eligible
  if tissue=='Normal':keep.discard('C3N-00314')
  D[layer,tissue]=d.loc[:,sorted(keep)].apply(pd.to_numeric,errors='raise')
common=sorted(set.intersection(*(set(d.columns) for d in D.values())));assert len(common)==cfg['cohort_n']==72
stages=cli.loc[common,'Tumor_Stage_Pathological']; early=sorted(stages.index[stages.isin(['Stage I','Stage II'])]); assert set(early)<=set(common)
cohorts={'all_stage':common,'early_stage':early}; pre=['CA9','NNMT','VEGFA','MTOR'];short=old['shortlist']; R={};summary={};rows=[]; selections={};concordance={}
for cohort,cases in cohorts.items():
 cutoff=max(20,math.ceil(.8*len(cases)));summary[cohort]={'cases':len(cases),'minimum_pairs':cutoff,'stages':cli.loc[cases,'Tumor_Stage_Pathological'].fillna('Missing').value_counts().to_dict(),'layers':{}}
 for layer in ['protein','rna']:
  r,diff=analyze(D[layer,'Tumor'],D[layer,'Normal'],cases)
  # Erase all inference outside new family, then recompute BH across valid retained tests.
  fail=r.n<cutoff;r.loc[fail,'status']='below_cohort_completeness';r.loc[fail,['ci95_low','ci95_high','t','p','q']]=np.nan
  r['q']=np.nan;ok=r.status.eq('tested');r.loc[ok,'q']=bh(r.loc[ok,'p'])
  r['finite_fraction']=r.n/len(cases);r['abs_effect_rank']=np.nan
  ix=r.loc[ok].assign(abs_effect=lambda x:abs(x.mean_difference)).sort_values(['abs_effect','gene'],ascending=[False,True]).index
  r.loc[ix,'abs_effect_rank']=np.arange(1,len(ix)+1)
  r.to_csv(O/f'{cohort}_{layer}_genes.csv',index=False);R[cohort,layer]=r.set_index('gene')
  summary[cohort]['layers'][layer]={'total_genes':len(r),'pass_completeness':int((r.n>=cutoff).sum()),'status_counts':r.status.value_counts().to_dict(),'tested':int(ok.sum()),'q_lt_005':int((r.q<.05).sum()),'up_q_lt_005':int(((r.q<.05)&(r.mean_difference>0)).sum()),'down_q_lt_005':int(((r.q<.05)&(r.mean_difference<0)).sum())}
  for g in short:
   row=R[cohort,layer].loc[g].to_dict();row.update(gene=g,cohort=cohort,layer=layer,selection='prespecified' if g in pre else 'selected in initial analysis')
   v=diff[r.index[r.gene.eq(g)][0]];v=v[np.isfinite(v)]
   if len(v)>1:
    row['loo_mean_min']=float(((v.sum()-v)/(len(v)-1)).min());row['loo_mean_max']=float(((v.sum()-v)/(len(v)-1)).max());row['skewness']=float(stats.skew(v))
   rows.append(row)
 p=R[cohort,'protein'];r=R[cohort,'rna'];c=p.loc[(p.q<.05)&(p.n>=math.ceil(.9*len(cases)))&~p.index.isin(pre)].copy();c=c.loc[c.index.isin(r.index[r.status.eq('tested')])];c['abs_effect']=abs(c.mean_difference)
 selections[cohort]=c.reset_index().sort_values(['abs_effect','gene'],ascending=[False,True]).gene.head(2).tolist()
 joined=p.loc[p.status.eq('tested')].join(r.loc[r.status.eq('tested')],lsuffix='_protein',rsuffix='_rna',how='inner')
 concordance[cohort]={'both_tested':len(joined),'same_direction':int((np.sign(joined.mean_difference_protein)==np.sign(joined.mean_difference_rna)).sum()),'fraction_same_direction':float((np.sign(joined.mean_difference_protein)==np.sign(joined.mean_difference_rna)).mean())}
comparisons={}
for layer in ['protein','rna']:
 a=R['all_stage',layer];e=R['early_stage',layer];j=a.loc[a.status.eq('tested')].join(e.loc[e.status.eq('tested')],lsuffix='_all',rsuffix='_early',how='inner');j.to_csv(O/f'{layer}_cohort_comparison.csv')
 top=lambda z:set(z.loc[z.status.eq('tested')].sort_values('abs_effect_rank').head(50).index)
 comparisons[layer]={'common_tested':len(j),'only_all_tested':len(a.loc[a.status.eq('tested')].index.difference(j.index)),'only_early_tested':len(e.loc[e.status.eq('tested')].index.difference(j.index)),'direction_agreement':float((np.sign(j.mean_difference_all)==np.sign(j.mean_difference_early)).mean()),'signed_effect_spearman':float(stats.spearmanr(j.mean_difference_all,j.mean_difference_early).statistic),'absolute_effect_spearman_common_genes':float(stats.spearmanr(abs(j.mean_difference_all),abs(j.mean_difference_early)).statistic),'top50_overlap':len(top(a)&top(e)),'significant_both':int(((j.q_all<.05)&(j.q_early<.05)).sum()),'significant_all_only':int(((j.q_all<.05)&(j.q_early>=.05)).sum()),'significant_early_only':int(((j.q_all>=.05)&(j.q_early<.05)).sum())}
 # Check original all-stage estimates are numerically identical where eligible.
 orig=pd.read_csv(P/'outputs'/f'{layer}_all_genes.csv').set_index('gene');assert np.allclose(a.mean_difference,orig.loc[a.index,'mean_difference'],equal_nan=True)
sdf=pd.DataFrame(rows);sdf.to_csv(O/'shortlist_comparison.csv',index=False)
results={'input_fingerprint':fp,'summary':summary,'cohort_cases':cohorts,'excluded_from_early':stages.loc[~stages.index.isin(early)].fillna('Missing').value_counts().to_dict(),'comparisons':comparisons,'cross_modal_concordance':concordance,'original_shortlist':short,'reselected_exploratory_genes':selections,'shortlist_results':json.loads(sdf.to_json(orient='records')),'methods':{'estimand':cfg['estimand'],'scales':cfg['scales'],'inference':cfg['inference']+' and separately by cohort','completeness':'at least ceil(0.8 * cohort case count) AND at least 20 finite tumor/normal pairs','selection_rule':cfg['selection_rule'],'no_imputation':True,'zero_variance':cfg['zero_variance']},'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}}
dump(results,P/'followup_results.json')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,5))
for ax,layer in zip(axes,['protein','rna']):
 for cohort,offset,color,label in [('all_stage',-.13,'#0072B2','All stages (72)'),('early_stage',.13,'#D55E00',f'Stage I–II ({len(early)})')]:
  t=sdf.query('cohort==@cohort and layer==@layer').set_index('gene').loc[short];ok=t.status.eq('tested');y=np.arange(len(short))+offset
  ax.errorbar(t.loc[ok,'mean_difference'],y[ok],xerr=np.vstack([t.loc[ok,'mean_difference']-t.loc[ok,'ci95_low'],t.loc[ok,'ci95_high']-t.loc[ok,'mean_difference']]),fmt='o',capsize=3,label=label,color=color)
 ax.set_yticks(range(len(short)),[g+(' *' if g not in pre else '') for g in short]);ax.invert_yaxis();ax.axvline(0,color='gray',lw=.7);ax.set_title(layer.upper());ax.set_xlabel('Paired mean Δ: '+('TMT log2 reference ratio' if layer=='protein' else 'supplied log2 FPKM'));ax.legend(fontsize=9)
 if layer=='protein':ax.text(.02,.53,'VEGFA: insufficient pairs in both cohorts',transform=ax.transAxes,fontsize=8)
fig.suptitle('Original shortlist: pointwise paired t 95% intervals\n* Initially selected; intervals are not selection-adjusted',fontsize=12);fig.tight_layout();fig.savefig(O/'shortlist_comparison.png',dpi=160);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,5))
for ax,layer in zip(axes,['protein','rna']):
 a=R['all_stage',layer];e=R['early_stage',layer];ix=a.index[a.status.eq('tested')].intersection(e.index[e.status.eq('tested')]);x=a.loc[ix,'mean_difference'];y=e.loc[ix,'mean_difference'];ax.scatter(x,y,s=5,alpha=.22,color='#0072B2');lo=min(x.min(),y.min());hi=max(x.max(),y.max());ax.plot([lo,hi],[lo,hi],color='gray',ls='--');ax.axhline(0,color='gray',lw=.5);ax.axvline(0,color='gray',lw=.5)
 for g in short:
  if g in ix:ax.annotate(g,(x[g],y[g]),fontsize=8,xytext=(3,4),textcoords='offset points')
 ax.set(xlabel='All-stage paired mean Δ',ylabel='Stage I–II paired mean Δ',title=f'{layer}: {len(ix):,} common tested genes\nDirection agreement {comparisons[layer]["direction_agreement"]:.1%}')
fig.suptitle('Overlapping cohorts: descriptive comparison, not replication');fig.tight_layout();fig.savefig(O/'effect_comparison.png',dpi=160);plt.close(fig)
assert all(sha(P/f)==v for f,v in original.items())
print(json.dumps({'fingerprint':fp,'summary':summary,'comparisons':comparisons,'selections':selections},indent=2))
