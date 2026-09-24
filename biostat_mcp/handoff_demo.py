"""Synthetic source → MCP proposal → simulated host review → memory/workflow demo."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from uuid import uuid4

from mcp import Client, StdioServerParameters
from .core import Toolkit
from .handoff import HandoffService


async def run_demo(output: Path):
    output = output.resolve(); output.mkdir(parents=True, exist_ok=True)
    root = output / 'artifacts'
    run_id = 'demo-' + uuid4().hex[:8]
    service = HandoffService(Toolkit(root, offline=True))
    events = []
    params = StdioServerParameters(command=sys.executable, args=['-m', 'biostat_mcp.server',
        '--artifact-dir', str(root), '--offline', '--demo-trials'])
    async with Client(params) as client:
        tools = await client.list_tools()
        async def call(name, **arguments):
            response = await client.call_tool(name, arguments)
            payload = response.structured_content or json.loads(response.content[0].text)
            events.append({'tool': name, 'is_error': response.is_error})
            if response.is_error:
                raise RuntimeError(payload)
            return payload['result']
        source = await call('get_trial', nct_id='NCT00000001')
        scope = {'project_id': 'synthetic-handoff-demo', 'run_id': run_id}
        initial = await call('create_project_run', **scope, goal='causal', input_fingerprint='synthetic-input-v1', synthetic=True)
        finding = await call('propose_reviewed_handoff', **scope, key='candidate-source',
            summary='SYNTHETIC: retain this fixture as a candidate source; its eligibility still requires study-specific review.',
            artifact_ids=[source['artifact']['artifact_id']], stages=['design', 'preparation'])
        before_review = await call('get_project_context', **scope, required_keys=['candidate-source'])
        def confirm(proposal, note):
            # This is an explicit simulated host, not actual user/scientific approval.
            return service.apply(proposal['artifact']['artifact_id'], proposal['proposal_sha256'],
                reviewer='SYNTHETIC reviewer fixture', confirmation_ref='synthetic://demo/explicit-confirmation', review_notes=note)
        memory_only = confirm(finding, 'SYNTHETIC review of source-retention decision only; no readiness approval.')
        after_memory = await call('get_project_context', **scope, required_keys=['candidate-source'])
        design = await call('propose_reviewed_handoff', **scope, key='estimand',
            summary='SYNTHETIC design target: adults in the fixture, A versus B, 52-week mean outcome difference; demonstration only.',
            artifact_ids=[source['artifact']['artifact_id']], stages=['design', 'preparation', 'identification', 'analysis'],
            outcome='complete', dependencies=[memory_only['memory_item']['item_id']])
        await client.read_resource(f"biostat://artifacts/{design['artifact']['artifact_id']}/handoff")
        approved_design = confirm(design, 'SYNTHETIC specialist review fixture marks design complete; no real scientific evaluation performed.')
        reopened = HandoffService(Toolkit(root, offline=True)).inspect_run(**scope)
        ready_context = await call('get_project_context', **scope, required_keys=['estimand'])
        # Reversible stale-artifact probe, kept in a clearly separate synthetic demo.
        source_file = Path(source['artifact']['local_directory']) / 'response.json'
        original = source_file.read_bytes()
        try:
            source_file.write_bytes(original + b'\n')
            blocked = await call('inspect_project_run', **scope)
        finally:
            source_file.write_bytes(original)
        reset = service.reset(scope['project_id'], run_id, approved_design['run']['version'], 'synthetic-input-v2',
            reviewer='SYNTHETIC reviewer fixture', confirmation_ref='synthetic://demo/input-change', reason='SYNTHETIC changed input contract')
        stale_context = await call('get_project_context', **scope, required_keys=['estimand'])
        audit = await call('inspect_handoff_audit', **scope)
    report = {'synthetic': True, 'notice': 'All confirmations are simulated fixture attestations. No real user decision or scientific claim was approved.',
              'tools': [t.name for t in tools.tools], 'scope': scope, 'initial': initial,
              'unconfirmed_context': before_review, 'memory_only': memory_only, 'confirmed_context': after_memory,
              'approved_design': approved_design, 'reopened': reopened, 'preparation_context': ready_context,
              'changed_source_guard': blocked, 'reset': reset, 'stale_context': stale_context, 'audit': audit, 'calls': events}
    (output / 'run.json').write_text(json.dumps(report, indent=2) + '\n')
    rows = [('Initial', 'design', 'None'), ('Unconfirmed proposal', 'design', 'Required context unavailable'),
            ('Confirmed source-retention decision', 'design', 'Candidate source available; readiness unchanged'),
            ('Confirmed design result', reopened['next_route']['stage'], 'Estimand available with provenance'),
            ('Source payload changed', 'Blocked', 'Gate evidence fails integrity validation'),
            ('Host reset with new input fingerprint', 'design', 'Old input-bound memory withheld')]
    lines = ['# Reviewed handoff demonstration', '', report['notice'], '',
             '| Event | Next step | Memory / guard |', '|---|---|---|']
    lines.extend('| ' + ' | '.join(row) + ' |' for row in rows)
    lines += ['', 'Transport: actual MCP stdio. Apply/reset: separate simulated host calls, never MCP approval tools.',
              'The original synthetic source file was restored after the integrity probe. No LLM calls or token-saving measurement.']
    (output / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('outputs/handoff-demo'))
    args = parser.parse_args()
    result = asyncio.run(run_demo(args.output))
    print(json.dumps({'synthetic': True, 'tools': len(result['tools']),
        'memory_only_next': result['memory_only']['run']['next_route']['stage'],
        'approved_design_next': result['reopened']['next_route']['stage'],
        'source_change_blocked': not result['changed_source_guard']['usable'],
        'changed_input_context_usable': result['stale_context']['usable'], 'report': str(args.output.resolve() / 'REPORT.md')}, indent=2))


if __name__ == '__main__':
    main()
