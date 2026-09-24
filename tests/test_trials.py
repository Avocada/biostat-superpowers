"""ClinicalTrials.gov adapter contracts; unit tests never access the network."""
import asyncio
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from biostat_mcp.core import MAX_BYTES, ServiceError, Toolkit, json_bytes, packaged_json
from biostat_mcp.trials import TrialService, download_trials, normalize

HAS_EXTRAS = all(importlib.util.find_spec(name) for name in ("mcp", "vl_convert"))


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Toolkit(Path(self.temp.name), offline=True)
        self.service = TrialService(self.store, demo=True)
        self.fixture = deepcopy(packaged_json("trials-demo.json"))

    def tearDown(self):
        self.temp.cleanup()

    def error(self, code, fn, *args, **kwargs):
        with self.assertRaises(ServiceError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def live_mock(self, fetch):
        return TrialService(Toolkit(Path(self.temp.name), fetch=Mock()), fetch=fetch)

    def test_search_query_encoded_and_filters(self):
        fetch = Mock(return_value=json_bytes({"studies": [], "totalCount": 0}))
        response = self.live_mock(fetch).search_trials("heart & lung", "A+B", "RECRUITING", "PHASE3", 7)
        params = parse_qs(urlsplit(fetch.call_args.args[0]).query)
        self.assertEqual(params['query.cond'], ['heart & lung'])
        self.assertEqual(params['query.intr'], ['A+B'])
        self.assertEqual(params['filter.advanced'], ['AREA[Phase]PHASE3'])
        self.assertEqual(params['filter.overallStatus'], ['RECRUITING'])
        self.assertEqual(params['pageSize'], ['7'])
        self.assertEqual(response['studies'], [])
        self.assertFalse(response['has_next_page'])

    def test_filter_validation_before_network(self):
        fetch = Mock()
        service = self.live_mock(fetch)
        for args in ({'status':'anything'}, {'phase':'PHASE5'}, {'page_size':0}, {'page_size':21},
                     {'page_size':True}, {'condition':'x'*201}, {'intervention':'a\nb'}):
            with self.subTest(args=args):
                self.error('invalid_request', service.search_trials, **args)
        fetch.assert_not_called()

    def test_offline_does_not_fallback_to_synthetic(self):
        fetch = Mock()
        service = TrialService(self.store, fetch=fetch)
        self.error('offline', service.search_trials, 'obesity')
        self.error('offline', service.get_trial, 'NCT00000001')
        fetch.assert_not_called()
        with self.assertRaises(ValueError):
            TrialService(Toolkit(Path(self.temp.name)), demo=True)

    def test_fixture_filters(self):
        response = self.service.search_trials('obesity', 'semaglutide', 'RECRUITING', 'PHASE3')
        self.assertEqual(len(response['studies']), 2)
        self.assertTrue(response['artifact']['synthetic'])
        self.assertIsNone(response['studies'][0]['source_url'])
        self.assertTrue(response['artifact']['source_url'].startswith('package://'))
        self.assertEqual(self.service.search_trials(phase='PHASE2')['studies'], [])

    def test_pagination_preserves_query_across_service_restart(self):
        first = self.service.search_trials('obesity', 'semaglutide', phase='PHASE3', page_size=2)
        restarted = TrialService(self.store, demo=True)
        second = restarted.next_trial_page(first['artifact']['artifact_id'])
        self.assertEqual(second['artifact']['query'], first['artifact']['query'])
        self.assertEqual(second['artifact']['page'], 2)
        self.assertEqual(second['artifact']['previous_search_id'], first['artifact']['artifact_id'])
        self.assertFalse(second['has_next_page'])
        self.assertTrue(set(s['nct_id'] for s in first['studies']).isdisjoint(s['nct_id'] for s in second['studies']))
        self.error('no_next_page', restarted.next_trial_page, second['artifact']['artifact_id'])

    def test_pagination_chain_cap(self):
        def fetch(url):
            params = parse_qs(urlsplit(url).query)
            return json_bytes({'studies': [], 'totalCount': 100, 'nextPageToken': str(int(params.get('pageToken',['0'])[0])+1)})
        service = self.live_mock(fetch)
        page = service.search_trials()
        for _ in range(9):
            page = service.next_trial_page(page['artifact']['artifact_id'])
        self.error('page_limit', service.next_trial_page, page['artifact']['artifact_id'])

    def test_bad_responses(self):
        for response in (b'bad', b'[]', b'{}', json_bytes({'studies':None}),
                         json_bytes({'studies':[{}]}), json_bytes({'studies':[], 'totalCount':-1}),
                         json_bytes({'studies':[], 'nextPageToken':123})):
            with self.subTest(response=response):
                self.error('invalid_source_response', self.live_mock(lambda _: response).search_trials)
        self.error('size_limit', self.live_mock(lambda _: b' '*(MAX_BYTES+1)).search_trials)

    def test_duplicate_and_oversized_search_page_rejected(self):
        study = self.fixture['studies'][0]
        for response, size in (({'studies':[study,study]},2), (self.fixture,1)):
            self.error('invalid_source_response', self.live_mock(lambda _: json_bytes(response)).search_trials, page_size=size)

    def test_repeated_page_token_rejected(self):
        service = self.live_mock(lambda _: json_bytes({'studies':[], 'nextPageToken':'repeat'}))
        first = service.search_trials()
        self.error('invalid_source_response', service.next_trial_page, first['artifact']['artifact_id'])

    def test_detail_missing_optional_fields_preserved_as_unknown(self):
        study = {'protocolSection': {'identificationModule': {'nctId':'NCT00000001'}}}
        item = normalize(study)
        self.assertIsNone(item['has_results'])
        self.assertIsNone(item['overall_status'])
        self.assertEqual(item['enrollment'], {})
        self.assertIsNone(item['eligibility']['eligibilityCriteria'])
        self.assertEqual(item['primary_outcomes'], [])

    def test_detail_results_and_enrollment_types(self):
        trial = self.service.get_trial('NCT00000002')
        self.assertTrue(trial['trial']['has_results'])
        self.assertEqual(trial['trial']['enrollment']['type'], 'ACTUAL')
        self.assertIn('outcomeMeasuresModule', trial['trial']['results_sections'])
        raw = json.loads(self.service.read_record(trial['artifact']['artifact_id']))
        self.assertIn('resultsSection', raw)
        self.assertEqual(len(trial['trial']['primary_outcomes']), 1)
        self.assertEqual(len(trial['trial']['locations']), 1)

    def test_bad_identifier_and_identity_mismatch(self):
        fetch = Mock(return_value=json_bytes(self.fixture['studies'][0]))
        service = self.live_mock(fetch)
        for identifier in ('../../etc', 'NCT1', 'https://example.com', 'nct00000001'):
            self.error('invalid_request', service.get_trial, identifier)
        fetch.assert_not_called()
        self.error('invalid_source_response', service.get_trial, 'NCT00000002')

    def test_malformed_modules(self):
        for key, value in (('designModule', []), ('eligibilityModule', 'text')):
            study = deepcopy(self.fixture['studies'][0]); study['protocolSection'][key] = value
            self.error('invalid_source_response', normalize, study)
        study = deepcopy(self.fixture['studies'][0]); study['hasResults'] = 'false'
        self.error('invalid_source_response', normalize, study)

    def test_snapshot_integrity(self):
        response = self.service.search_trials(page_size=2)
        path = Path(response['artifact']['local_directory']) / 'response.json'
        path.write_text('{}')
        self.error('artifact_changed', self.service.next_trial_page, response['artifact']['artifact_id'])

    def test_source_url_restriction(self):
        for url in ('http://clinicaltrials.gov/api/v2/studies', 'https://clinicaltrials.gov.evil/api/v2/studies',
                    'https://clinicaltrials.gov/api/v2/studies/../../secret', 'https://clinicaltrials.gov/api/v2/version'):
            self.error('invalid_source', download_trials, url)

    @patch('biostat_mcp.core.time.sleep')
    @patch('biostat_mcp.core.build_opener')
    def test_rate_limit_retry_and_404(self, opener, sleep):
        url = 'https://clinicaltrials.gov/api/v2/studies/NCT00000001'
        opener.return_value.open.side_effect = HTTPError(url,429,'rate limited',{},None)
        error = self.error('source_unavailable', download_trials, url)
        self.assertTrue(error.retryable)
        self.assertEqual(opener.return_value.open.call_count, 2)
        opener.return_value.open.reset_mock()
        opener.return_value.open.side_effect = HTTPError(url,404,'missing',{},None)
        self.error('not_found', download_trials, url)
        self.assertEqual(opener.return_value.open.call_count, 1)

    def test_comparison_rejects_wrong_type_empty_and_conflicting_snapshots(self):
        dataset = self.store.fetch_dataset('demo')
        self.error('wrong_artifact_type', self.service.compare_trials, [dataset['artifact_id']])
        self.error('invalid_request', self.service.compare_trials, [])
        empty = self.service.search_trials('no such condition')
        self.error('no_trials', self.service.compare_trials, [empty['artifact']['artifact_id']])
        study = deepcopy(self.fixture['studies'][0])
        service = self.live_mock(lambda _: json_bytes(study))
        first = service.get_trial('NCT00000001')
        study['protocolSection']['statusModule']['overallStatus'] = 'COMPLETED'
        second = service.get_trial('NCT00000001')
        self.error('snapshot_conflict', service.compare_trials, [first['artifact']['artifact_id'],second['artifact']['artifact_id']])

    @unittest.skipUnless(HAS_EXTRAS, 'Install .[mcp]')
    def test_comparison_deduplicates_and_labels_partial_scope(self):
        page = self.service.search_trials(page_size=2)
        detail = self.service.get_trial(page['studies'][0]['nct_id'])
        result = self.service.compare_trials([page['artifact']['artifact_id'], detail['artifact']['artifact_id']])
        self.assertEqual(result['artifact']['unique_trials'], 2)
        self.assertEqual(result['artifact']['duplicates_removed'], 1)
        self.assertEqual(sum(result['status_counts'].values()), 2)
        self.assertIn('Selected snapshots only', result['scope'])
        saved = json.loads(self.service.read_comparison(result['artifact']['artifact_id']))
        self.assertTrue(saved['inputs'][0]['has_next_page'])
        self.assertEqual(saved['inputs'][0]['total_count'], 4)
        self.assertTrue(self.store._read(result['artifact']['artifact_id'],'figure.png').startswith(b'\x89PNG'))
        spec = json.loads(self.store._read(result['artifact']['artifact_id'],'chart.vl.json'))
        self.assertIn('not all registry matches', spec['title']['subtitle'][0])

    @unittest.skipUnless(HAS_EXTRAS, 'Install .[mcp]')
    def test_csv_escapes_formula_and_keeps_canonical_text(self):
        study = deepcopy(self.fixture['studies'][0]); study['protocolSection']['identificationModule']['briefTitle'] = '=1+1'
        service = self.live_mock(lambda _: json_bytes(study))
        detail = service.get_trial('NCT00000001')
        result = service.compare_trials([detail['artifact']['artifact_id']])
        self.assertIn("'=1+1", self.store._read(result['artifact']['artifact_id'],'comparison.csv').decode())
        data = json.loads(service.read_comparison(result['artifact']['artifact_id']))
        self.assertEqual(data['studies'][0]['title'], '=1+1')


@unittest.skipUnless(HAS_EXTRAS, 'Install .[mcp]')
class TrialProtocolTests(unittest.TestCase):
    def test_full_trial_workflow_over_stdio(self):
        from biostat_mcp.trials_demo import run_demo
        with tempfile.TemporaryDirectory() as temp:
            report = asyncio.run(asyncio.wait_for(run_demo(Path(temp)), timeout=60))
            self.assertTrue({'search_trials','get_trial','next_trial_page','compare_trials'}.issubset(report['tools_discovered']))
            self.assertEqual(report['comparison']['artifact']['unique_trials'], 4)
            self.assertTrue(report['invalid_identifier_rejected'])
            self.assertEqual(report['mode'], 'synthetic')


if __name__ == '__main__':
    unittest.main()
