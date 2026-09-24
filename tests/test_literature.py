"""Offline provider contracts and actual MCP transport tests."""
import asyncio
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from biostat_mcp.core import MAX_BYTES, ServiceError, Toolkit, json_bytes, packaged_json
from biostat_mcp.literature import (EPMC, PUBMED, LiteratureService, download_literature,
                                    normalize_epmc, parse_pubmed, throttle)
from biostat_mcp.literature_fixture import response

HAS_EXTRAS=all(importlib.util.find_spec(x) for x in ('mcp','vl_convert'))


class LiteratureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Toolkit(Path(self.temp.name),offline=True)
        self.service=LiteratureService(self.store,demo=True)

    def tearDown(self):self.temp.cleanup()

    def error(self,code,fn,*args,**kwargs):
        with self.assertRaises(ServiceError) as caught:fn(*args,**kwargs)
        self.assertEqual(caught.exception.code,code)

    def live(self,fetch):return LiteratureService(Toolkit(Path(self.temp.name)),fetch=fetch)

    def test_offline_and_explicit_fixture_mode(self):
        fetch=Mock();service=LiteratureService(self.store,fetch=fetch)
        self.error('offline',service.search_literature,'pubmed','test')
        fetch.assert_not_called()
        with self.assertRaises(ValueError):LiteratureService(Toolkit(Path(self.temp.name)),demo=True)
        result=self.service.search_literature('pubmed','NCT00000001')
        self.assertTrue(result['artifact']['synthetic'])
        self.assertIsNone(result['articles'][0]['source_url'])
        self.assertTrue(result['artifact']['requests'][0]['url'].startswith('package://'))

    def test_validation_before_requests(self):
        fetch=Mock();service=self.live(fetch)
        for provider,query,size in [('other','test',10),('pubmed','',10),('europepmc','x'*501,10),('pubmed','a\nb',1),('pubmed','a',21),('pubmed','a',True)]:
            self.error('invalid_request',service.search_literature,provider,query,size)
        for provider,identifier,source in [('pubmed','../a','MED'),('europepmc','bad:OR:x','MED'),('pubmed','1','PPR'),('europepmc','PPR1','bad query')]:
            self.error('invalid_request',service.get_article,provider,identifier,source)
        fetch.assert_not_called()

    def test_provider_queries_and_pagination_survive_restart(self):
        for provider in ('pubmed','europepmc'):
            with self.subTest(provider=provider):
                first=self.service.search_literature(provider,'NCT00000001',2)
                service=LiteratureService(self.store,demo=True)
                second=service.next_literature_page(first['artifact']['artifact_id'])
                self.assertEqual(second['artifact']['page'],2)
                self.assertEqual(second['artifact']['query'],'NCT00000001')
                self.assertEqual(len(second['articles']),1)
                self.assertFalse(second['has_next_page'])
                self.error('no_next_page',service.next_literature_page,second['artifact']['artifact_id'])

    def test_epmc_query_encoding(self):
        fetch=Mock(return_value=json_bytes({'hitCount':0,'resultList':{'result':[]}}))
        self.live(fetch).search_literature('europepmc','TITLE:"a+b" AND x & y',7)
        params=parse_qs(urlsplit(fetch.call_args.args[0]).query)
        self.assertEqual(params['query'],['TITLE:"a+b" AND x & y'])
        self.assertEqual(params['resultType'],['core'])
        self.assertEqual(params['pageSize'],['7'])

    def test_pubmed_batched_fetch_and_source_order(self):
        calls=[]
        def fetch(url):
            calls.append(url)
            if 'esearch.fcgi' in url:
                return json_bytes({'esearchresult':{'count':'2','idlist':['90000002','90000001'],'querytranslation':'expanded query'}})
            return response(url)
        result=self.live(fetch).search_literature('pubmed','NCT00000001',2)
        self.assertEqual([a['id'] for a in result['articles']],['90000002','90000001'])
        self.assertEqual(len(calls),2)
        saved=json.loads(self.live(fetch).read_record(result['artifact']['artifact_id']))
        self.assertEqual(saved['source_query'],'expanded query')
        self.assertEqual(len(result['artifact']['requests']),2)

    def test_pubmed_xml_labels_collective_authors_corrections(self):
        raw=b'''<!DOCTYPE PubmedArticleSet SYSTEM "https://example.invalid/no-fetch.dtd"><PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>A <i>trial</i></ArticleTitle><Abstract><AbstractText Label="RESULTS">Mention nct00000001.</AbstractText><CopyrightInformation>Rights retained</CopyrightInformation></Abstract><AuthorList><Author><CollectiveName>Study Group</CollectiveName></Author></AuthorList><PublicationTypeList><PublicationType>Retracted Publication</PublicationType></PublicationTypeList></Article><CommentsCorrectionsList><CommentsCorrections RefType="RetractionIn"><PMID>456</PMID></CommentsCorrections></CommentsCorrectionsList></MedlineCitation></PubmedArticle></PubmedArticleSet>'''
        article=parse_pubmed(raw)[0]
        self.assertEqual(article['title'],'A trial')
        self.assertEqual(article['abstract_sections'][0]['label'],'RESULTS')
        self.assertEqual(article['authors'],['Study Group'])
        self.assertEqual(article['trial_id_mentions'],['NCT00000001'])
        self.assertTrue(article['is_retracted'])
        self.assertEqual(article['corrections'][0]['pmid'],'456')
        self.assertEqual(article['copyright'],'Rights retained')

    def test_pubmed_primary_identifiers_not_cited_reference_ids(self):
        raw=b'<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>Primary</ArticleTitle></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.9999/primary</ArticleId><ArticleId IdType="pmc">PMC123</ArticleId></ArticleIdList><ReferenceList><Reference><ArticleIdList><ArticleId IdType="doi">10.9999/cited</ArticleId><ArticleId IdType="pmc">PMC456</ArticleId></ArticleIdList></Reference></ReferenceList></PubmedData></PubmedArticle></PubmedArticleSet>'
        article=parse_pubmed(raw)[0]
        self.assertEqual(article['doi'],'10.9999/primary')
        self.assertEqual(article['pmcid'],'PMC123')

    def test_epmc_mismatched_ids_rejected(self):
        self.error('invalid_source_response',normalize_epmc,{'source':'MED','id':'123','pmid':'456'})
        self.error('invalid_source_response',normalize_epmc,{'source':'MED','id':'123','pmcid':[]})

    def test_missing_abstract_and_retraction_unknown(self):
        raw=b'<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>No abstract</ArticleTitle></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'
        item=parse_pubmed(raw)[0]
        self.assertEqual(item['abstract_sections'],[])
        self.assertIsNone(item['is_retracted'])
        self.assertIsNone(item['is_open_access'])

    def test_books_and_entity_rejection(self):
        book=b'<PubmedArticleSet><PubmedBookArticle><BookDocument><PMID>123</PMID><Book><BookTitle>Example book</BookTitle></Book></BookDocument></PubmedBookArticle></PubmedArticleSet>'
        self.assertEqual(parse_pubmed(book)[0]['title'],'Example book')
        for raw in (b'<html/>',b'not xml',b'<!DOCTYPE x [<!ENTITY a "xx">]><PubmedArticleSet/>', '<PubmedArticleSet/>'.encode('utf-16')):
            self.error('invalid_source_response',parse_pubmed,raw)

    def test_preprint_and_epmc_markup(self):
        article=self.service.get_article('europepmc','PPRdemo1','PPR')['article']
        self.assertIn('Preprint',article['publication_types'])
        self.assertIsNone(article['pmid'])
        item=normalize_epmc({'id':'123','source':'MED','abstractText':'<h4>Methods</h4><p>A &amp; B</p>'})
        self.assertIn('A & B',item['abstract_sections'][0]['text'])
        self.assertNotIn('<',item['abstract_sections'][0]['text'])

    def test_malformed_provider_responses(self):
        for provider,raw in [('pubmed',b'{}'),('pubmed',json_bytes({'esearchresult':{'count':'1','idlist':['oops']}})),
                             ('pubmed',json_bytes({'esearchresult':{'count':'0','idlist':[],'errorlist':{'FieldNotFound':['xx']}}})),
                             ('europepmc',b'[]'),('europepmc',b'{}'),('europepmc',json_bytes({'hitCount':1,'resultList':{'result':[{'id':'123','source':'MED','authorList':None}]}}))]:
            self.error('invalid_source_response',self.live(lambda _:raw).search_literature,provider,'query')
        self.error('size_limit',self.live(lambda _:b' '*(MAX_BYTES+1)).search_literature,'pubmed','x')

    def test_epmc_exhausted_cursor_is_not_a_failure(self):
        raw=json_bytes({'hitCount':0,'resultList':{'result':[]},'nextCursorMark':'*'})
        result=self.live(lambda _:raw).search_literature('europepmc','query')
        self.assertFalse(result['has_next_page'])

    def test_pagination_cap_and_cursor_cycle(self):
        record=packaged_json('literature-demo.json')['europepmc'][0]
        def fetch(url):
            cursor=parse_qs(urlsplit(url).query)['cursorMark'][0]
            token='1' if cursor=='*' else str(int(cursor)+1)
            return json_bytes({'hitCount':100,'resultList':{'result':[record]},'nextCursorMark':token})
        service=self.live(fetch); page=service.search_literature('europepmc','query',1)
        for _ in range(9):page=service.next_literature_page(page['artifact']['artifact_id'])
        self.error('page_limit',service.next_literature_page,page['artifact']['artifact_id'])
        fetch=Mock(side_effect=[json_bytes({'hitCount':100,'resultList':{'result':[record]},'nextCursorMark':'a'}),
                               json_bytes({'hitCount':100,'resultList':{'result':[record]},'nextCursorMark':'*'})])
        service=self.live(fetch);page=service.search_literature('europepmc','query',1)
        self.error('invalid_source_response',service.next_literature_page,page['artifact']['artifact_id'])

    def test_missing_and_mismatched_article_identity(self):
        self.error('not_found',self.service.get_article,'pubmed','99999999')
        self.error('not_found',self.service.get_article,'europepmc','99999999')
        raw=json_bytes({'hitCount':1,'resultList':{'result':[{'id':'123','source':'MED'}]}})
        self.error('invalid_source_response',self.live(lambda _:raw).get_article,'europepmc','456')

    def test_snapshot_integrity(self):
        page=self.service.search_literature('pubmed','NCT00000001',2)
        (Path(page['artifact']['local_directory'])/'records.xml').write_text('changed')
        self.error('artifact_changed',self.service.next_literature_page,page['artifact']['artifact_id'])

    def test_network_boundary(self):
        for url in ('file:///etc/passwd','https://eutils.ncbi.nlm.nih.gov.evil/entrez/eutils/esearch.fcgi',
                    'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1/fullTextXML'):
            self.error('invalid_source',download_literature,url)

    @patch('biostat_mcp.literature.time.sleep')
    @patch('biostat_mcp.literature.time.monotonic',side_effect=[100,100,100,100.36])
    @patch.dict('biostat_mcp.literature._LAST',{},clear=True)
    def test_pubmed_requests_are_throttled(self,clock,sleep):
        throttle('eutils.ncbi.nlm.nih.gov');throttle('eutils.ncbi.nlm.nih.gov')
        sleep.assert_called_once_with(0.36)

    def test_dedup_preserves_both_sources_and_metadata_differences(self):
        first=self.service.get_article('pubmed','90000001')
        second=self.service.get_article('europepmc','90000001')
        result=self.service.build_reference_list([first['artifact']['artifact_id'],second['artifact']['artifact_id']])
        self.assertEqual(result['unique_references'],1)
        self.assertEqual(result['duplicates_grouped'],1)
        reference=json.loads(self.service.read_references(result['artifact']['artifact_id']))['references'][0]
        self.assertEqual(len(reference['source_records']),2)
        self.assertIn('publication_date',reference['metadata_differences'])
        self.assertEqual(reference['identifiers']['doi'],['10.9999/synthetic-1'])

    def test_title_only_not_merged_and_conflicting_pmids_rejected(self):
        record={'id':'123','source':'MED','title':'Same title'}
        service=self.live(lambda _:json_bytes({'hitCount':1,'resultList':{'result':[record]}}))
        first=service.get_article('europepmc','123');record['id']='456';second=service.get_article('europepmc','456')
        result=service.build_reference_list([first['artifact']['artifact_id'],second['artifact']['artifact_id']])
        self.assertEqual(result['unique_references'],2)
        record['doi']='10.9999/shared';third=service.get_article('europepmc','456')
        record['id']='123';fourth=service.get_article('europepmc','123')
        self.error('identifier_conflict',service.build_reference_list,[third['artifact']['artifact_id'],fourth['artifact']['artifact_id']])

    def test_wrong_kind_empty_and_mixed_source_modes(self):
        data=self.store.fetch_dataset('demo')
        self.error('wrong_artifact_type',self.service.build_reference_list,[data['artifact_id']])
        self.error('invalid_request',self.service.build_reference_list,[])
        first=self.service.get_article('pubmed','90000001')
        second=self.live(response).get_article('pubmed','90000001')
        self.error('invalid_request',self.service.build_reference_list,[first['artifact']['artifact_id'],second['artifact']['artifact_id']])


@unittest.skipUnless(HAS_EXTRAS,'Install .[mcp]')
class LiteratureProtocolTests(unittest.TestCase):
    def test_trial_literature_workflow_over_stdio(self):
        from biostat_mcp.literature_demo import run_demo
        with tempfile.TemporaryDirectory() as temp:
            report=asyncio.run(asyncio.wait_for(run_demo(Path(temp)),timeout=60))
            self.assertTrue({'search_literature','get_article','next_literature_page','build_reference_list'}.issubset(report['tools_discovered']))
            self.assertEqual(report['references']['unique_references'],4)
            self.assertEqual(report['references']['duplicates_grouped'],4)
            self.assertTrue(report['invalid_identifier_rejected'])


if __name__=='__main__':unittest.main()
