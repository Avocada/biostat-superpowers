from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from scipy import stats
c=json.load(open('cohort_case_ids.json'));checks=[]
for l,stem in [('protein','proteome'),('rna','RNAseq_fpkm_log2')]:
 r=pd.read_csv('tables/'+l+'_all_genes.csv').set_index('gene');t=pd.read_csv('input/HS_CPTAC_CCRCC_'+stem+'_Tumor.cct',sep='\t',index_col=0);n=pd.read_csv('input/HS_CPTAC_CCRCC_'+stem+'_Normal.cct',sep='\t',index_col=0)
 valid=r.status=='tested';assert np.allclose(stats.false_discovery_control(r.loc[valid,'p_value'].to_numpy(),method='bh'),r.loc[valid,'q_value'].to_numpy(),rtol=1e-9,atol=1e-300)
 for g in ['CA9','NNMT','MTOR','NDUFA4L2','MT1H']:
  a=t.loc[g,c].to_numpy();b=n.loc[g,c].to_numpy();ok=np.isfinite(a)&np.isfinite(b);test=stats.ttest_rel(a[ok],b[ok]);ci=test.confidence_interval();rr=r.loc[g];assert np.isclose(test.pvalue,rr.p_value,rtol=1e-9,atol=1e-300);assert np.allclose([ci.low,ci.high],[rr.ci_low,rr.ci_high]);assert ok.sum()==rr.n
 checks.append(l+': independent scipy paired t/CI checks for five shortlist genes; scipy BH checked for full tested family')
assert len(c)==72 and len(set(c))==72 and 'C3N-00314' not in c
checks+=['72 unique common case IDs; contaminated normal pair excluded','All four PNGs visually inspected: axes/scales readable; revise untestable VEGFA marker to explicit no estimate','No remote CDN, script or stylesheet dependency']
j=pd.read_csv('tables/rna_protein_comparison.csv');opp=j[(j.mean_difference_protein*j.mean_difference_rna<0)&(j.q_value_protein<.05)&(j.q_value_rna<.05)].copy();opp['abs_protein_difference']=opp.mean_difference_protein.abs();opp.sort_values('abs_protein_difference',ascending=False).head(5).to_csv('tables/discordant_examples.csv',index=False)
profile=json.load(open('data_profile.json'));diagnostics=json.load(open('diagnostics.json'))
review={'scope':'same-session technical checks, not independent evaluation','checks':checks,'opposite_direction_both_q005':len(opp),'unresolved':[{'severity':'serious','issue':'No independent evaluation yet','action':'Fresh-session artifact review; controller remains blocked'},{'severity':'serious','issue':'Potential tissue/abundance-dependent missingness and assay-selection bias','action':'Investigate missingness mechanism and targeted orthogonal assays; do not generalize sparse genes'},{'severity':'serious','issue':'Processed-scale batch/purity and tissue-composition confounding unresolved','action':'Review processing and sample batches; obtain purity/composition information before mechanistic interpretation'},{'severity':'routine','issue':'Shortlist data selection and nominal CIs','action':'Independent validation of exploratory candidates; no selective-inference claim'}], 'profile':profile,'shortlist_leave_one_out_direction_stable':all(d['loo_mean_min']*d['loo_mean_max']>0 for d in diagnostics)}
Path('validation.json').write_text(json.dumps(review,indent=2));print(json.dumps({'checks_passed':True,'opposite_direction_both_q005':len(opp),'shortlist_leave_one_out_direction_stable':review['shortlist_leave_one_out_direction_stable']}))
