"""Reviewed handoff contracts, persistence and actual MCP proposal/context flow."""
import asyncio
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from biostat_mcp.core import ServiceError, Toolkit
from biostat_mcp.handoff import HandoffService
from biostat_mcp.trials import TrialService
from biostat_workflow.controller import Goal, Stage
from biostat_workflow.memory import MemoryStore

HAS_MCP = importlib.util.find_spec('mcp') is not None


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifacts = Toolkit(self.root, offline=True)
        self.service = HandoffService(self.artifacts)
        self.source = TrialService(self.artifacts, demo=True).get_trial('NCT00000001')['artifact']
        self.scope = {'project_id': 'project-a', 'run_id': 'run-a'}
        self.service.create_run(**self.scope, goal='causal', input_fingerprint='input-v1', synthetic=True)

    def tearDown(self):
        self.temp.cleanup()

    def error(self, code, fn, *args, **kwargs):
        with self.assertRaises(ServiceError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def proposal(self, **changes):
        arguments = dict(**self.scope, key='estimand', summary='SYNTHETIC reviewed target',
                         artifact_ids=[self.source['artifact_id']], stages=['design', 'preparation', 'analysis'])
        arguments.update(changes)
        return self.service.propose(**arguments)

    def apply(self, proposal, **changes):
        arguments = dict(reviewer='Synthetic reviewer', confirmation_ref='synthetic://confirmation', review_notes='Synthetic completed review')
        arguments.update(changes)
        return self.service.apply(proposal['artifact']['artifact_id'], proposal['proposal_sha256'], **arguments)

    def items(self):
        with MemoryStore(self.service.db_path, self.scope['project_id']) as memory:
            return memory.inspect()

    def test_proposal_cannot_write_memory_or_readiness(self):
        proposal = self.proposal(outcome='complete')
        self.assertEqual(self.items(), ())
        run = self.service.inspect_run(**self.scope)
        self.assertEqual(run['version'], 0)
        self.assertFalse(run['state']['estimand_ready'])
        self.assertEqual(proposal['proposal']['review_skill'], 'study-design-and-power')
        context = self.service.context(**self.scope, required_keys=['estimand'])
        self.assertFalse(context['usable'])
        self.assertEqual(context['records'], [])

    def test_memory_only_does_not_advance(self):
        result = self.apply(self.proposal())
        self.assertFalse(result['run']['state']['estimand_ready'])
        self.assertEqual(result['run']['next_route']['stage'], 'design')
        context = self.service.context(**self.scope, required_keys=['estimand'])
        self.assertTrue(context['usable'])
        self.assertEqual(len(context['records']), 1)
        self.assertIn('confirmation', context['records'][0]['confirmed_by'])

    def test_workflow_result_persists_after_reopen(self):
        applied = self.apply(self.proposal(outcome='complete'))
        service = HandoffService(Toolkit(self.root, offline=True))
        run = service.inspect_run(**self.scope)
        self.assertEqual(run['version'], 1)
        self.assertTrue(run['state']['estimand_ready'])
        self.assertEqual(run['next_route']['stage'], 'preparation')
        audit = service.audit(**self.scope)
        self.assertEqual(audit['events'][0]['memory_item_id'], applied['memory_item']['item_id'])
        self.assertEqual(audit['events'][0]['review']['proposal_sha256'], json.loads(applied['memory_item']['source'])['proposal_sha256'])

    def test_blank_confirmation_or_wrong_digest_rejected(self):
        proposal = self.proposal(outcome='complete')
        self.error('invalid_request', self.apply, proposal, confirmation_ref='')
        self.error('invalid_request', self.apply, proposal, review_notes='')
        self.error('proposal_changed', self.service.apply, proposal['artifact']['artifact_id'], '0'*64,
                   reviewer='reviewer', confirmation_ref='ref', review_notes='notes')
        self.assertEqual(self.items(), ())

    def test_duplicate_apply_and_stale_competing_proposal(self):
        first = self.proposal(outcome='complete')
        second = self.proposal(key='other', outcome='complete')
        self.apply(first)
        self.error('stale_proposal', self.apply, first)
        self.error('stale_proposal', self.apply, second)
        self.assertEqual(len(self.items()), 1)
        self.assertEqual(len(self.service.audit(**self.scope)['events']), 1)

    def test_atomic_rollback_after_event_insert(self):
        proposal = self.proposal(outcome='complete')
        with patch.object(self.service, '_write_run', side_effect=RuntimeError('simulated disk/host failure')):
            with self.assertRaises(RuntimeError):
                self.apply(proposal)
        self.assertEqual(self.items(), ())
        self.assertEqual(self.service.audit(**self.scope)['events'], [])
        self.assertEqual(self.service.inspect_run(**self.scope)['version'], 0)
        self.apply(proposal)  # Failed attempt did not consume the proposal.

    def test_cross_project_and_input_reuse(self):
        self.apply(self.proposal())
        self.service.create_run('project-b', 'run-a', 'causal', 'input-v1', True)
        context = self.service.context('project-b', 'run-a', ['estimand'])
        self.assertFalse(context['usable'])
        self.service.create_run('project-a', 'same-input', 'causal', 'input-v1', True)
        self.assertTrue(self.service.context('project-a', 'same-input', ['estimand'])['usable'])
        self.service.create_run('project-a', 'new-input', 'causal', 'input-v2', True)
        self.assertFalse(self.service.context('project-a', 'new-input', ['estimand'])['usable'])
        self.assertFalse(self.service.inspect_run('project-a', 'same-input')['state']['estimand_ready'])

    def test_no_workflow_gate_skipping_or_inapplicable_rating(self):
        self.error('invalid_transition', self.proposal, outcome='complete', evaluation='ready')
        self.apply(self.proposal(outcome='complete'))
        self.error('invalid_transition', self.proposal, key='data', outcome='complete')
        prepared = self.apply(self.proposal(key='data', outcome='complete', missing_data_required=False))
        self.assertEqual(prepared['run']['next_route']['stage'], 'identification')
        self.error('invalid_transition', self.proposal, outcome='revise', revision_target='analysis')

    def test_review_correction_invalidates_gate_only_with_revision(self):
        old = self.apply(self.proposal(outcome='complete'))['memory_item']
        correction = self.proposal(summary='Corrected synthetic target', supersedes=old['item_id'])
        self.error('evidence_unavailable', self.apply, correction)
        self.assertEqual(self.items()[0].status, 'active')
        revision = self.proposal(summary='Corrected synthetic target', supersedes=old['item_id'],
                                 outcome='revise', revision_target='design')
        result = self.apply(revision)
        self.assertFalse(result['run']['state']['estimand_ready'])
        self.assertEqual(result['run']['next_route']['stage'], 'design')
        self.assertEqual(self.items()[0].status, 'superseded')
        self.assertEqual(result['run']['state']['revision_count'], 1)

    def test_conflicting_value_fails_atomic_apply(self):
        self.apply(self.proposal())
        conflicting = self.proposal(summary='Conflicting target without supersession')
        self.error('evidence_unavailable', self.apply, conflicting)
        self.assertEqual(len(self.items()), 1)
        self.assertTrue(self.service.context(**self.scope, required_keys=['estimand'])['usable'])

    def test_source_change_before_and_after_review_blocks(self):
        pending = self.proposal(outcome='complete')
        path = Path(self.source['local_directory']) / 'response.json'
        original = path.read_bytes()
        path.write_bytes(original + b'\n')
        self.error('artifact_changed', self.apply, pending)
        self.assertEqual(self.items(), ())
        path.write_bytes(original)
        self.apply(pending)
        path.write_bytes(original + b'\n')
        run = self.service.inspect_run(**self.scope)
        self.assertFalse(run['usable'])
        self.assertIsNone(run['next_route'])
        self.error('artifact_changed', self.service.context, **self.scope)

    def test_manifest_changes_are_detected(self):
        pending = self.proposal()
        path = Path(self.source['local_directory']) / 'manifest.json'
        manifest = json.loads(path.read_text()); manifest['provider'] = 'changed provider'
        path.write_text(json.dumps(manifest))
        self.error('artifact_changed', self.apply, pending)

    def test_transitive_source_payload_is_bound(self):
        from biostat_mcp.literature import LiteratureService
        literature = LiteratureService(self.artifacts, demo=True)
        article = literature.get_article('pubmed', '90000001')['artifact']
        reference = literature.build_reference_list([article['artifact_id']])['artifact']
        proposal = self.proposal(artifact_ids=[reference['artifact_id']])
        self.assertEqual(len(proposal['proposal']['sources']), 2)
        (Path(article['local_directory']) / 'records.xml').write_text('changed upstream')
        self.error('artifact_changed', self.apply, proposal)

    def test_deleted_gate_memory_blocks_reuse(self):
        item = self.apply(self.proposal(outcome='complete'))['memory_item']
        with MemoryStore(self.service.db_path, 'project-a') as memory:
            memory.delete(item['item_id'])
        self.assertFalse(self.service.inspect_run(**self.scope)['usable'])
        self.error('evidence_unavailable', self.service.context, **self.scope)

    def test_source_changed_memory_only_is_excluded_without_marking_gate_ready(self):
        self.apply(self.proposal())
        (Path(self.source['local_directory']) / 'response.json').write_text('changed')
        context = self.service.context(**self.scope, required_keys=['estimand'])
        self.assertFalse(context['usable'])
        self.assertEqual(context['records'], [])
        self.assertEqual(len(context['excluded_item_ids']), 1)
        self.assertTrue(self.service.inspect_run(**self.scope)['usable'])

    def test_host_reset_changes_input_and_clears_all_gates(self):
        self.apply(self.proposal(outcome='complete'))
        self.error('stale_proposal', self.service.reset, 'project-a', 'run-a', 0, 'input-v2',
                   reviewer='r', confirmation_ref='c', reason='changed')
        run = self.service.reset('project-a', 'run-a', 1, 'input-v2', reviewer='r', confirmation_ref='c', reason='changed')
        self.assertEqual(run['version'], 2)
        self.assertFalse(run['state']['estimand_ready'])
        self.assertEqual(run['next_route']['stage'], 'design')
        self.assertFalse(self.service.context(**self.scope, required_keys=['estimand'])['usable'])
        self.assertEqual(self.service.audit(**self.scope)['events'][-1]['action'], 'host_reset')

    def test_synthetic_sources_cannot_enter_live_run(self):
        self.service.create_run('project-a', 'live', 'causal', 'input-v1', False)
        self.error('invalid_request', self.proposal, run_id='live')

    def test_context_budget_is_explicit_and_required_key_not_truncated(self):
        self.apply(self.proposal())
        context = self.service.context(**self.scope, required_keys=['estimand'], max_bytes=1)
        self.assertFalse(context['usable'])
        self.assertEqual(context['records'], [])
        self.assertIn('estimand', context['omitted_keys'])
        self.assertEqual(context['unit'], 'UTF-8 bytes, not tokens')

    def test_fabricated_memory_record_cannot_self_approve(self):
        proposal = self.proposal()
        with MemoryStore(self.service.db_path, 'project-a') as memory:
            memory.record(run_id='run-a', key='estimand', value=proposal['proposal']['summary'],
                source=json.dumps({'handoff_id': proposal['artifact']['artifact_id'], 'proposal_sha256': proposal['proposal_sha256']}),
                confirmed_by='unverified arbitrary label', goal=Goal.CAUSAL, stages=(Stage.DESIGN,), input_fingerprint='input-v1')
        context = self.service.context(**self.scope, required_keys=['estimand'])
        self.assertFalse(context['usable'])
        self.assertEqual(context['records'], [])

    def test_no_progress_and_fatal_policies_still_apply(self):
        for i in range(3):
            result = self.apply(self.proposal(key=f'blocked-{i}', outcome='blocked'))
        self.assertEqual(result['run']['state']['stop_reason'], 'no_progress_threshold')
        self.error('invalid_transition', self.proposal, key='further', outcome='complete')
        self.service.create_run('project-a', 'fatal', 'causal', 'input-v1', True)
        result = self.apply(self.proposal(run_id='fatal', key='fatal', outcome='fatal'))
        self.assertEqual(result['run']['state']['stop_reason'], 'fatal_flaw_human_escalation')

    def test_full_causal_lifecycle_requires_ready_review(self):
        for stage in ('design', 'preparation', 'missing_data', 'identification', 'analysis', 'evaluation', 'reporting'):
            current = self.service.inspect_run(**self.scope)
            self.assertEqual(current['next_route']['stage'], stage)
            fields = {'key': stage, 'outcome': 'complete', 'stages': [stage]}
            if stage == 'preparation':
                fields['missing_data_required'] = True
            if stage == 'evaluation':
                self.error('invalid_transition', self.proposal, **fields, evaluation='conditionally_ready')
                fields['evaluation'] = 'ready'
            final = self.apply(self.proposal(**fields))
        self.assertEqual(final['run']['state']['stop_reason'], 'success_ready')
        self.assertEqual(final['run']['state']['iteration_count'], 7)
        self.assertEqual(len(self.service.audit(**self.scope)['events']), 7)

    def test_host_cli_inspect_and_synthetic_apply(self):
        proposal = self.proposal()
        command = [sys.executable, '-m', 'biostat_mcp.handoff', '--artifact-dir', str(self.root)]
        inspected = subprocess.run(command + ['inspect', proposal['artifact']['artifact_id']],
                                   capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(inspected.stdout)['proposal_sha256'], proposal['proposal_sha256'])
        applied = subprocess.run(command + ['apply', proposal['artifact']['artifact_id'],
            '--accept-digest', proposal['proposal_sha256'], '--reviewer', 'SYNTHETIC CLI fixture',
            '--confirmation-ref', 'synthetic://test/confirmation', '--review-notes', 'Synthetic host CLI test'],
            capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(applied.stdout)['run']['next_route']['stage'], 'design')
        self.assertEqual(len(self.items()), 1)

    def test_existing_memory_exclusion_propagates_to_dependents(self):
        with MemoryStore(self.service.db_path, 'other-project') as memory:
            args = dict(run_id='r', value='v', source='s', confirmed_by='c', goal=Goal.CAUSAL, stages=(Stage.DESIGN,))
            parent = memory.record(key='parent', **args)
            child = memory.record(key='child', dependencies=(parent.item_id,), **args)
            result = memory.retrieve(goal=Goal.CAUSAL, stage=Stage.DESIGN, input_fingerprint='data',
                required_keys=('child',), max_units=10000, count=len, excluded_ids=(parent.item_id,))
            self.assertFalse(result.usable)
            self.assertNotIn(child, result.items)


@unittest.skipUnless(HAS_MCP, 'Install .[mcp]')
class HandoffProtocolTests(unittest.TestCase):
    def test_full_synthetic_handoff_and_no_mcp_approval_tool(self):
        from biostat_mcp.handoff_demo import run_demo
        with tempfile.TemporaryDirectory() as temp:
            result = asyncio.run(asyncio.wait_for(run_demo(Path(temp)), timeout=60))
            self.assertTrue({'create_project_run', 'propose_reviewed_handoff', 'get_project_context',
                             'inspect_project_run', 'inspect_handoff_audit'}.issubset(result['tools']))
            self.assertFalse(any(name in {'apply', 'apply_handoff', 'approve_handoff', 'reset'} for name in result['tools']))
            self.assertFalse(result['unconfirmed_context']['usable'])
            self.assertEqual(result['memory_only']['run']['next_route']['stage'], 'design')
            self.assertEqual(result['reopened']['next_route']['stage'], 'preparation')
            self.assertFalse(result['changed_source_guard']['usable'])
            self.assertFalse(result['stale_context']['usable'])


if __name__ == '__main__':
    unittest.main()
