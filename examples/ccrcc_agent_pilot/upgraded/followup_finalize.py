#!/usr/bin/env python3
"""Finalize provenance, preservation checks and append-only sensitivity memory."""
import json,hashlib,sys,re
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0,'/Users/amiee/Projects_code/biostat-superpowers')
from biostat_workflow.memory import MemoryStore
from biostat_workflow.controller import Goal,Stage
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,default=str,allow_nan=False))
prior=json.loads(Path('followup_preservation.json').read_text());changed=[p for p,h in prior.items() if not Path(p).exists() or sha(p)!=h];assert set(changed)<= {'FOLLOWUP.md','followup_memory_retrieval.json'},changed
assert sha('followup_initial_notes.md')==prior['FOLLOWUP.md']
validation=json.loads(Path('followup_validation.json').read_text());validation.update({'figure_inspection':'Both actual PNGs inspected in session: readable axes, paired intervals, explicit VEGFA untestability and cohort labels; descriptive overlap warning present.','preservation':{'all_original_scientific_artifacts_unchanged':True,'files_checked':len(prior),'updated_existing_paths':changed,'note':'Existing followup_memory_retrieval.json refreshed for this requested session; original scientific artifacts preserved','original_note_preserved_as':'followup_initial_notes.md','report_html_sha256':sha('report.html'),'results_json_sha256':sha('results.json'),'original_figures':{p:sha(p) for p in prior if p.startswith('figures/')}},'html_checks':['Two embedded PNG data URIs; no external script, stylesheet or image loads','Required cohort, four-gene, source-status/date and limitation text present'],'scope':'Same-session numerical, source, preservation and visual checks; independent review pending'})
h=Path('followup.html').read_text();assert h.count('src="data:image/png;base64,')==2;assert '<script' not in h and '<link' not in h
for token in ['CA9','NNMT','VEGFA','MTOR','Stage I/II','NCT03849118','NCT00087022','2026-07-30']:assert token in h
save('followup_validation.json',validation)
audit=json.loads(Path('followup_controller_audit.json').read_text())
for event in audit:
 if event['route']['stage']=='analysis':event['result']['evidence']='Four cohort/layer paired t families recalculated with BH and explicit excluded/zero-variance states; final followup_results.json sha256='+sha('followup_results.json')
assert audit[-1]['result']['outcome']=='blocked' and not audit[-1]['after']['report_ready'];save('followup_controller_audit.json',audit)
ctx=json.loads(Path('runtime_context.json').read_text());original_memory=json.loads(Path('followup_memory_retrieval.json').read_text())
with MemoryStore(Path(ctx['memory']),ctx['project_id']) as m:
 before={x.item_id for x in m.inspect()}
 value={'request':'Original cohort pathological Stage I/II sensitivity; 80% finite pairs within each cohort and >=20','cohorts':{'all_stage':72,'stage_I_II':37},'tested_protein':[8054,8087],'tested_rna':[19015,18915],'shortlist':'Original directions and NDUFA4L2/MT1H selection ranks 1/2 persist descriptively; VEGFA protein n=1 untestable','source_scope':'Two actual MCP trial concepts; four details; no new annotations/literature; negative NNMT search not absence proof','limitations':'Overlapping cohorts, changed testing families/power, MNAR, purity/batch, selection bias; independent evaluation remains blocked','continuation':'FOLLOWUP.md; original continuation note preserved byte-for-byte at followup_initial_notes.md'}
 item=m.record(run_id='followup_stage',key='stage_I_II_sensitivity',value=json.dumps(value),source='followup_config.json sha256='+sha('followup_config.json')+'; followup_results.json sha256='+sha('followup_results.json')+'; context_sources.json; followup_validation.json',confirmed_by='Codex analyst same-session review, not human approval or independent evaluation',goal=Goal.INFERENTIAL,stages=(Stage.ANALYSIS,Stage.EVALUATION),input_fingerprint=ctx['input_fingerprint'])
 after=m.inspect();assert before<={x.item_id for x in after}
 save('followup_memory_append.json',{'key':'stage_I_II_sensitivity','new_records':[asdict(x) for x in after if x.item_id not in before],'original_records_retained':True,'superseded_original_decisions':False})
context=json.loads(Path('context_sources.json').read_text());context.update({'validation_sha256':sha('followup_validation.json'),'memory_append':'followup_memory_append.json','original_continuation_note':'followup_initial_notes.md','preservation':'followup_validation.json','controller':'followup_controller_audit.json'});save('context_sources.json',context)
save('followup_runtime_context.json',{'project_id':ctx['project_id'],'run_id':'followup_stage','input_fingerprint':ctx['input_fingerprint'],'memory':ctx['memory'],'controller':'followup_controller_audit.json','original_runtime_context':'runtime_context.json','review':'blocked: independent evaluation pending','decisions':'followup_memory_retrieval.json','sensitivity_decision':'followup_memory_append.json','context_sources':'context_sources.json','context_units':'bytes, not tokens'})
save('followup_output_manifest.json',{str(p):sha(p) for p in Path('.').rglob('*') if p.is_file() and (p.name.startswith('followup') or p.name in ['FOLLOWUP.md','context_sources.json'] or any(s in ('followup_tables','followup_figures') for s in p.parts)) and p.name!='followup_output_manifest.json'})
print(json.dumps({'original_files_checked':len(prior),'changed_original_paths':changed,'original_scientific_artifacts_preserved':True,'memory_appended':True,'independent_evaluation':'blocked'},indent=2))
