"""Offline RHC association audit. Run with supplied scientific Python; no network."""
import os
os.environ["MPLCONFIGDIR"]=os.path.join(os.path.dirname(os.path.abspath(__file__)),".mplconfig")
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[key]='1'
from pathlib import Path
import json, hashlib, platform, warnings, base64
import numpy as np, pandas as pd, scipy, sklearn, matplotlib
matplotlib.use('Agg')
# Avoid blocked OS font discovery; use Matplotlib's bundled fonts only.
import subprocess
_original_check_output = subprocess.check_output
def _font_safe_check_output(args, *a, **kw):
    if args[0] in ('fc-list', 'system_profiler'):
        raise OSError('System font discovery disabled for this local report')
    return _original_check_output(args, *a, **kw)
subprocess.check_output = _font_safe_check_output
try:
    import matplotlib.pyplot as plt
finally:
    subprocess.check_output = _original_check_output
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.stats import norm
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT); Path('figures').mkdir(exist_ok=True)
SEED=20260924; B=80
D=pd.read_csv('input/rhc.csv'); n=len(D)
assert set(D.swang1)=={'RHC','No RHC'} and set(D.dth30)=={'Yes','No'}
assert D.ptid.notna().all() and D.ptid.is_unique
T=(D.swang1=='RHC').to_numpy().astype(int); Y=(D.dth30=='Yes').to_numpy().astype(int)
drop=['swang1','death','dth30','t3d30','dthdte','lstctdte','dschdte','sadmdte','ptid']
features=[c for c in D if c not in drop]
def design(d, missing=False, cols=features):
    z=d[cols].copy()
    if missing:
        for c in cols:
            if z[c].isna().any():
                if not pd.api.types.is_numeric_dtype(z[c]): z[c]=z[c].fillna('Missing / unspecified')
                else: z[c+'_missing']=z[c].isna().astype(int)
    z=pd.get_dummies(z,drop_first=True,dummy_na=False)
    z=z.apply(pd.to_numeric,errors='coerce'); z=z.fillna(z.median()).fillna(0)
    return z
fit_warnings=[]
def propensity(x,t):
    xs=StandardScaler().fit_transform(x)
    with warnings.catch_warnings(record=True) as caught:
        m=LogisticRegression(max_iter=5000,C=1.0).fit(xs,t)
    fit_warnings.extend(str(w.message) for w in caught)
    return m.predict_proba(xs)[:,1]
def weights(ps,t,clip=.02):
    p=np.clip(ps,clip,1-clip); return np.where(t==1,t.mean()/p,(1-t.mean())/(1-p))
def contrast(y,t,w=None):
    w=np.ones(len(y)) if w is None else w
    r1=np.average(y[t==1],weights=w[t==1]); r0=np.average(y[t==0],weights=w[t==0])
    return {'risk_rhc':float(r1),'risk_no_rhc':float(r0),'rd':float(r1-r0),'rr':float(r1/r0)}
X=design(D); ps=propensity(X,T); w=weights(ps,T)
raw=contrast(Y,T); legacy=contrast(Y,T,w)
n1=int(T.sum()); n0=n-n1; e1=int(Y[T==1].sum()); e0=int(Y[T==0].sum())
se=np.sqrt(raw['risk_rhc']*(1-raw['risk_rhc'])/n1+raw['risk_no_rhc']*(1-raw['risk_no_rhc'])/n0)
raw['rd_ci']=[raw['rd']-1.96*se,raw['rd']+1.96*se]
se_log=np.sqrt(1/e1-1/n1+1/e0-1/n0); raw['rr_ci']=list(np.exp(np.log(raw['rr'])+np.array([-1,1])*1.96*se_log))
rng=np.random.default_rng(SEED); boots=[]
for b in range(B):
    ix=rng.integers(0,n,n); db=D.iloc[ix]; tb=T[ix]; yb=Y[ix]
    pb=propensity(design(db),tb); boots.append(contrast(yb,tb,weights(pb,tb)))
for k in ['rd','rr']: legacy[k+'_ci']=np.quantile([v[k] for v in boots],[.025,.975]).tolist()
# A fixed unweighted pooled SD makes before/after differences comparable.
def balance(x,t,w):
    a=x.to_numpy(dtype=float); den=np.sqrt((a[t==1].var(axis=0)+a[t==0].var(axis=0))/2)
    delta=np.average(a[t==1],axis=0,weights=w[t==1])-np.average(a[t==0],axis=0,weights=w[t==0])
    return np.divide(abs(delta),den,out=np.zeros_like(delta),where=den>0)
bal=pd.DataFrame({'term':X.columns,'before':balance(X,T,np.ones(n)),'after':balance(X,T,w)}).sort_values('before',ascending=False)
bal.to_csv('balance.csv',index=False)
miss=pd.DataFrame({'variable':D.columns,'n_missing':D.isna().sum().values,'pct_missing':100*D.isna().mean().values})
for t,label in [(0,'no_rhc'),(1,'rhc')]:miss['pct_'+label]=100*D[T==t].isna().mean().values
miss.to_csv('missingness.csv',index=False)
sens=[]
for clip in [0,.01,.02,.05]:
    ww=weights(ps,T,clip); sens.append({'specification':f'Legacy PS clipping {clip:g}',**contrast(Y,T,ww),'max_weight':float(ww.max())})
p2=propensity(design(D,True),T); sens.append({'specification':'Explicit missing category / indicators',**contrast(Y,T,weights(p2,T))})
restricted=['age','sex','race','edu','income','ninsclas']+[c for c in features if c.endswith('hx')]
p3=propensity(design(D,cols=restricted),T); sens.append({'specification':'Demographics / history only',**contrast(Y,T,weights(p3,T))})
# Public dates are numeric day counts; validate only observable consistency.
delta=D.dthdte-D.sadmdte
checks={'unique_patient_ids':bool(D.ptid.is_unique),'duplicate_rows':int(D.duplicated().sum()),'missing_exposure_outcome':int(D[['swang1','dth30']].isna().any(axis=1).sum()),'dth30_date_disagreement':int(((delta.le(30)&delta.notna())!=(Y==1)).sum()),'negative_death_intervals':int(delta.lt(0).sum()),'no_death30_followup_below30':int(((Y==0)&(D.t3d30<30)).sum()),'min_t3d30':float(D.t3d30.min()),'last_contact_before_day30_among_no_death30':int(((Y==0)&((D.lstctdte-D.sadmdte)<30)).sum()),'candidate_complete_cases':int(D[features].notna().all(axis=1).sum()),'numeric_ranges':{c:[float(D[c].min()),float(D[c].max())] for c in features if pd.api.types.is_numeric_dtype(D[c])}}
roles=[]
for c in D:
    role='candidate covariate' if c in features else ('exposure' if c=='swang1' else 'outcome / follow-up / identifier')
    roles.append({'column':c,'role':role,'type':str(D[c].dtype),'missing_n':int(D[c].isna().sum()),'legacy_action':'one-hot; missing maps to reference' if c in features and not pd.api.types.is_numeric_dtype(D[c]) else ('median impute; standardize' if c in features else 'exclude from propensity model'),'timing':'pre-exposure not established; day-1 or assessment timing needs adjudication' if c in features and c not in restricted else 'history/demographic candidate; source verification still needed','outlier_action':'retain; no unsupported deletion'})
pd.DataFrame(roles).to_csv('variable_audit.csv',index=False)
# Descriptive table: all candidate fields, observed denominators, no hypothesis tests.
table=[]
for c in features:
    for t,label in [(0,'No RHC'),(1,'RHC')]:
        v=D.loc[T==t,c]; non=v.dropna()
        if not pd.api.types.is_numeric_dtype(v):
            for level,count in non.value_counts().items():table.append({'variable':c,'group':label,'level':level,'observed_n':len(non),'missing_n':int(v.isna().sum()),'summary':f'{count} ({100*count/len(non):.1f}%)'})
        else:table.append({'variable':c,'group':label,'level':'median [Q1, Q3]','observed_n':len(non),'missing_n':int(v.isna().sum()),'summary':f'{non.median():.2f} [{non.quantile(.25):.2f}, {non.quantile(.75):.2f}]'})
pd.DataFrame(table).to_csv('table1.csv',index=False)
ess={label:float(w[T==t].sum()**2/(w[T==t]**2).sum()) for t,label in [(0,'no_rhc'),(1,'rhc')]}
evalue=lambda rr: float(max(rr,1/rr)+np.sqrt(max(rr,1/rr)*(max(rr,1/rr)-1)))
R={'analysis_status':'associational audit; causal identification not ready; no human approval','n':n,'counts':{'rhc':n1,'no_rhc':n0,'deaths_rhc':e1,'deaths_no_rhc':e0},'raw':raw,'legacy_weighted':legacy,'bootstrap':{'replicates':B,'seed':SEED,'successful':len(boots),'method':'individual nonparametric percentile; re-fit encoding, median imputation, scaling and PS each resample; conditional on chosen missing-data procedure; not multiple imputation'},'sensitivity':sens,'diagnostics':{'encoded_terms':X.shape[1],'candidate_fields':len(features),'ps_range':[float(ps.min()),float(ps.max())],'clipped_n':int(((ps<.02)|(ps>.98)).sum()),'weight_quantiles':dict(zip(['min','median','p95','p99','max'],np.quantile(w,[0,.5,.95,.99,1]).tolist())),'ess':ess,'smd_mean_before':float(bal.before.mean()),'smd_mean_after':float(bal.after.mean()),'smd_max_after':float(bal.after.max()),'smd_above_010_after':int((bal.after>.1).sum()),'fit_warnings':fit_warnings},'checks':checks,'evalue_point_only':evalue(legacy['rr']),'source_sha256':hashlib.sha256(Path('input/rhc.csv').read_bytes()).hexdigest(),'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'matplotlib':matplotlib.__version__}}
Path('results.json').write_text(json.dumps(R,indent=2,allow_nan=False))
D[['cat2','adld3p','urin1']].isna().astype(int).value_counts().rename('n').reset_index().to_csv('missingness_patterns.csv',index=False)
Path('requirements-recorded.txt').write_text('\n'.join(('scikit-learn' if k=='sklearn' else k)+'=='+v for k,v in R['versions'].items() if k!='python')+'\n')

# Common visual language, readable without reliance on color.
navy='#15324F'; teal='#007C83'; orange='#B95625'; gray='#64748B'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':navy,'text.color':navy,'axes.titleweight':'bold','figure.facecolor':'#FFFFFF','savefig.facecolor':'#FFFFFF'})
def save(name):plt.savefig('figures/'+name+'.png',dpi=165,bbox_inches='tight');plt.close()
fig,ax=plt.subplots(figsize=(10,3.5)); ax.axis('off')
boxes=[(.5,.84,f'Supplied cohort  •  {n:,} patients\nUpstream screening and exclusions unavailable'),(.5,.48,f'Analysis cohort  •  {n:,}\n0 excluded: exposure and outcome complete; IDs unique'),(.24,.10,f'No day-1 RHC  •  {n0:,}\n{e0:,} deaths / {n0:,} ({100*raw["risk_no_rhc"]:.1f}%)'),(.76,.10,f'Day-1 RHC  •  {n1:,}\n{e1:,} deaths / {n1:,} ({100*raw["risk_rhc"]:.1f}%)')]
for x,y,label in boxes:ax.text(x,y,label,ha='center',va='center',transform=ax.transAxes,bbox=dict(boxstyle='round,pad=.6',fc='#EFF6F8',ec=teal))
for xy,xytext in [((.5,.60),(.5,.72)),((.24,.24),(.5,.36)),((.76,.24),(.5,.36))]:ax.annotate('',xy=xy,xytext=xytext,xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':gray})
save('flow')
m=miss[miss.n_missing>0].sort_values('pct_missing'); fig,ax=plt.subplots(figsize=(10,4)); yy=np.arange(len(m));ax.barh(yy-.16,m.pct_no_rhc,.3,label=f'No RHC (n={n0:,})',color=navy);ax.barh(yy+.16,m.pct_rhc,.3,label=f'RHC (n={n1:,})',color=teal);ax.set(yticks=yy,yticklabels=m.variable,xlabel='Missing within exposure group (%)',xlim=(0,100));ax.legend(loc='lower right');ax.set_title('Missingness is concentrated, not negligible',loc='left');save('missingness')
fig,(ax,bx)=plt.subplots(1,2,figsize=(12,6),gridspec_kw={'width_ratios':[1.1,1]});b=bal.head(15).iloc[::-1];yy=np.arange(len(b));ax.scatter(b.before,yy,label='Before',color=gray,marker='o');ax.scatter(b.after,yy,label='Legacy weighted',color=teal,marker='D');ax.axvline(.1,ls='--',color=orange);ax.set(yticks=yy,yticklabels=b.term,xlabel='Absolute standardized mean difference');ax.legend(fontsize=9);ax.set_title('15 largest initial imbalances',loc='left');
for t,c,l in [(0,navy,'No RHC'),(1,teal,'RHC')]:bx.hist(ps[T==t],bins=np.linspace(0,1,26),density=True,histtype='step',linewidth=2,color=c,label=l)
bx.set(xlabel='Estimated propensity before clipping',ylabel='Density');bx.legend();bx.set_title('Overlap with thin tails',loc='left');fig.tight_layout();save('diagnostics')
fig,(ax,bx)=plt.subplots(1,2,figsize=(11,3.5));
for i,(label,r,c) in enumerate([('Observed',raw,navy),('Legacy weighted',legacy,teal)]):
    for a,k,scale in [(ax,'rd',100),(bx,'rr',1)]:
        ci=np.array(r[k+'_ci'])*scale;v=r[k]*scale;a.errorbar(v,i,xerr=[[v-ci[0]],[ci[1]-v]],fmt='o',color=c,capsize=5);a.text(v,i+.15,f'{v:.2f}',ha='center',fontsize=10)
for a,k,null in [(ax,'Risk difference (percentage points)',0),(bx,'Risk ratio',1)]:a.axvline(null,ls='--',color=gray);a.set(yticks=[0,1],yticklabels=['Observed','Legacy weighted'],xlabel=k,ylim=(-.4,1.5));a.grid(axis='x',alpha=.15)
fig.tight_layout();save('effects')
fig,ax=plt.subplots(figsize=(10,4));ss=sens[::-1];ax.scatter([s['rd']*100 for s in ss],range(len(ss)),s=65,color=teal);ax.axvline(raw['rd']*100,color=navy,ls=':',label='Observed RD');ax.axvline(0,color=gray,ls='--');ax.set(yticks=range(len(ss)),yticklabels=[s['specification'] for s in ss],xlabel='Risk difference (percentage points); point estimates only');ax.legend();ax.set_title('Exploratory specification sensitivity',loc='left');save('sensitivity')
print(json.dumps({k:R[k] for k in ['counts','raw','legacy_weighted','diagnostics']},indent=2))
