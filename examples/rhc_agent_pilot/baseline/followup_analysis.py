"""Offline sensitivity follow-up. Does not execute or overwrite the initial analysis."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ['MPLCONFIGDIR']=str(ROOT/'.mplconfig')
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import ast, hashlib, json, platform, warnings, base64, html
import numpy as np, pandas as pd, sklearn, scipy, matplotlib
matplotlib.use('Agg')
import subprocess
_orig=subprocess.check_output
def safe_fonts(args,*a,**kw):
    if args[0] in ('fc-list','system_profiler'):raise OSError('Use bundled fonts')
    return _orig(args,*a,**kw)
subprocess.check_output=safe_fonts
try:import matplotlib.pyplot as plt
finally:subprocess.check_output=_orig
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
prior=json.loads(Path('results.json').read_text())
expected=prior['source_sha256']
assert sha('input/rhc.csv')==expected=='811bad3c113c26acc64c00ed149993b09dd320cf2540b750738f5656233d2ec6'
protected=['report.html','report.md','results.json','decision_log.md','analysis.py','build_report.py']+[str(p) for p in Path('figures').glob('*')]
before={p:sha(p) for p in protected}
D=pd.read_csv('input/rhc.csv');n=len(D)
assert n==prior['n']==5735 and D.ptid.notna().all() and D.ptid.is_unique
assert set(D.swang1)=={'RHC','No RHC'} and set(D.dth30)=={'Yes','No'}
assert not D[['swang1','dth30']].isna().any().any()
T=(D.swang1=='RHC').to_numpy().astype(int);Y=(D.dth30=='Yes').to_numpy().astype(int)
counts={'rhc':int(T.sum()),'no_rhc':int((1-T).sum()),'deaths_rhc':int(Y[T==1].sum()),'deaths_no_rhc':int(Y[T==0].sum())}
assert counts==prior['counts']
# Extract only the exact saved definitions and exclusion list, avoiding top-level writes/bootstrap.
tree=ast.parse(Path('analysis.py').read_text())
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='drop' for t in node.targets):drop=ast.literal_eval(node.value)
features=[c for c in D if c not in drop]
fit_warnings=[]
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in ['design','propensity','weights','contrast','balance']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'analysis.py extracted definitions','exec'))
assert len(features)==53
reduced=[c for c in features if c not in ['adld3p','urin1']]
X=design(D,cols=features)
versions={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'matplotlib':matplotlib.__version__}
assert versions==prior['versions']
rows=[]; reproduction=[]; models={}; balance_rows=[]
for spec,cols in [('original',features),('reduced',reduced)]:
    xx=design(D,cols=cols);p=propensity(xx,T)
    assert len(xx)==n and np.isfinite(xx.to_numpy(dtype=float)).all() and np.isfinite(p).all()
    if spec=='reduced':pd.testing.assert_frame_equal(xx,X.drop(columns=['adld3p','urin1']))
    models[spec]={'variables':cols,'encoded_terms':list(xx.columns),'ps_range':[float(p.min()),float(p.max())], 'ps_quantiles_by_group':{str(t):np.quantile(p[T==t],[0,.01,.05,.5,.95,.99,1]).tolist() for t in [0,1]}}
    for clip in [.01,.02,.05]:
        w=weights(p,T,clip);r=contrast(Y,T,w)
        smd=balance(X,T,w); retained=balance(xx,T,w)
        row={'specification':spec,'clip':clip,'n':n,**r,'confidence_intervals':None,'clipped_n':int(((p<clip)|(p>1-clip)).sum()),'max_weight':float(w.max()),'ess_rhc':float(w[T==1].sum()**2/(w[T==1]**2).sum()),'ess_no_rhc':float(w[T==0].sum()**2/(w[T==0]**2).sum()),'max_abs_smd_retained':float(retained.max()),'retained_terms_above_010':int((retained>.1).sum()),'max_abs_smd_original_terms':float(smd.max()),'original_terms_above_010':int((smd>.1).sum()),'excluded_variable_smd':{c:float(smd[X.columns.get_loc(c)]) for c in ['adld3p','urin1']}}
        rows.append(row)
        balance_rows.extend({'specification':spec,'clip':clip,'term':c,'abs_smd':float(v)} for c,v in zip(X.columns,smd))
        if spec=='original':
            saved=next(s for s in prior['sensitivity'] if s['specification']==f'Legacy PS clipping {clip:g}')
            delta=max(abs(r[k]-saved[k]) for k in r)
            assert delta<1e-10
            reproduction.append({'clip':clip,'maximum_absolute_point_estimate_difference':delta,'tolerance':1e-10,'passed':True})
assert not fit_warnings,fit_warnings
changes=[]
for c in [.01,.02,.05]:
    a=next(r for r in rows if r['clip']==c and r['specification']=='original');b=next(r for r in rows if r['clip']==c and r['specification']=='reduced')
    changes.append({'clip':c,'rd_change_percentage_points':100*(b['rd']-a['rd']),'rr_change':b['rr']-a['rr']})
missing={c:{'n':int(D[c].isna().sum()),'percent':float(D[c].isna().mean()*100)} for c in ['adld3p','urin1','cat2']}
pd.DataFrame(balance_rows).to_csv('followup_balance.csv',index=False)
uncertainties=['Potential confounder deletion may increase residual confounding; neither specification is a justified sufficient adjustment set.','Within-day exposure/covariate ordering, eligibility and early-event selection remain unresolved.','Single median imputation and categorical reference-level missingness encoding remain; MAR/MNAR and cat2 structural missingness are unverified.','Prior audit flagged 11 recorded survivors with last contact before day 30; outcome ascertainment remains unresolved.','No new confidence intervals, bootstrap, multiple imputation or MNAR analysis; no statistical significance claim about estimates or their differences.','Balance and finite weights cannot establish causal identification or structural positivity. No human scientific approval or independent review is implied.']
R={'status':'exploratory association sensitivity; causal readiness not_ready; no human scientific approval','contrast':'Recorded 30-day mortality in day-1 RHC versus No RHC among all 5735 supplied patients; normalized propensity-weighted RD and RR','input_sha256':expected,'counts':counts,'excluded_rows':0,'missingness':missing,'models':models,'estimates':rows,'reduced_minus_original':changes,'original_reproduction_checks':reproduction,'versions':versions,'fit_warnings':fit_warnings,'uncertainty':'Point estimates only; confidence intervals not calculated or carried forward.','remaining_uncertainties':uncertainties,'method':{'encoding':'Exact saved design(): get_dummies(drop_first=True,dummy_na=False); numeric median imputation then zero fallback; no missingness indicators','propensity':'Exact saved propensity(): StandardScaler then LogisticRegression(max_iter=5000,C=1.0), existing sklearn defaults','weights':'p clipped to [c,1-c]; stabilized weights T*Pr(T=1)/p + (1-T)*Pr(T=0)/(1-p); risks normalized within each exposure group','clipping':'No patient trimming; each model fitted once, then weights and contrasts recomputed for each threshold','balance':'Fixed unweighted pooled SD; original encoded/imputed 72-term matrix for common diagnostics, plus retained-term diagnostics; imputed ADL/urine SMDs do not assess missingness bias'}}
dump('followup_results.json',R)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(12,5.5))
for ax,key,scale,null,xlim,label in [(axes[0],'rd',100,0,(-.5,8),'Risk difference (percentage points)'),(axes[1],'rr',1,1,(.985,1.26),'Risk ratio (RHC / No RHC)')]:
    ax.axvline(null,color='#7a8490',ls='--',lw=1)
    for spec,offset,color,marker in [('original',.12,'#15324f','o'),('reduced',-.12,'#b95625','D')]:
        rr=[r for r in rows if r['specification']==spec]
        yy=np.arange(3)+offset;xx=[r[key]*scale for r in rr]
        ax.scatter(xx,yy,color=color,marker=marker,s=65,label='Original: 53 variables' if spec=='original' else 'Reduced: 51 variables',zorder=3)
        for x,y in zip(xx,yy):ax.annotate(f'{x:.2f}' if key=='rd' else f'{x:.3f}',(x,y),xytext=(8,0),textcoords='offset points',va='center',fontsize=10,color=color)
    ax.set(xlim=xlim,ylim=(-.5,2.6),yticks=[0,1,2],yticklabels=['0.01 / 0.99','0.02 / 0.98','0.05 / 0.95'],xlabel=label)
    ax.set_title('RHC minus No RHC' if key=='rd' else 'RHC divided by No RHC',loc='left',fontsize=12)
    ax.text(null,2.39,'Null = '+str(null),ha='left',fontsize=9,color='#657080')
    ax.grid(axis='x',alpha=.15)
axes[0].set_ylabel('Propensity clipping bounds')
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.09),ncol=2,frameon=False)
fig.suptitle('Removing ADL and urine output changes the weighted association',fontsize=15,y=.98)
fig.text(.5,.035,'All 5,735 patients retained • Point estimates only; no intervals calculated • Exploratory, not causal',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.18,1,.93));fig.savefig('followup_comparison.png',dpi=170);plt.close(fig)

summary='Excluding adld3p and urin1 increased the estimated positive association at every clipping threshold. '
summary+='The RD increased by '+', '.join(f"{v['rd_change_percentage_points']:.2f} pp at {v['clip']:.2f}" for v in changes)+'.'
summary+=' '+'Removing the variables worsened balance on median-imputed ADL: absolute SMD rose from about 0.039 to 0.165–0.166 across thresholds. Urine-output SMD rose from 0.033–0.038 to 0.080–0.086. Retained-term maximum SMDs remained below 0.07 in the reduced model. This diagnostic does not validate deletion or resolve bias from missing values.'
method='Both specifications retain all 5,735 patients (2,184 RHC; 3,551 No RHC), with 830 and 1,088 recorded deaths respectively. Original adjustment uses 53 variables; reduced adjustment uses exactly the same set except adld3p and urin1 (51 variables). All other column order, encoding, imputation, scaling, logistic model settings and risk calculations match the saved analysis. Cat2 remains included. Numeric missing values use cohort medians (zero fallback), and categorical missingness maps to the reference level. The logistic model uses standardized predictors, C=1.0 and max_iter=5000 with unchanged library defaults. Propensities are clipped symmetrically to [c,1-c]; stabilized inverse-propensity weights are normalized within exposure groups to calculate risks. Clipping changes weights, not cohort membership.'
reuse='Reused decision_log.md decisions 2–3 and 5–9, report.md limitations, results.json cohort counts/software versions/point-estimate benchmarks, analysis.py exact design/propensity/weights/contrast/balance functions and excluded-column list, input/SOURCE.md attribution and analysis-input fingerprint, and selected local dictionary entries. The original report.html and five figures were fingerprinted for preservation; their analyses were not rerun wholesale. Local dictionary text required cp1252 decoding after a UTF-8 read failed. Source attribution (Vanderbilt SUPPORT/RHC; Connors et al., JAMA 1996, PMID 8782638) is inherited, not newly externally verified.'
rerun='Actually reran SHA256 verification before model reuse, cohort/ID/exposure/outcome/count checks, missingness counts for the three named fields, both propensity fits, six sets of weights and weighted risks/RD/RR, clipping counts, weight maxima, Kish effective sample sizes and balance diagnostics. Verified identical retained design columns, software versions and reproduction of all three saved original point-estimate specifications to tolerance 1e-10. No bootstrap or intervals were computed; old intervals are not reused. Initial discovery, broad date audits, Table 1, original figures, alternative missingness models and restricted-history models were not rerun.'
warning='Deleting potential confounders is a sensitivity exercise, not a repair that establishes causal validity. No new confidence intervals are available, so these point-estimate changes do not establish a statistically distinguishable difference. No user scientific approval or causal readiness is implied.'
header=['Clip c','Adjustment','RHC risk (%)','No RHC risk (%)','RD (pp)','RR']
table=[[f"{r['clip']:.2f}",r['specification'],f"{100*r['risk_rhc']:.2f}",f"{100*r['risk_no_rhc']:.2f}",f"{100*r['rd']:.2f}",f"{r['rr']:.3f}"] for r in sorted(rows,key=lambda r:(r['clip'],r['specification']))]
diaghead=['Clip','Adjustment','Clipped n','Max weight','ESS RHC','ESS No RHC','Max SMD retained','ADL SMD','Urine SMD']
diag=[[f"{r['clip']:.2f}",r['specification'],str(r['clipped_n']),f"{r['max_weight']:.2f}",f"{r['ess_rhc']:.0f}",f"{r['ess_no_rhc']:.0f}",f"{r['max_abs_smd_retained']:.3f}",f"{r['excluded_variable_smd']['adld3p']:.3f}",f"{r['excluded_variable_smd']['urin1']:.3f}"] for r in sorted(rows,key=lambda r:(r['clip'],r['specification']))]
miss='; '.join(f"{c}: {v['n']:,}/{n:,} missing ({v['percent']:.1f}%)" for c,v in missing.items())+'.'
def mdtable(h,rows):return '\n'.join(['| '+' | '.join(h)+' |','| '+' | '.join(['---']*len(h))+' |']+['| '+' | '.join(r)+' |' for r in rows])
sections=[('Interpretation',summary+'\n\n'+warning),('Methods',method+'\n\n'+miss),('Reuse and provenance',reuse+'\n\nVerified analysis-input SHA256: `'+expected+'`.'),('Operations rerun',rerun),('Remaining uncertainty and next steps','\n'.join('- '+u for u in uncertainties)+'\n\nBefore causal analysis: recover timing and eligibility rules, clarify ascertainment and cat2 missingness, establish a clinically justified adjustment set, and design appropriate missing-data sensitivity and inference.'),('Reproduce','Run `/tmp/biostat-rhc-analysis-env/bin/python followup_analysis.py` from this folder. No dependencies installed; no network, MCP, runtime, SQLite or other study arms used. Model work was not delegated. Outputs: followup.html, FOLLOWUP.md, followup_results.json, followup_comparison.png, followup_balance.csv and context_sources.json.')]
md='# RHC follow-up: removing ADL and urine output\n\n'+summary+'\n\n'+warning+'\n\n'+mdtable(header,table)+'\n\n![Annotated risk difference and risk ratio comparison](followup_comparison.png)\n\n'
md+='\n\n'.join('## '+h+'\n\n'+v for h,v in sections[1:])+'\n\n## Weighting diagnostics\n\n'+mdtable(diaghead,diag)+'\n\nSMDs use the fixed original imputed/encoded matrix; good balance cannot establish identification. Omitted-variable diagnostics use median-imputed values and do not resolve their missingness.\n'
Path('FOLLOWUP.md').write_text(md)
def ht(h,rows):return '<table><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in h)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table>'
page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RHC adjustment sensitivity</title><style>body{font:17px/1.6 system-ui,sans-serif;color:#15324f;max-width:1120px;margin:40px auto;padding:0 24px}h1,h2{line-height:1.2}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:9px;text-align:left;border-bottom:1px solid #ddd}th{background:#eef4f6}img{width:100%;height:auto}.note{background:#fff1e7;padding:18px}code{overflow-wrap:anywhere} @media print{body{margin:0}}</style><h1>RHC follow-up: removing ADL and urine output</h1><p>'+html.escape(summary)+'</p><p class="note">'+html.escape(warning)+'</p>'+ht(header,table)+'<img alt="Annotated risk-difference and risk-ratio point estimates comparing original and reduced adjustment at three clipping thresholds" src="data:image/png;base64,'+base64.b64encode(Path('followup_comparison.png').read_bytes()).decode()+'">'
for h,v in sections[1:]:page+='<h2>'+h+'</h2><p>'+html.escape(v).replace('\n','<br>')+'</p>'
page+='<h2>Weighting diagnostics</h2>'+ht(diaghead,diag)+'<p>ADL and urine SMDs use the original median-imputed columns, including for the reduced model. They cannot assess missingness bias. Good balance cannot establish causal identification.</p></html>'
Path('followup.html').write_text(page)
assert before=={p:sha(p) for p in protected}
read_roles={'decision_log.md':'saved decisions 2–3, 5–9','report.md':'saved report and limitations','results.json':'fingerprint, counts, versions, original sensitivity point estimates','analysis.py':'AST-extracted exact functions and exclusion list; not executed wholesale','input/SOURCE.md':'source attribution and analysis-input fingerprint','input/rhc_dictionary.html':'selected swang1/dth30/adld3p/urin1 entries decoded cp1252','input/rhc.csv':'verified unchanged before read; data for two fits','AGENTS.md':'user-supplied scope instructions'}
context={'records_read':[{'path':p,'sha256':sha(p),'used_for':v} for p,v in read_roles.items()],'skills_read':['/Users/amiee/.codex/skills/biostatistics/SKILL.md']+['/Users/amiee/.codex/biostat-superpowers/skills/'+x+'/SKILL.md' for x in ['causal-inference','method-evaluation','statistical-analysis','missing-data']],'reuse_checks':{'input_sha256_verified':True,'counts_and_ids_verified':True,'versions_identical':True,'retained_design_columns_identical':True,'original_point_estimates':reproduction,'protected_files_unchanged':True},'protected_sha256':before,'operations_rerun':rerun,'remaining_uncertainties':uncertainties,'figure_inspection':'pending visual inspection by assistant','scope':'ordinary files only; no delegation, runtime, SQLite, MCP, network or installations; other study arms not accessed'}
dump('context_sources.json',context)
print(json.dumps({'changes':changes,'estimates':rows,'missingness':missing,'reproduction':reproduction},indent=2))
