# Optional runtime quickstart (upgraded condition only)
Use PYTHONPATH=/Users/amiee/Projects_code/biostat-superpowers and the shared Python. No Jev. Source APIs and controller are tools, not scientific approval.
Native MCP annotate_proteins(symbols=[...]) returns bounded human UniProt matches, Ensembl mappings and Reactome annotations plus saved provenance. get_target_evidence(ensembl_id='ENSG...') returns tractability and up to10 drug/candidate rows across ALL indications. Use actual native MCP for relevant source retrieval. search_literature(provider='pubmed' or 'europepmc',query=...,page_size=3) retrieves literature. Do not send full omics matrices through the generic100-column CSV tool. Host/local statistical code analyzes matrices and makes scientific figures; MCP is an evidence interface here.
Use input/manifest.json input_fingerprint exactly as the memory scope AFTER verifying all listed hashes. Store the run/project/fingerprint in runtime_context.json, so fresh sessions do not guess it. Project ID ccrcc-pilot, goal inferential.
Memory API:
from biostat_workflow.memory import MemoryStore
from biostat_workflow.controller import Goal, Stage
with MemoryStore(Path('project-memory.sqlite3'),'ccrcc-pilot') as m:
    m.record(run_id='initial',key='cohort',value='concise verified decision and artifact pointers',source='actual source/artifact paths and hashes',confirmed_by='Codex analyst review, not human approval',goal=Goal.INFERENTIAL,stages=(Stage.ANALYSIS,Stage.EVALUATION),input_fingerprint=fingerprint)
    r=m.retrieve(goal=Goal.INFERENTIAL,stage=Stage.ANALYSIS,input_fingerprint=fingerprint,required_keys=('cohort',),max_units=8000,count=lambda text: len(text.encode("utf-8")))
    # inspect r.usable/r.issues BEFORE relying on r.text. Save selected keys, bytes and source pointers.
Keep<=6 concise decisions (cohort/scales/missingness/model/source interpretation/shortlist). Capture actual reviewed choices, not raw participant rows. Drive reusable config and validation from these decisions; memory must not merely decorate an already-finished script. No fabricated user approval. Ordinary config remains useful too.
Controller: read docs/modernization/WORKFLOW_CONTROLLER.md only for needed typed API; record real stage results/evidence. Statistical work is still host-executed. Do not mark independent evaluation ready; save blocked evaluation honestly. Preserve unresolved scientific issues on follow-up. Do not read previous example analyses. Retrieval cannot reinstate readiness automatically.
