#!/usr/bin/env python3
"""Build offline follow-up from saved sensitivity tables and registry snapshots."""
from pathlib import Path
import json,hashlib,html,base64
import numpy as np,pandas as pd
from scipy import stats
P=Path(__file__).resolve().parent;O=P/'followup_outputs'
R=json.loads((P/'followup_results.json').read_text());C=json.loads((P/'context_sources.json').read_text());S=pd.read_csv(O/'shortlist_comparison.csv')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
notes={
'NCT03849118':'Diagnostic imaging: ZIRCON uses 89Zr-girentuximab PET/CT. The registry intervention explicitly lists 89Zr-TLX250 as another name. Reused ZIRCON literature concerns this same trial, not an additional independent study. No therapeutic efficacy conclusion.',
'NCT00087022':'Treatment: randomized adjuvant girentuximab versus placebo after surgery for nonmetastatic kidney cancer. Completed phase 3 and posted results do not establish benefit; no efficacy extraction or new efficacy claim made here.',
'NCT05663710':'Treatment: 177Lu-girentuximab combined with cabozantinib and nivolumab in advanced ccRCC. Combination study does not isolate the effect of CA9 targeting; no posted results in this snapshot.',
'NCT05239533':'Treatment: 177Lu-girentuximab plus nivolumab; also includes diagnostic 89Zr-girentuximab scans. The diagnostic component must not be described as treatment. No posted results in this snapshot.',
'NCT07197580':'Treatment: advanced relapsed/recurrent ccRCC. Registry intervention explicitly verifies 177Lu-TLX250 as 177Lu girentuximab tetraxetan. Phase 3/recruiting is development status, not demonstrated efficacy; no posted results in this snapshot.',
'NCT01144169':'NNMT is a secondary serum biomarker outcome in a hydroxychloroquine study, not a verified drug target. Terminated for accrual barriers (surgery delay/additional visits), not a reported efficacy failure. No posted results. This is not evidence of an NNMT-targeting therapy.'}
selected=[]
for r in C['trial_records']:
 if r['nct_id'] in notes:
  r['review_interpretation']=notes[r['nct_id']];selected.append(r)
C['reviewed_records']=selected;C['review_scope']='Six illustrative relevant records reviewed against intervention, purpose, status/date and summary fields; remaining search returns are archived but not asserted to be verified target-directed trials. No new literature requests.'
C['reused_artifact_hashes']={f:sha(P/f) for f in ['DECISIONS.md','analysis_config.json','analysis.py','results.json','method_review.json','report.md','sources/annotations.json','sources/target_evidence_matrix.json','sources/evidence_records.json','sources/source_manifest.json','input/SOURCE.md']}
(P/'context_sources.json').write_text(json.dumps(C,indent=2))
fmt=lambda v: '—' if pd.isna(v) else f'{v:.3g}'
lines=[]
def p(t):lines.append(t+'\n')
def table(headers,rows):
 lines.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')
p('# Stage I–II sensitivity and bounded trial context')
p('The original paired molecular shortlist persists descriptively in the Stage I–II subset: CA9 and NNMT increase in both layers, MTOR decreases in both, and VEGFA increases in RNA but remains unevaluable in protein. Reapplying the original exploratory selection rule again selects NDUFA4L2 and MT1H in both cohorts. This is an overlapping-cohort sensitivity analysis, not independent replication or proof of robustness, stage interaction, or clinical benefit.')
p('## Input integrity and cohort')
p('All nine input file SHA256 hashes and byte counts match the original manifest. Combined fingerprint: `'+R['input_fingerprint']+'`. The original all-four-assay cohort was reconstructed under the saved histology and contaminated-normal exclusions, and its size verified as 72. Authoritative `input/clinical_annotation.csv`, field `Tumor_Stage_Pathological`, supplies exact Stage I/Stage II eligibility; no older CLI staging was used. Stage I: 28; Stage II: 9; Stage III: 23; Stage IV: 12; missing/unknown stage: 0. The early-stage cohort contains 37 original cases, excluding 35 Stage III–IV cases. No cases were added from layer-specific cohorts.')
p('## Estimator and changing testing families')
p('The estimand is the mean within-case tumor-minus-normal difference in the selected cohort, estimated from each gene’s available finite pairs. Protein remains supplied processed TMT log2 reference ratios; RNA remains supplied log2 FPKM. No re-log, cross-layer subtraction, imputation, covariate adjustment or outlier removal. Exact original `analyze` and `bh` functions were extracted from `analysis.py` without executing its top-level analysis. Eligibility now requires both ≥80% finite pairs within the respective cohort and ≥20 pairs: 58/72 all-stage and 30/37 early-stage. Ineligible genes retain descriptive values where available but have no p/q/interval. Zero-variance differences have undefined inference and are excluded from BH.')
p('Two-sided paired t tests and pointwise 95% t intervals use the sample SD of paired differences, SE = SD/√n and n−1 degrees of freedom. BH is recomputed separately for each of four layer/cohort families over valid retained p-values. Intervals are model-based, not simultaneous or selection-adjusted; they assume independent cases and approximately normal sampling of the mean. BH control relies on its usual dependence conditions; arbitrary gene dependence is not guaranteed to satisfy them.')
rr=[]
for c,z in R['summary'].items():
 for l,x in z['layers'].items():rr.append([c,l,z['cases'],z['minimum_pairs'],x['total_genes'],x['pass_completeness'],x['tested'],x['status_counts'].get('zero_variance',0),x['q_lt_005']])
table(['Cohort','Layer','Cases','Min pairs','Input genes','Pass completeness','BH family','Zero variance','q<0.05'],rr)
p('The original ≥20-pair protein family contained 10,033 tests; the fair all-stage comparator now contains 8,054. All-stage means are numerically unchanged, but protein BH q-values change with the smaller family. RNA all-stage inference is unchanged. Protein has 46 tested genes unique to all-stage and 79 unique to early-stage; 100 RNA genes become constant and untestable in early-stage. Cohort-specific completeness can therefore retain more protein genes in the smaller cohort. These family changes and reduced sample size/power preclude reading significance changes as biological differences.')
p('## Direction and ranking comparisons')
rr=[]
for l,x in R['comparisons'].items():rr.append([l,x['common_tested'],f'{x["direction_agreement"]:.1%}',f'{x["signed_effect_spearman"]:.3f}',f'{x["absolute_effect_spearman_common_genes"]:.3f}',str(x['top50_overlap'])+'/50',x['significant_all_only'],x['significant_early_only']])
table(['Layer','Common tested','Same direction','Signed-effect Spearman','Absolute-effect Spearman','Top-50 overlap','q<.05 all only','q<.05 early only'],rr)
p('Rank correlations use genes tested in both cohorts; absolute-effect ranks in the full tables use each cohort’s own tested family, descending absolute mean difference with gene-name tie-breaks. Top-50 overlap compares each family’s top 50. Significance-transition counts above concern only common tested genes. Correlations are descriptive, with no gene-independent p-values: genes are correlated and the cohorts share 37 cases. Difference in significance is not a test of interaction; no independent-cohort or all-versus-subset difference test was run.')
p('RNA/protein direction agreement within each cohort is 5,859/7,638 (76.7%) all-stage and 5,804/7,670 (75.7%) early-stage. These use different jointly tested gene sets and available pairs and are not a biological change estimate. RNA is finite for every case; protein completeness can still select case subsets.')
p('![Comparative effects](followup_outputs/effect_comparison.png)')
p('## Prespecified genes and original exploratory shortlist')
p('CA9, NNMT, VEGFA and MTOR are the four user-prespecified genes. NDUFA4L2 (verified current symbol COXFA4L2) and MT1H were selected in the initial data and remain exploratory. The unchanged selection rule uses protein q<0.05, ≥90% finite pairs, an available RNA test, then descending absolute protein mean difference; excludes the four prespecified genes. The ≥90% cutoff is 65 all-stage and 34 early-stage pairs. No drug or RNA-direction selection filter was introduced.')
rr=[]
for g in R['original_shortlist']:
 for l in ['protein','rna']:
  for c in ['all_stage','early_stage']:
   v=S.query('gene==@g and layer==@l and cohort==@c').iloc[0]
   rr.append([g+('*' if g not in ['CA9','NNMT','VEGFA','MTOR'] else ''),l,c,int(v.n),fmt(v.mean_difference),fmt(v.ci95_low)+' to '+fmt(v.ci95_high),fmt(v.q),fmt(v.abs_effect_rank)])
table(['Gene','Layer','Cohort','Pairs','Mean Δ','95% paired CI','BH q','Absolute rank'],rr)
p('*Initially data-selected. All tested shortlist effects retain direction and q<0.05. CA9 protein rank stays 26; NNMT changes 10→17. NDUFA4L2 and MT1H remain protein ranks 1 and 2. MTOR’s decrease is total abundance, not a measurement of kinase activity. VEGFA protein n=1 all-stage and n=0 early-stage: no valid paired inference. Protein and RNA differences have distinct supplied scales and must not be compared as identically calibrated quantities.')
p('![Shortlist intervals](followup_outputs/shortlist_comparison.png)')
p('Leave-one-pair-out shortlist mean ranges preserve all tested directions (saved in shortlist_comparison.csv). Several early-stage RNA paired-difference distributions are strongly skewed (CA9 −4.05, VEGFA −3.99, NDUFA4L2 −3.40); t intervals remain the prespecified model-based intervals, but finite-sample coverage is not guaranteed. Direction stability under one deletion does not validate interval coverage or remove selection bias. Further resampling/orthogonal validation would be useful before stronger claims.')
p('## Registered trial context: two bounded concepts')
p('Retrieved 2026-09-24 UTC directly from ClinicalTrials.gov API v2. Exactly two new requests: kidney cancer with `CA9 OR girentuximab` (49 records) and kidney cancer with `NNMT OR "nicotinamide N-methyltransferase"` (1 record). Each was capped at 50; neither response had another page. All-field search hits are not necessarily target-directed trials. Agent naming was grounded in cached CA9 Open Targets/literature and intervention fields; no guessed NNMT drug aliases. Six illustrative records were reviewed below; remaining hits are archived without target/efficacy adjudication.')
rr=[]
for r in selected:
 rr.append([f'[{r["nct_id"]}]({r["url"]})',r['primary_purpose'],', '.join(r['phases']),r['status'],r['last_update_posted']['date']+' ('+r['last_update_posted']['type']+')',r['last_verified'],str(r['has_results'])])
table(['Registry','Purpose','Phase','Status as retrieved','Last update posted','Status verified','Results posted'],rr)
for r in selected:p('**'+r['nct_id']+'** — '+r['review_interpretation'])
p('The NNMT hit lists nicotinamide N-methyltransferase among secondary serum biomarker outcomes. Hydroxychloroquine was not verified as an NNMT-targeting agent and is not presented as one. No verified NNMT-targeting kidney treatment trial was identified in this bounded search; that is not proof none exist. Registry statuses are sponsor-reported snapshots and may be stale (especially older records); dates are preserved exactly. Phase, recruitment status and posted-results flags are not efficacy evidence. Diagnostic imaging localization does not establish therapeutic benefit. Advanced-disease combination trials cannot validate treatment response in these early-stage tissue samples. No efficacy estimates were newly extracted.')
p('## Reuse, reruns and continuation')
p('Reused without new literature/annotation requests: DECISIONS.md, analysis_config.json, original estimator/BH function bodies from analysis.py, original results.json shortlist, report.md and method_review.json limitations; cached UniProt identities/pathways, Open Targets candidate records and evidence_records.json interpretations. Source URLs, original retrieval timestamps and hashes are carried into context_sources.json. Original source-response hashes were verified before reuse. Existing literature remains abstract-level where originally documented, with unresolved cohort overlap; ZIRCON reanalysis is not a new independent trial. No new annotation, pathway-enrichment, or efficacy claim was added.')
p('Rerun: nine input hash/byte checks and combined fingerprint; reconstruction of original cross-modal cases; authoritative stage restriction; paired summaries/t inference under each cohort’s completeness rule; all four BH families; direction/rank/selection comparisons; shortlist leave-one-out/skewness diagnostics; two registry API requests and six record reviews; two comparative figures and offline report. Initial layer-specific sensitivity, initial bootstrap analysis, initial plots and full initial analysis were not rerun. Original all-stage estimates were compared numerically to saved outputs.')
p('Original files are enumerated in followup_outputs/original_hashes.json; final verification checks them byte-for-byte, including report.html, results.json, figures, config, code, raw data and source snapshots. Both new PNGs were opened and visually inspected for labels, intervals, missing VEGFA inference and cohort comparison. This is same-agent verification, with independent review still pending; no scientific/human approval is claimed.')
p('Reproduce using `/tmp/biostat-rhc-analysis-env/bin/python followup_analysis.py`, then `followup_trials.py`, then `followup_report.py` in this folder. The trial script reuses saved followup_sources responses on rerun (no silent status refresh). The analysis script refuses changed original artifacts or inputs. followup_results.json stores cohorts, summaries, full-precision shortlist estimates and methods; followup_outputs contains complete gene tables, comparisons and diagnostics. context_sources.json stores requests, source hashes, full returned record metadata, reviewed relevance and reused sources. followup_outputs/validation.json records checks. No dependencies installed, delegation, runtime, MCP, SQLite or other-arm reads.')
p('## Unresolved limitations and review priorities')
p('Selection is explicit: availability of all four assays, finite protein pairs, pathological stage and data-selected shortlist can each alter the population represented. Missingness may depend on abundance (MNAR); 80% completeness does not solve this. Adjacent tissue is not healthy-donor kidney. Purity/cell composition, stage-associated case mix and tissue-confounded batch/processing may explain contrasts. Processed input scales and raw processing were not re-audited. Sample size and families changed, and the nested samples mechanically favor concordance. No stage interaction, equivalence or robustness proof follows. Independent specimens, assay specificity/localization checks, defensible missingness sensitivity and fuller batch/provenance review remain research priorities. Registry results and full texts need separate appraisal before translational decisions. These outputs are bounded exploratory associations, not causal, predictive or clinical efficacy findings.')
md='\n'.join(lines);(P/'FOLLOWUP.md').write_text(md)
# Small dependency-free Markdown renderer for this controlled report, with embedded images.
def inline(s):
 import re
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)',r'<a href="\2">\1</a>',s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s);s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
 return s
parts=[]
for block in md.strip().split('\n\n'):
 if block.startswith('!['):
  path=block.split('](')[1].rstrip(')\n');b64=base64.b64encode((P/path).read_bytes()).decode();parts.append('<img alt="'+html.escape(block[2:block.index(']')])+'" src="data:image/png;base64,'+b64+'">')
 elif block.startswith('| '):
  rr=block.strip().splitlines();parts.append('<div class="scroll"><table><thead><tr>'+''.join('<th>'+inline(v.strip())+'</th>' for v in rr[0].strip('|').split('|'))+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(v.strip())+'</td>' for v in row.strip('|').split('|'))+'</tr>' for row in rr[2:])+'</tbody></table></div>')
 elif block.startswith('# '):parts.append('<h1>'+inline(block[2:])+'</h1>')
 elif block.startswith('## '):parts.append('<h2>'+inline(block[3:])+'</h2>')
 else:parts.append('<p>'+inline(block)+'</p>')
(P/'followup.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ccRCC stage sensitivity</title><style>body{font:16px/1.55 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 24px;color:#172b3a}h1,h2{color:#125677}table{border-collapse:collapse;font-size:14px;width:100%}td,th{padding:8px;border-bottom:1px solid #ccd8dd;text-align:left}th{background:#edf4f6}.scroll{overflow-x:auto}img{width:100%;height:auto}code{overflow-wrap:anywhere}a{color:#006da0}</style>'+''.join(parts)+'</html>')
# Independent direct scipy spot checks, BH reference, preservation and offline structure.
from scipy.stats import false_discovery_control
checks=[]
for c in ['all_stage','early_stage']:
 for l in ['protein','rna']:
  d=pd.read_csv(O/f'{c}_{l}_genes.csv');ok=d.status.eq('tested');assert np.allclose(d.loc[ok,'q'],false_discovery_control(d.loc[ok,'p']),rtol=1e-10,atol=1e-15)
  assert (d.loc[ok,'n']>=R['summary'][c]['minimum_pairs']).all();assert d.loc[~ok,'q'].isna().all();checks.append(c+' '+l+' BH and eligibility checked')
  tag='proteome' if l=='protein' else 'RNAseq_fpkm_log2';a=pd.read_csv(P/'input'/f'HS_CPTAC_CCRCC_{tag}_Tumor.cct',sep='\t',index_col=0);b=pd.read_csv(P/'input'/f'HS_CPTAC_CCRCC_{tag}_Normal.cct',sep='\t',index_col=0)
  for g in R['original_shortlist']:
   row=d.set_index('gene').loc[g]
   if row.status!='tested':continue
   cases=R['cohort_cases'][c];diff=a.loc[g,cases]-b.loc[g,cases];diff=diff[np.isfinite(diff)];test=stats.ttest_1samp(diff,0);ci=test.confidence_interval()
   assert np.isclose(row.p,test.pvalue,rtol=1e-9,atol=0);assert np.allclose([row.ci95_low,row.ci95_high],[ci.low,ci.high])
original=json.loads((O/'original_hashes.json').read_text());assert all(sha(P/f)==v for f,v in original.items())
for r in C['new_requests']:assert sha(P/r['file'])==r['sha256']
h=(P/'followup.html').read_text();assert h.count('data:image/png;base64,')==2 and '<script' not in h and '<img' in h
validation={'checks':checks+['All tested shortlist intervals/p-values independently checked with scipy ttest_1samp','All original artifact hashes unchanged','New source hashes match','Offline HTML embeds both figures; no scripts or remote assets'],'original_files_preserved':len(original),'visual_inspection':'Both actual new PNG files opened and inspected by assistant; no clipping obscuring results','review':'Same-agent checks; independent review pending'}
(O/'validation.json').write_text(json.dumps(validation,indent=2))
print(json.dumps(validation,indent=2))
