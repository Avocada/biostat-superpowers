#!/usr/bin/env python3
"""Paired RHC reproduction plus runtime audit; not an autonomous-agent benchmark."""
import argparse
import asyncio
import contextlib
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import runpy
import sys
import time
import warnings
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from mcp import Client, StdioServerParameters
from biostat_workflow.controller import Goal, Stage, WorkflowState, Result, Outcome, advance, route
from biostat_workflow.memory import MemoryStore


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def reproduce(script, data, folder):
    folder.mkdir(parents=True)
    reader = pd.read_csv
    def frozen_read(source, *args, **kwargs):
        if source != 'https://hbiostat.org/data/repo/rhc.csv':
            raise ValueError('Unexpected original-script input')
        return reader(data, *args, **kwargs)
    stream = io.StringIO()
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught, patch.object(pd, 'read_csv', frozen_read), contextlib.redirect_stdout(stream):
        warnings.simplefilter('always')
        scope = runpy.run_path(str(script))
    elapsed = time.perf_counter() - start
    (folder / 'stdout.txt').write_text(stream.getvalue())
    metrics = {k: float(scope[k]) for k in ['rr_naive','rr_iptw','rd_iptw','or_naive','or_adj','smd_before','smd_after','evalue']}
    metrics.update(n=len(scope['y']), treated=int(scope['t'].sum()), events=int(scope['y'].sum()),
                   compute_seconds=elapsed, timing_notice='Ordered same-process execution; imports/warm-up and workflow overhead differ. Not a speed benchmark.', warnings=[str(w.message) for w in caught])
    save(folder / 'metrics.json', metrics)
    return scope, metrics


def iptw(frame, clip=.02):
    t = (frame.swang1 == 'RHC').to_numpy(dtype=int)
    y = (frame.dth30 == 'Yes').to_numpy(dtype=int)
    drop = ['swang1','death','dth30','t3d30','dthdte','lstctdte','dschdte','sadmdte','ptid']
    x = pd.get_dummies(frame.drop(columns=drop), drop_first=True, dummy_na=False)
    x = x.apply(pd.to_numeric, errors='coerce').fillna(x.median(numeric_only=True)).fillna(0)
    xs = StandardScaler().fit_transform(x)
    raw = LogisticRegression(max_iter=5000, C=1.0).fit(xs, t).predict_proba(xs)[:,1]
    ps = np.clip(raw, clip, 1-clip) if clip else raw
    if np.any((ps <= 0) | (ps >= 1)):
        raise ValueError('Propensity reached zero or one')
    weights = np.where(t, t.mean()/ps, (1-t.mean())/(1-ps))
    r1, r0 = [np.average(y[t==a], weights=weights[t==a]) for a in (1,0)]
    return np.array([r1/r0, r1-r0]), raw


async def sources(output):
    calls = []
    params = StdioServerParameters(command=sys.executable, args=['-m','biostat_mcp.server','--artifact-dir',str(output/'mcp_artifacts')])
    async with Client(params) as client:
        discovered = await client.list_tools()
        async def call(name, **args):
            start = time.perf_counter()
            response = await client.call_tool(name, args)
            body = response.structured_content or json.loads(response.content[0].text)
            calls.append({'tool':name, 'arguments':args, 'seconds':time.perf_counter()-start, 'is_error':response.is_error})
            if response.is_error:
                raise RuntimeError(body)
            return body['result']
        original = await call('get_article', provider='pubmed', article_id='8782638')
        sensitivity = await call('get_article', provider='pubmed', article_id='28693043')
        refs = await call('build_reference_list', artifact_ids=[original['artifact']['artifact_id'],sensitivity['artifact']['artifact_id']])
    report = {'transport':'actual MCP stdio', 'tools_discovered':len(discovered.tools), 'calls':calls,
              'original_study':original, 'evalue_method':sensitivity, 'references':refs}
    save(output/'mcp.json', report)
    return report


def workflow(output, data, profile):
    fingerprint = sha(data)
    state = WorkflowState(Goal.CAUSAL)
    transitions = []
    def step(result):
        nonlocal state
        before = state
        selected = route(state)
        state = advance(state, result)
        transitions.append({'before':asdict(before),'route':asdict(selected),'result':asdict(result),'after':asdict(state)})
    step(Result(Outcome.COMPLETE, 'protocol.md: target contrast specified; identification remains unverified.'))
    step(Result(Outcome.COMPLETE, 'data_profile.json: public input validated; substantial missingness explicitly requires specialist handling.', missing_data_required=True))
    step(Result(Outcome.BLOCKED, 'adld3p and urin1 have substantial missingness; inherited single imputation is not an approved primary causal strategy. Requires missing-data review and identification timing evidence.'))
    save(output/'workflow.json', {'transitions':transitions,'checkpoint':asdict(state),
         'next_route':asdict(route(state)), 'notice':'Causal workflow is blocked before estimation, not successfully completed. Paired script runs are separate exploratory reproductions.'})
    database = output/'project-memory.sqlite3'
    records = {
        'estimand':f'Target: 30-day mortality risk difference and risk ratio for day-1 RHC versus no day-1 RHC among the {profile["n"]} SUPPORT patients. Causal identification is unresolved.',
        'data_contract':f'Frozen input SHA256={fingerprint}; n={profile["n"]}; one row per patient; exposure and outcome labels validated. See data_profile.json.',
        'readiness':'Exploratory reproduction only. Do not promote the old median-imputation calculation to a causal result. Missing-data and within-day treatment/covariate timing remain unresolved.'}
    with MemoryStore(database,'rhc-comparison') as memory:
        for key,value in records.items():
            memory.record(run_id='modernized',key=key,value=value,source=str(output/'protocol.md' if key=='estimand' else output/'workflow.json'),
                          confirmed_by='Codex analyst: recorded analysis scope and checked facts; not human scientific approval',
                          goal=Goal.CAUSAL,stages=(Stage.MISSING_DATA,Stage.IDENTIFICATION,Stage.EVALUATION),input_fingerprint=fingerprint)
    with MemoryStore(database,'rhc-comparison') as memory:
        args=dict(goal=Goal.CAUSAL,stage=Stage.MISSING_DATA,required_keys=tuple(records),max_units=12000,count=lambda s:len(s.encode()))
        recalled = memory.retrieve(input_fingerprint=fingerprint,**args)
        stale = memory.retrieve(input_fingerprint='different-input',**args)
    assert recalled.usable and not stale.usable
    save(output/'memory_check.json',{'reopened_usable':recalled.usable,'context_bytes':recalled.units,'records':[r.context_record() for r in recalled.items],
                                   'changed_input_usable':stale.usable,'changed_input_issues':stale.issues,
                                   'notice':'Actual SQLite retrieval, not token savings. No host-reviewed MCP handoff or human approval was fabricated.'})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--bootstrap',type=int,default=500)
    args=p.parse_args()
    if args.bootstrap < 200:
        p.error('Use at least 200 bootstrap resamples for this exploratory interval')
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    script=Path(__file__).resolve().parents[1]/'demo/rhc_causal.py'
    data=args.data.resolve()
    frame=pd.read_csv(data)
    frame=frame.drop(columns=[c for c in frame if c.lower().startswith('unnamed')])
    assert frame.ptid.is_unique and frame.ptid.notna().all()
    assert set(frame.swang1.unique())=={'RHC','No RHC'}
    assert set(frame.dth30.unique())=={'Yes','No'}
    profile={'n':len(frame),'columns':len(frame.columns),'patient_id_unique':True,'missing_counts':frame.isna().sum().loc[lambda x:x>0].to_dict(),
             'treatment_counts':frame.swang1.value_counts().to_dict(),'outcome_counts':frame.dth30.value_counts().to_dict(),
             'row_exclusions':0, 'source':'https://hbiostat.org/data/repo/rhc.csv','input_sha256':sha(data)}
    save(output/'data_profile.json',profile)
    protocol='''# Paired RHC protocol

Target: day-1 RHC versus no day-1 RHC, 30-day mortality, SUPPORT cohort, marginal risk difference and risk ratio; conditional adjusted odds ratio reported separately. This is an observational association reproduction, not an identified treatment effect.

A: execute the original script unchanged, substituting only frozen local bytes for its fixed download URL. B: execute that same script afresh, with identical input/environment, accompanied by actual controller state, memory retrieval, MCP source retrieval, and additional diagnostic calculations. No new agent/model is invoked by this script. No claim of an autonomous model benchmark or token savings is supported.

Preserve the inherited adjustment set, single imputation and 0.02 propensity clipping so method changes do not confound the paired point-estimate comparison. Clipping changes probabilities, not patient inclusion. Conditional logistic OR is not marginal g-computation. Do not use effect direction to select specifications.

Additional diagnostics: fixed preweighting pooled-SD SMD denominator, maximum and count above 0.1, group ESS, raw propensity quantiles and clipped counts. Exploratory percentile bootstrap resamples independent patient rows, refits encoding/median imputation/scaling/propensity model, and recalculates marginal IPTW RR/RD. It characterizes the inherited estimator under patient independence; it does not repair single-imputation bias or establish MAR, causal identification or appropriate cluster handling. Record failures and convergence warnings. Sensitivity clips: none, 0.01, 0.02, 0.05, retaining all patients.

Causal readiness requires resolving substantial missingness and whether day-1 covariates precede RHC. Baseline status alone is not a DAG justification. Record the block; exploratory reproduction must not set analysis/evaluation/report readiness to true. MCP sources are references, not approvals. No human review is implied.
'''
    (output/'protocol.md').write_text(protocol)
    workflow(output,data,profile)
    mcp=asyncio.run(sources(output))
    with threadpool_limits(limits=1):
        _,a=reproduce(script,data,output/'baseline')
        scope,b=reproduce(script,data,output/'modernized')
        for key in ['rr_iptw','rd_iptw','or_adj','smd_after']:
            assert np.isclose(a[key],b[key],rtol=0,atol=1e-12)
        x,t,y,w=scope['Xs'],scope['t'],scope['y'],scope['w']
        denominator=np.sqrt((x[t==1].var(axis=0)+x[t==0].var(axis=0))/2)
        before=np.divide(abs(x[t==1].mean(axis=0)-x[t==0].mean(axis=0)),denominator,out=np.zeros(x.shape[1]),where=denominator>0)
        after=np.divide(abs(np.average(x[t==1],weights=w[t==1],axis=0)-np.average(x[t==0],weights=w[t==0],axis=0)),denominator,out=np.zeros(x.shape[1]),where=denominator>0)
        balance=pd.DataFrame({'covariate':scope['X'].columns,'abs_smd_before':before,'abs_smd_after':after}).sort_values('abs_smd_after',ascending=False)
        balance.to_csv(output/'balance.csv',index=False)
        estimate,raw=iptw(frame)
        assert np.allclose(estimate,[a['rr_iptw'],a['rd_iptw']],rtol=0,atol=1e-10)
        sensitivity=[]
        for clip in [0,.01,.02,.05]:
            point,_=iptw(frame,clip)
            sensitivity.append({'clip':clip,'rr':float(point[0]),'rd':float(point[1]),'n':len(frame)})
        rng=np.random.default_rng(20260924)
        boot=[]; failures=[]; convergence=[]
        start=time.perf_counter()
        for i in range(args.bootstrap):
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    point,_=iptw(frame.iloc[rng.integers(0,len(frame),len(frame))])
                if not np.isfinite(point).all(): raise ValueError('non-finite estimate')
                if caught:
                    convergence.extend({'replicate':i,'warning':str(w.message)} for w in caught)
                if any(issubclass(w.category, ConvergenceWarning) for w in caught):
                    raise RuntimeError('Propensity fit did not converge; excluded from bootstrap interval')
                boot.append(point)
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as exc:
                failures.append({'replicate':i,'error':str(exc)})
            if (i+1)%100==0: print(f'Bootstrap {i+1}/{args.bootstrap}',flush=True)
        pd.DataFrame(boot,columns=['rr','rd']).to_csv(output/'bootstrap.csv',index=False)
        save(output/'bootstrap_status.json', {'attempted':args.bootstrap,'successful':len(boot),'failures':failures,'warnings':convergence})
        if len(boot)<.95*args.bootstrap: raise RuntimeError('More than 5% resampling failures; see bootstrap_status.json and partial bootstrap.csv before reporting intervals')
        intervals=np.quantile(boot,[.025,.975],axis=0)
        diag={'max_abs_smd_after':float(after.max()),'count_smd_above_0_1':int((after>.1).sum()),
              'mean_abs_smd_fixed_denominator':float(after.mean()),'clipped_by_arm':{str(k):int(((raw<.02)|(raw>.98))[t==k].sum()) for k in [0,1]},
              'ess_by_arm':{str(k):float(w[t==k].sum()**2/(w[t==k]**2).sum()) for k in [0,1]},
              'propensity_quantiles_by_arm':{str(k):np.quantile(raw[t==k],[0,.01,.5,.99,1]).tolist() for k in [0,1]},
              'weight_quantiles':np.quantile(w,[0,.5,.95,.99,1]).tolist(), 'sensitivity':sensitivity,
              'bootstrap':{'attempted':args.bootstrap,'successful':len(boot),'failures':failures,'warnings':convergence,'seed':20260924,'compute_seconds':time.perf_counter()-start,
                           'rr_percentile_95':intervals[:,0].tolist(),'rd_percentile_95':intervals[:,1].tolist(),
                           'interpretation':'Exploratory interval for inherited single-imputation estimator; not a validated causal interval.'}}
    save(output/'diagnostics.json',diag)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(12,6),layout='constrained')
    for group,label in [(0,'No RHC'),(1,'RHC')]: ax[0].hist(raw[t==group],bins=30,alpha=.55,density=True,label=label)
    ax[0].set(xlabel='Raw estimated propensity for RHC',ylabel='Density',title='Overlap before clipping'); ax[0].legend()
    top=balance.head(15).iloc[::-1]
    ax[1].scatter(top.abs_smd_before,np.arange(len(top)),label='Before')
    ax[1].scatter(top.abs_smd_after,np.arange(len(top)),label='After IPTW')
    ax[1].set_yticks(np.arange(len(top)),top.covariate)
    ax[1].axvline(.1,color='gray',linestyle='--'); ax[1].set(xlabel='Absolute SMD (fixed denominator)',title='15 largest residual imbalances'); ax[1].legend()
    fig.suptitle('RHC: diagnostics of the reproduced estimator — exploratory')
    fig.savefig(output/'diagnostics.png',dpi=180); plt.close(fig)
    metadata={'created_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':sha(data),'original_script_sha256':sha(script),
              'runner_sha256':sha(__file__),'python':sys.version,'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scikit-learn','statsmodels','matplotlib','mcp','biostat-superpowers-runtime']},
              'runtime_import':__import__('biostat_workflow').__file__,'baseline':a,'modernized':b,
              'causal_readiness':'blocked at missing_data; timing/identification also unresolved',
              'jev':'not installed or used','llm_tokens':None,'llm_cost':None,'historical_model_run_comparison':False}
    save(output/'comparison.json',metadata)
    print(json.dumps({'output':str(output),'rr':a['rr_iptw'],'rd':a['rd_iptw'],'diagnostics':diag},indent=2))


if __name__=='__main__':
    main()
