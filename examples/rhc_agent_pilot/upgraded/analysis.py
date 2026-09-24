#!/usr/bin/env python3
"""Offline RHC audit; no network, no API calls. Run with the supplied environment."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'; os.environ['OMP_NUM_THREADS']='1'; os.environ['MPLCONFIGDIR']=os.path.abspath('.mplconfig')
from pathlib import Path
import sys,json,hashlib,platform,base64,warnings
from dataclasses import asdict
import numpy as np,pandas as pd, scipy, sklearn, statsmodels, statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent; os.chdir(ROOT)
sys.path.insert(0,'/Users/amiee/Projects_code/biostat-superpowers')
from biostat_workflow.controller import WorkflowState,Goal,Stage,Outcome,Result,Policy,route,advance,settle
from biostat_workflow.memory import MemoryStore
for p in ['figures','tables']: Path(p).mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savej(p,x): Path(p).write_text(json.dumps(x,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
RUN='rhc-audit-20260924'; SEED=240924; B=120
contract={'goal':'associational audit, not causal estimation','population':'all supplied SUPPORT rows','unit':'one patient / ptid','exposure':'swang1 == RHC on first qualifying study day','outcome':'supplied dth30 == Yes','primary':'unadjusted 30-day risk difference and risk ratio, RHC versus No RHC','causal_target':'hypothetical initiation during first qualifying day versus no initiation that day, 30-day all-cause mortality in eligible ICU adults; grace period handling unresolved','exclusions':'none if all exposure and outcome labels valid','uncertainty':'independent-patient Wald RD and log-RR; no site identifier available','secondary':'legacy IPTW reproduction; clipping, imputation and feature-set sensitivity; exploratory'}
fp=hashlib.sha256((sha('input/rhc.csv')+sha('input/rhc_dictionary.html')+sha('input/legacy_analysis.py')+json.dumps(contract,sort_keys=True)).encode()).hexdigest();savej('analysis-contract.json',dict(contract,input_fingerprint=fp,run_id=RUN))
d=pd.read_csv('input/rhc.csv');assert sha('input/rhc.csv')=='811bad3c113c26acc64c00ed149993b09dd320cf2540b750738f5656233d2ec6'
assert d.ptid.notna().all() and not d.ptid.duplicated().any()
assert set(d.swang1)=={'RHC','No RHC'} and set(d.dth30)=={'Yes','No'}
t=(d.swang1=='RHC').to_numpy().astype(int);y=(d.dth30=='Yes').to_numpy().astype(int);n=len(d)
drop=['swang1','death','dth30','t3d30','dthdte','lstctdte','dschdte','sadmdte','ptid']; cov=[c for c in d if c not in drop]
# Real runtime transitions, no readiness inferred from the request.
traces={}
def step(s,result,history,policy=Policy()):
    s=settle(s,policy);r=route(s);a=advance(s,result,policy);history.append({'before':asdict(s),'route':asdict(r),'result':asdict(result),'after':asdict(a)});return a
h=[];cs=WorkflowState(Goal.CAUSAL)
cs=step(cs,Result(Outcome.COMPLETE,'analysis-contract.json: hypothetical target specified; operational timing remains a preparation gate'),h)
cs=step(cs,Result(Outcome.BLOCKED,'Dictionary says first qualifying day, but no RHC or covariate timestamps within day. Cannot align eligibility, treatment and follow-up; missing-data and identification gates remain unresolved.'),h,Policy(no_progress_limit=1))
traces['causal']={'transitions':h,'terminal':asdict(cs),'unresolved':['preparation/timing','missing-data mechanism and MI plan','causal identification','independent review']}
h=[];ss=WorkflowState(Goal.INFERENTIAL)
ss=step(ss,Result(Outcome.COMPLETE,'analysis-contract.json: supplied-label crude association is primary'),h)
ss=step(ss,Result(Outcome.COMPLETE,'Validated 5735 unique IDs and complete binary treatment/outcome; no exclusions. Covariate missingness affects exploratory reproduction only.',missing_data_required=False),h)
# Record analyst-reviewed facts, then retrieve them to determine downstream labeling.
with MemoryStore(ROOT/'project-memory.sqlite3','rhc-upgraded-pilot') as mem:
    facts={
      'scope':'Primary is crude supplied-label association; single-imputation weighting is an exploratory legacy reproduction only.',
      'timing':'Dictionary: first day qualifying for SUPPORT. No within-day order confirmed. Do not label all legacy covariates pretreatment.',
      'profile':'MCP profile confirms 5735 rows; cat2 4535 missing, adld3p 4296 missing, urin1 3028 missing. cat2 blanks may be structural, unconfirmed.',
      'source':'PubMed PMID 8782638 abstract confirms prospective cohort, five US teaching hospitals 1989–1994; original matching differs from legacy IPTW.'}
    existing={i.key:i for i in mem.inspect() if i.input_fingerprint==fp}
    for k,v in facts.items():
        if k not in existing:
            mem.record(run_id=RUN,key=k,value=v,source={'profile':'mcp_artifacts/c74883de0afd431daa369af1a4814b22/profile.json','source':'mcp_artifacts/bfde5f6401c24b459b16d2c4258926ec/literature.json','timing':'input/rhc_dictionary.html','scope':'analysis-contract.json'}[k],confirmed_by='Codex analyst: source checked; not human scientific approval',goal=Goal.INFERENTIAL,stages=(Stage.ANALYSIS,Stage.EVALUATION,Stage.REPORTING),input_fingerprint=fp)
    sel=mem.retrieve(goal=Goal.INFERENTIAL,stage=Stage.ANALYSIS,input_fingerprint=fp,required_keys=tuple(facts),max_units=12000,count=len)
    assert sel.usable,sel.issues
    Path('memory-retrieval.txt').write_text(sel.text)
    assert 'exploratory' in sel.text and 'within-day' in sel.text
# Missingness and column role/action ledger.
miss=d.isna().sum();miss.to_csv('tables/missingness-all.csv',header=['missing_n'])
patterns=d[['cat2','adld3p','urin1']].isna().value_counts().rename('n').reset_index();patterns.to_csv('tables/missingness-patterns.csv',index=False)
roles=[]
for c in d:
    roles.append(dict(column=c,role='excluded: ID/date/outcome/exposure' if c in drop else 'legacy candidate; causal role unverified',type=str(d[c].dtype),missing_n=int(miss[c]),timing='unresolved within day' if c not in drop else 'not adjustment covariate',action='excluded from X' if c in drop else ('dummy; missing folded into reference' if d[c].dtype=='object' else 'numeric; median fill if missing'),outliers='retained; no clinical adjudication',primary_use=c in ['swang1','dth30']))
pd.DataFrame(roles).to_csv('tables/column-actions.csv',index=False)
rows=[]
for c in cov:
    for g in [0,1]:
        z=d.loc[t==g,c];a={'variable':c,'group':['No RHC','RHC'][g],'denominator':len(z),'observed':int(z.notna().sum()),'missing':int(z.isna().sum())}
        if pd.api.types.is_numeric_dtype(z): a.update(summary=f'{z.mean():.3g} (SD {z.std():.3g}); median {z.median():.3g} [IQR {z.quantile(.25):.3g}, {z.quantile(.75):.3g}]')
        else: a.update(summary='; '.join(f'{k}: {v} ({100*v/len(z):.1f}%)' for k,v in z.value_counts().items()))
        rows.append(a)
pd.DataFrame(rows).to_csv('tables/table1-all.csv',index=False)
def design(df,variant='legacy'):
    z=df[cov].copy()
    if variant=='missing indicators':
        for c in ['adld3p','urin1']:z[c+'_missing']=z[c].isna().astype(int)
        z['cat2']=z.cat2.fillna('Missing/unspecified')
    if variant=='omit sparse fields':z=z.drop(columns=['cat2','adld3p','urin1'])
    x=pd.get_dummies(z,drop_first=True,dummy_na=False); x=x.apply(pd.to_numeric,errors='coerce');x=x.fillna(x.median(numeric_only=True)).fillna(0)
    return x,StandardScaler().fit_transform(x)
def fit(df,tt,variant='legacy'):
    x,xs=design(df,variant);model=LogisticRegression(max_iter=5000,C=1.0).fit(xs,tt)
    return x,xs,model.predict_proba(xs)[:,1],int(model.n_iter_[0])
def calc(yy,tt,pp=None,clip=.02):
    if pp is None:w=np.ones(len(tt))
    else:
        pp=np.clip(pp,clip,1-clip);w=np.where(tt==1,tt.mean()/pp,(1-tt.mean())/(1-pp))
    r1=np.average(yy[tt==1],weights=w[tt==1]);r0=np.average(yy[tt==0],weights=w[tt==0]);return {'risk_rhc':r1,'risk_no_rhc':r0,'rd':r1-r0,'rr':r1/r0},w
crude,_=calc(y,t);r1=crude['risk_rhc'];r0=crude['risk_no_rhc'];n1=t.sum();n0=n-n1;e1=y[t==1].sum();e0=y[t==0].sum()
se=np.sqrt(r1*(1-r1)/n1+r0*(1-r0)/n0);crude['rd_ci']=[crude['rd']-1.96*se,crude['rd']+1.96*se]
se=np.sqrt(1/e1-1/n1+1/e0-1/n0);crude['rr_ci']=np.exp(np.log(crude['rr'])+np.array([-1,1])*1.96*se).tolist()
x,xs,ps,iters=fit(d,t);weighted,w=calc(y,t,ps)
# Full pipeline patient bootstrap; median/scaling/PS refit per sample.
rng=np.random.default_rng(SEED);boot=[];failed=[]
for b in range(B):
    idx=rng.integers(0,n,n)
    try:
        _,_,bp,_=fit(d.iloc[idx],t[idx]);v,_=calc(y[idx],t[idx],bp);boot.append([v['rd'],v['rr']])
    except Exception as exc:failed.append(str(exc))
boot=np.asarray(boot);weighted['rd_ci']=np.quantile(boot[:,0],[.025,.975]).tolist();weighted['rr_ci']=np.quantile(boot[:,1],[.025,.975]).tolist()
pd.DataFrame(boot,columns=['rd','rr']).to_csv('tables/bootstrap.csv',index=False)
# Conditional OR, not g-computation. Fit same all-covariate specification.
with warnings.catch_warnings(record=True) as warns:
    om=sm.Logit(y,sm.add_constant(np.column_stack([t,xs]))).fit(disp=0,maxiter=200)
    adjusted_or={'or':float(np.exp(om.params[1])),'ci':np.exp(om.conf_int()[1]).tolist(),'converged':bool(om.mle_retvals['converged']),'warnings':[str(z.message) for z in warns]}
# Fixed unweighted SD prevents weighted denominator from obscuring imbalance.
a=xs[t==1];b=xs[t==0];den=np.sqrt((a.var(axis=0)+b.var(axis=0))/2)
before=np.divide(np.abs(a.mean(axis=0)-b.mean(axis=0)),den,out=np.zeros_like(den),where=den>0)
after=np.divide(np.abs(np.average(a,axis=0,weights=w[t==1])-np.average(b,axis=0,weights=w[t==0])),den,out=np.zeros_like(den),where=den>0)
balance=pd.DataFrame({'term':x.columns,'abs_smd_before':before,'abs_smd_after':after}).sort_values('abs_smd_before',ascending=False);balance.to_csv('tables/balance-all.csv',index=False)
# Missingness itself can remain imbalanced, even after median filling.
mb=[]
for c in ['cat2','adld3p','urin1']:
    z=d[c].isna().to_numpy().astype(float);sd=np.sqrt((z[t==1].var()+z[t==0].var())/2)
    mb.append({'variable':c,'before':abs(z[t==1].mean()-z[t==0].mean())/sd,'after':abs(np.average(z[t==1],weights=w[t==1])-np.average(z[t==0],weights=w[t==0]))/sd})
pd.DataFrame(mb).to_csv('tables/missingness-balance.csv',index=False)
sens=[]
for cut in [0,.01,.02,.05]:
    v,ww=calc(y,t,ps,cut);sens.append(dict(label=f'PS clip {cut:g}',**v,n=n,changed_scores=int(((ps<cut)|(ps>1-cut)).sum()),max_weight=float(ww.max())))
for variant in ['missing indicators','omit sparse fields']:
    _,_,pv,_=fit(d,t,variant);v,_=calc(y,t,pv);sens.append(dict(label=variant,**v,n=n))
pd.DataFrame(sens).to_csv('tables/sensitivity.csv',index=False)
quality={'duplicate_ids':int(d.ptid.duplicated().sum()),'missing_ids':int(d.ptid.isna().sum()),'full_row_duplicates':int(d.duplicated().sum()),'t3d30_range':[float(d.t3d30.min()),float(d.t3d30.max())],'no_death_before_30_followup':int(((y==0)&(d.t3d30<30)).sum()),'death_label_date_disagreement':int((((d.dthdte-d.sadmdte)<=30)&d.dthdte.notna()).ne(pd.Series(y==1)).sum()),'age_range':[float(d.age.min()),float(d.age.max())],'zero_weight_values':int((d.wtkilo1==0).sum()),'complete_legacy_covariate_rows':int(d[cov].notna().all(axis=1).sum())}
diag={'features':len(x.columns),'iterations':iters,'ps_range':[float(ps.min()),float(ps.max())],'ps_quantiles_by_group':{str(g):np.quantile(ps[t==g],[0,.01,.1,.5,.9,.99,1]).tolist() for g in [0,1]},'clipped_n':int(((ps<.02)|(ps>.98)).sum()),'max_weight':float(w.max()),'ess':{str(g):float(w[t==g].sum()**2/(w[t==g]**2).sum()) for g in [0,1]},'smd_mean_before':float(before.mean()),'smd_mean_after':float(after.mean()),'smd_max_after':float(after.max()),'terms_above_01_after':int((after>.1).sum())}
ev=weighted['rr']+np.sqrt(weighted['rr']*(weighted['rr']-1))
results={'run_id':RUN,'input_sha256':sha('input/rhc.csv'),'input_fingerprint':fp,'contract':contract,'n':n,'n_rhc':int(n1),'n_no_rhc':int(n0),'deaths_rhc':int(e1),'deaths_no_rhc':int(e0),'crude':crude,'legacy_iptw':weighted,'conditional_adjusted_or':adjusted_or,'diagnostics':diag,'quality':quality,'sensitivity':sens,'evalue_point':float(ev),'bootstrap':{'seed':SEED,'attempted':B,'successful':len(boot),'failed':failed,'method':'patient percentile bootstrap; entire preprocessing/propensity pipeline refitted; single-imputation policy remains fixed; not MI'},'causal_ready':False,'human_approval':False,'independent_review':'pending external reviewer','software':{k:v for k,v in [('python',platform.python_version()),('numpy',np.__version__),('pandas',pd.__version__),('scipy',scipy.__version__),('sklearn',sklearn.__version__),('statsmodels',statsmodels.__version__),('matplotlib',matplotlib.__version__)]}}
ss=step(ss,Result(Outcome.COMPLETE,'results.json and tables: primary crude risks and intervals; separate exploratory reproduction and diagnostics'),h)
ss=step(ss,Result(Outcome.BLOCKED,'Self-audit saved; independent review reserved for later reviewer per user. No human scientific approval. Deliverable is an audit report, not a completed reviewed analysis.'),h,Policy(no_progress_limit=1));traces['associational']={'transitions':h,'terminal':asdict(ss)}
savej('workflow-transitions.json',traces);savej('results.json',results)
Path('requirements-observed.txt').write_text('\n'.join(f'{k}=={v}' for k,v in results['software'].items())+'\n')
# Consistent local publication-style plots.
BLUE='#176B86';ORANGE='#B95D20';INK='#183344';GRAY='#697C89';PALE='#E5EEF1'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':INK,'text.color':INK,'axes.titleweight':'bold','axes.titlesize':15,'figure.facecolor':'#FFFFFF','axes.facecolor':'#FFFFFF','savefig.facecolor':'#FFFFFF'})
def export(fig,name):
    fig.savefig(f'figures/{name}.png',dpi=160,bbox_inches='tight');fig.savefig(f'figures/{name}.svg',bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(11,4));ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
for cx,cy,width,height,text in [(5,3.3,7,.7,'Supplied cohort · 5,735 unique patients\nEarlier screening / exclusions unavailable'),(5,2.15,7,.65,'Valid RHC + mortality labels · 5,735 analyzed\n0 exclusions · no new eligibility restrictions'),(2.4,.75,4.3,.95,f'RHC · {n1:,}\n{e1:,} deaths / {n1:,} = {100*r1:.1f}%'),(7.6,.75,4.3,.95,f'No RHC · {n0:,}\n{e0:,} deaths / {n0:,} = {100*r0:.1f}%')]:
    ax.add_patch(FancyBboxPatch((cx-width/2,cy-height/2),width,height,boxstyle='round,pad=.08',facecolor=PALE,edgecolor='none'));ax.text(cx,cy,text,ha='center',va='center',fontsize=12)
for xy,xytext in [((5,2.55),(5,2.9)),((2.4,1.3),(5,1.78)),((7.6,1.3),(5,1.78))]:ax.annotate('',xy=xy,xytext=xytext,arrowprops={'arrowstyle':'->','color':GRAY})
export(fig,'flow')
fig,ax=plt.subplots(figsize=(10,4.2));ms=['cat2','adld3p','urin1'];pos=np.arange(3)
for g,col,off in [(0,BLUE,-.18),(1,ORANGE,.18)]:
    vals=d.loc[t==g,ms].isna().mean()*100;bars=ax.barh(pos+off,vals,.32,color=col,label=f'{["No RHC","RHC"][g]} (n = {(t==g).sum():,})')
    for bar,val in zip(bars,vals):ax.text(val+1,bar.get_y()+bar.get_height()/2,f'{val:.1f}%',va='center',fontsize=10)
ax.set(yticks=pos,yticklabels=['Secondary diagnosis · cat2','Activities of daily living · adld3p','Urine output · urin1'],xlim=(0,100),xlabel='Missing within exposure group (%)',title='Sparse covariates change what adjustment can mean');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.20),ncol=2);export(fig,'missingness')
fig,(ax,ax2)=plt.subplots(1,2,figsize=(12,6.5),gridspec_kw={'width_ratios':[1.2,1]});z=balance.head(16).iloc[::-1];p=np.arange(len(z))
ax.scatter(z.abs_smd_before,p,c=ORANGE,label='Before',s=30);ax.scatter(z.abs_smd_after,p,c=BLUE,label='Weighted',s=30);ax.axvline(.1,ls='--',c=GRAY,lw=1);ax.set(yticks=p,yticklabels=z.term,xlabel='Absolute SMD · fixed unweighted SD',title='Largest 16 initial imbalances');ax.legend()
for g,col in [(0,BLUE),(1,ORANGE)]:ax2.hist(ps[t==g],bins=np.linspace(0,1,26),histtype='step',linewidth=2,density=True,color=col,label=['No RHC','RHC'][g])
ax2.axvline(.02,c=GRAY,ls=':');ax2.axvline(.98,c=GRAY,ls=':');ax2.set(xlabel='Estimated propensity · before clipping',ylabel='Within-group density',title='Overlap is uneven');ax2.legend();fig.tight_layout(w_pad=3);export(fig,'diagnostics')
fig,axs=plt.subplots(1,2,figsize=(11,3.5))
for ax,key,mul,null,title in [(axs[0],'rd',100,0,'Risk difference (percentage points)'),(axs[1],'rr',1,1,'Risk ratio')]:
    for j,(v,col) in enumerate([(crude,BLUE),(weighted,ORANGE)]):
        lo,hi=np.array(v[key+'_ci'])*mul;est=v[key]*mul;ax.errorbar(est,1-j,xerr=[[est-lo],[hi-est]],fmt='o',color=col,capsize=5,markersize=8);ax.text(hi+.02*(100 if key=='rd' else 1),1-j,f'{est:.2f} [{lo:.2f}, {hi:.2f}]',va='center',fontsize=10)
    ax.axvline(null,color=GRAY,ls='--');ax.set(yticks=[1,0],yticklabels=['Crude · primary','Legacy IPTW\nexploratory'],ylim=(-.6,1.6),xlabel=title);ax.margins(x=.5)
fig.tight_layout(w_pad=2);export(fig,'uncertainty')
fig,ax=plt.subplots(figsize=(10,4));p=np.arange(len(sens));vals=[s['rd']*100 for s in sens];ax.scatter(vals,p,color=ORANGE,s=55);ax.axvline(weighted['rd']*100,c=GRAY,ls=':',label='Legacy 0.02 clip');ax.set(yticks=p,yticklabels=[s['label'] for s in sens],xlabel='Weighted risk difference (percentage points)',title='Analysis choices: point-estimate sensitivity');ax.invert_yaxis()
for xx,yy in zip(vals,p):ax.annotate(f'{xx:+.2f}',(xx,yy),xytext=(8,0),textcoords='offset points',va='center')
ax.margins(x=.4);ax.legend();export(fig,'sensitivity')
print(json.dumps({'crude':crude,'weighted':weighted,'diagnostics':diag,'quality':quality,'bootstrap_success':len(boot)},indent=2))
