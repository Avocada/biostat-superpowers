"""Aggregate checks independent of analysis.py's BH implementation."""
import json,hashlib
from pathlib import Path
import pandas as pd,numpy as np
from statsmodels.stats.multitest import multipletests
P=Path(__file__).resolve().parent;checks={}
for l in ['protein','rna']:
 d=pd.read_csv(P/'outputs'/f'{l}_all_genes.csv');v=d.status.eq('tested');checks[l+'_BH_matches_statsmodels']=bool(np.allclose(d.loc[v,'q'],multipletests(d.loc[v,'p'],method='fdr_bh')[1]));checks[l+'_family_count']=int(v.sum());checks[l+'_CI_brackets_mean']=bool(((d.loc[v,'ci95_low']<=d.loc[v,'mean_difference'])&(d.loc[v,'ci95_high']>=d.loc[v,'mean_difference'])).all());assert checks[l+'_BH_matches_statsmodels'] and checks[l+'_CI_brackets_mean'];assert d.loc[~v,['p','q','ci95_low','ci95_high']].isna().all().all()
for p in (P/'sources').glob('*.provenance.json'):
 d=json.loads(p.read_text());assert hashlib.sha256((P/d['file']).read_bytes()).hexdigest()==d['sha256']
checks['source_checksums_match']=True
from scipy import stats
c=pd.read_csv(P/'input/clinical_annotation.csv');eligible=set(c.loc[c.Histologic_Type.eq('Clear cell renal cell carcinoma'),'Case_ID'])-{'C3N-00314'}
t=pd.read_csv(P/'input/HS_CPTAC_CCRCC_proteome_Tumor.cct',sep='\t',index_col=0);n=pd.read_csv(P/'input/HS_CPTAC_CCRCC_proteome_Normal.cct',sep='\t',index_col=0);rn=pd.read_csv(P/'input/HS_CPTAC_CCRCC_RNAseq_fpkm_log2_Normal.cct',sep='\t',index_col=0);cases=sorted(eligible&set(t.columns)&set(n.columns)&set(rn.columns));pval=stats.ttest_rel(t.loc['CA9',cases],n.loc['CA9',cases]).pvalue;stored=pd.read_csv(P/'outputs/protein_all_genes.csv').set_index('gene').loc['CA9','p'];checks['CA9_direct_ttest_relative_error']=float(abs(pval/stored-1));assert checks['CA9_direct_ttest_relative_error']<1e-10
h=(P/'report.html').read_text();assert 'src="http' not in h and 'cdn.' not in h;checks['html_no_remote_dependencies']=True
(P/'outputs/validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks))
