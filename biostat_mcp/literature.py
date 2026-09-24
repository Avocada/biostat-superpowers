"""Bounded PubMed/Europe PMC retrieval and identifier-based reference lists."""
from collections import defaultdict
import csv
from datetime import datetime, timezone
from html.parser import HTMLParser
import io
import json
import re
import threading
import time
from urllib.parse import urlencode, urlsplit
from xml.etree import ElementTree as ET

from .core import MAX_BYTES, ServiceError, Toolkit, digest, download_bounded, json_bytes

PUBMED = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
EPMC = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
NOTICE = 'Retrieved citations and abstracts are unreviewed source material; trial-ID mentions are not verified study links.'
RIGHTS = 'Abstracts may be copyrighted. No full-text articles are downloaded. https://www.ncbi.nlm.nih.gov/About/disclaimer.html'
_LOCK = threading.Lock()
_LAST = {}


def bad(message):
    return ServiceError('invalid_source_response', message)


def throttle(host):
    with _LOCK:
        delay = (0.36 if host == 'eutils.ncbi.nlm.nih.gov' else 0.2) - (time.monotonic() - _LAST.get(host, 0))
        if delay > 0:
            time.sleep(delay)
        _LAST[host] = time.monotonic()


def download_literature(url):
    p = urlsplit(url)
    allowed = ((p.netloc == 'eutils.ncbi.nlm.nih.gov' and p.path in
                ('/entrez/eutils/esearch.fcgi', '/entrez/eutils/efetch.fcgi')) or
               (p.netloc == 'www.ebi.ac.uk' and p.path == '/europepmc/webservices/rest/search'))
    if p.scheme != 'https' or not allowed or p.fragment:
        raise ServiceError('invalid_source', 'Only the configured PubMed/Europe PMC endpoints are allowed')
    return download_bounded(url, 'Literature provider', before_request=lambda: throttle(p.netloc))


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {'p', 'br', 'h1', 'h2', 'h3', 'h4', 'li'}:
            self.parts.append('\n')


def plain(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise bad('Expected source text')
    parser = PlainText(); parser.feed(value)
    return ''.join(parser.parts).strip() or None


def text(element):
    return ''.join(element.itertext()).strip() if element is not None else None


def doi(value):
    if not value:
        return None
    if not isinstance(value, str):
        raise bad('DOI must be text')
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value.strip(), flags=re.I).lower()
    return value if re.fullmatch(r'10\.\d{4,9}/\S+', value) else None


def normalize_pmcid(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise bad('PMCID must be text')
    return value.upper() if re.fullmatch(r'PMC[0-9]+', value, flags=re.I) else None


def mentions(*values):
    return sorted({value.upper() for value in re.findall(r'\bNCT\d{8}\b', ' '.join(v or '' for v in values), flags=re.I)})


def parse_pubmed(raw):
    if len(raw) > MAX_BYTES:
        raise ServiceError('size_limit', 'PubMed response exceeds 5 MiB')
    # Normal PubMed XML has an external DOCTYPE. ElementTree does not fetch it;
    # explicitly forbid entity declarations, including non-UTF8 bypasses.
    try:
        xml = raw.decode('utf-8')
        if '\x00' in xml or '<!ENTITY' in xml.upper():
            raise ValueError('entity declaration or unsupported encoding')
        root = ET.fromstring(xml)
    except (UnicodeError, ValueError, ET.ParseError) as exc:
        raise bad('Unsupported PubMed XML') from exc
    if root.tag != 'PubmedArticleSet' or root.find('.//ERROR') is not None:
        raise bad('PubMed did not return an article set')
    result = []
    for entry in root:
        if entry.tag == 'PubmedArticle':
            citation = entry.find('MedlineCitation'); article = entry.find('MedlineCitation/Article')
        elif entry.tag == 'PubmedBookArticle':
            citation = entry.find('BookDocument'); article = citation
        else:
            raise bad('Unsupported PubMed record type')
        if citation is None or article is None:
            raise bad('Missing PubMed citation')
        pmid = text(citation.find('PMID'))
        if not pmid or not re.fullmatch(r'[1-9]\d{0,8}', pmid):
            raise bad('Invalid PMID in source')
        id_path = 'PubmedData/ArticleIdList/ArticleId' if entry.tag == 'PubmedArticle' else 'PubmedBookData/ArticleIdList/ArticleId'
        ids = {node.get('IdType'): text(node) for node in entry.findall(id_path)}
        abstract = [{'label': n.get('Label'), 'text': text(n)} for n in article.findall('Abstract/AbstractText')]
        title = text(article.find('ArticleTitle')) or text(article.find('Book/BookTitle'))
        authors = [text(a.find('CollectiveName')) or ' '.join(filter(None, [text(a.find('LastName')), text(a.find('ForeName'))]))
                   for a in article.findall('AuthorList/Author')]
        pubdate = article.find('Journal/JournalIssue/PubDate')
        if pubdate is None:
            pubdate = article.find('Book/PubDate')
        date = ' '.join(text(child) or '' for child in pubdate) if pubdate is not None else None
        relations = [{'type': n.get('RefType'), 'pmid': text(n.find('PMID')), 'citation': text(n.find('RefSource'))}
                     for n in citation.findall('CommentsCorrectionsList/CommentsCorrections')]
        types = [text(n) for n in article.findall('PublicationTypeList/PublicationType')]
        trial_fields = [text(n) for n in article.findall('DataBankList/DataBank/AccessionNumberList/AccessionNumber')]
        result.append({'provider': 'pubmed', 'source': 'MED', 'id': pmid, 'pmid': pmid,
                       'pmcid': normalize_pmcid(ids.get('pmc')), 'doi': doi(ids.get('doi') or text(article.find("ELocationID[@EIdType='doi']"))),
                       'title': title, 'authors': authors, 'journal': text(article.find('Journal/Title')) or text(article.find('Book/BookTitle')),
                       'publication_date': date, 'publication_types': types, 'abstract_sections': abstract,
                       'is_open_access': None, 'is_retracted': True if 'Retracted Publication' in types or any(r['type']=='RetractionIn' for r in relations) else None,
                       'corrections': relations, 'trial_id_mentions': mentions(title, *[a['text'] for a in abstract], *trial_fields),
                       'copyright': text(article.find('Abstract/CopyrightInformation')), 'license': None,
                       'source_url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'})
    if len({a['id'] for a in result}) != len(result):
        raise bad('Duplicate PMID in source response')
    return result


def normalize_epmc(item):
    if not isinstance(item, dict):
        raise bad('Europe PMC article must be an object')
    identifier, source = item.get('id'), item.get('source')
    if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', identifier) or not isinstance(source, str) or not re.fullmatch(r'[A-Z]{2,6}', source):
        raise bad('Invalid Europe PMC source/ID')
    pmid = item.get('pmid') or (identifier if source == 'MED' else None)
    if pmid is not None and (not isinstance(pmid, str) or not re.fullmatch(r'[1-9]\d{0,8}', pmid)):
        raise bad('Invalid Europe PMC PMID')
    if source == 'MED' and pmid != identifier:
        raise bad('Europe PMC MED ID does not match PMID')
    authors = item.get('authorList', {}).get('author', [])
    types = item.get('pubTypeList', {}).get('pubType', [])
    if not isinstance(authors, list) or any(not isinstance(a, dict) for a in authors) or not isinstance(types, list) or any(not isinstance(t,str) for t in types):
        raise bad('Unsupported author/publication type list')
    abstract = plain(item.get('abstractText'))
    title = plain(item.get('title'))
    journal_info = item.get('journalInfo', {})
    return {'provider': 'europepmc', 'source': source, 'id': identifier, 'pmid': pmid,
            'pmcid': normalize_pmcid(item.get('pmcid')), 'doi': doi(item.get('doi')), 'title': title,
            'authors': [a.get('fullName') or a.get('collectiveName') for a in authors] or ([plain(item.get('authorString'))] if item.get('authorString') else []),
            'journal': journal_info.get('journal', {}).get('title'),
            'publication_date': item.get('firstPublicationDate') or item.get('pubYear'),
            'publication_types': types, 'abstract_sections': [{'label': None, 'text': abstract}] if abstract else [],
            'is_open_access': {'Y': True, 'N': False}.get(item.get('isOpenAccess')),
            'is_retracted': {'Y': True, 'N': False}.get(item.get('isRetracted')),
            'corrections': item.get('commentCorrectionList', {}),
            'trial_id_mentions': mentions(title, abstract), 'copyright': item.get('copyright'), 'license': item.get('license'),
            'source_url': f'https://europepmc.org/article/{source}/{identifier}'}


def compact(article):
    return {k: article[k] for k in ('provider','source','id','pmid','pmcid','doi','title','publication_date',
                                    'publication_types','is_retracted','trial_id_mentions','source_url')}


class LiteratureService:
    def __init__(self, store: Toolkit, *, fetch=download_literature, demo=False):
        if demo and not store.offline:
            raise ValueError('Synthetic literature mode requires offline=True')
        self.store, self.fetch, self.demo = store, fetch, demo

    def _request(self, url, payloads, requests, filename):
        if self.demo:
            from .literature_fixture import response
            raw = response(url)
        elif self.store.offline:
            raise ServiceError('offline', 'Literature network retrieval is disabled')
        else:
            raw = self.fetch(url)
        if len(raw) > MAX_BYTES:
            raise ServiceError('size_limit', 'Literature response exceeds 5 MiB; reduce page_size')
        payloads[filename] = raw
        requests.append({'url': 'package://biostat_mcp/data/literature-demo.json' if self.demo else url,
                         'retrieved_at': datetime.now(timezone.utc).isoformat(), 'sha256': digest(raw), 'file': filename})
        return raw

    def _json(self, raw):
        try:
            body = json.loads(raw)
            if not isinstance(body, dict):
                raise ValueError('not object')
            return body
        except (ValueError, UnicodeError) as exc:
            raise bad('Invalid provider JSON') from exc

    def _epmc(self, query, size, cursor, payloads, requests):
        url = EPMC + '?' + urlencode({'query':query,'format':'json','resultType':'core','pageSize':size,'cursorMark':cursor})
        body = self._json(self._request(url,payloads,requests,'response.json'))
        try:
            total = body['hitCount']; items = body['resultList']['result']
            if type(total) is not int or total < 0 or not isinstance(items,list) or len(items)>size:
                raise ValueError('count or result list')
            records = [normalize_epmc(a) for a in items]
            token = body.get('nextCursorMark')
            if token is not None and (not isinstance(token,str) or len(token)>8192):
                raise ValueError('cursor')
            if len({(a['source'],a['id']) for a in records}) != len(records) or total < len(records):
                raise ValueError('duplicate or count mismatch')
            return records, total, token, {'source_query':body.get('request',{}).get('queryString',query)}
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            raise bad('Unsupported Europe PMC response') from exc

    def _pubmed_records(self, ids, payloads, requests):
        if not ids:
            return []
        url = PUBMED+'efetch.fcgi?'+urlencode({'db':'pubmed','id':','.join(ids),'retmode':'xml','tool':'biostat_superpowers'})
        records = parse_pubmed(self._request(url,payloads,requests,'records.xml'))
        by_id = {a['id']:a for a in records}
        if len(ids) == 1 and not records:
            raise ServiceError('not_found', 'No PubMed record returned for this PMID')
        if set(by_id) != set(ids):
            raise bad('PubMed returned missing or unexpected identifiers')
        return [by_id[i] for i in ids]

    def _pubmed(self, query, size, offset, payloads, requests):
        url = PUBMED+'esearch.fcgi?'+urlencode({'db':'pubmed','term':query,'retmode':'json','retmax':size,'retstart':offset,'sort':'relevance','tool':'biostat_superpowers'})
        body = self._json(self._request(url,payloads,requests,'search.json'))
        try:
            b = body['esearchresult']; ids=b['idlist']; total=int(b['count'])
            if b.get('ERROR') or b.get('errorlist') or body.get('error'):
                raise ValueError('source query error')
            if not isinstance(ids,list) or len(ids)>size or len(set(ids))!=len(ids) or any(not isinstance(i,str) or not re.fullmatch(r'[1-9]\d{0,8}',i) for i in ids) or total<len(ids):
                raise ValueError('invalid IDs')
            records = self._pubmed_records(ids,payloads,requests)
            next_offset = offset+len(ids)
            next_token = next_offset if ids and next_offset<min(total,10000) else None
            return records,total,next_token,{'source_query':b.get('querytranslation'), 'warnings':b.get('warninglist')}
        except (KeyError, TypeError, ValueError) as exc:
            raise bad('Unsupported PubMed search response') from exc

    def search_literature(self, provider, query, page_size=10):
        if provider not in {'pubmed','europepmc'}:
            raise ServiceError('invalid_request','Provider must be pubmed or europepmc')
        if not isinstance(query,str) or not query.strip() or len(query)>500 or any(ord(c)<32 for c in query):
            raise ServiceError('invalid_request','Query must be 1–500 characters without control characters')
        if type(page_size) is not int or not 1<=page_size<=20:
            raise ServiceError('invalid_request','page_size must be 1–20')
        return self._search(provider,query.strip(),page_size,0 if provider=='pubmed' else '*')

    def _search(self,provider,query,size,cursor,page=1,previous=None,seen=None):
        payloads, requests = {}, []
        if provider=='pubmed':
            records,total,token,extra = self._pubmed(query,size,cursor,payloads,requests)
        else:
            records,total,token,extra = self._epmc(query,size,cursor,payloads,requests)
            if token==cursor or not records:
                token=None
        seen = list(seen or [])+[cursor]
        if token is not None and token in seen:
            raise bad('Provider pagination cursor cycle')
        saved={'provider':provider,'query':query,'page_size':size,'page':page,'next_cursor':token,
               'seen_cursors':seen,'total_count':total,'records':records,**extra}
        artifact=self._save('literature_search',saved,payloads,requests,
                            previous_search_id=previous,page=page,query=query,total_count=total,has_next_page=token is not None)
        return {'artifact':artifact,'articles':[compact(a) for a in saved['records']],
                'has_next_page':token is not None,'scope':'One search page; source totals and ranking may change.', 'notice':NOTICE}

    def _save(self,kind,saved,payloads,requests,**extra):
        if self.demo:
            for article in saved['records']:
                article['source_url']=None
        payloads['literature.json']=json_bytes(saved)
        return self.store._save(kind,payloads,{'provider':saved['provider'],'synthetic':self.demo,'requests':requests,
                                             'returned_count':len(saved['records']),'rights':RIGHTS,**extra})

    def _load(self,identifier):
        manifest=self.store._manifest(identifier)
        if manifest['kind'] not in {'literature_search','literature_article'}:
            raise ServiceError('wrong_artifact_type','Expected a literature search or article snapshot')
        for request in manifest['requests']:
            self.store._read(identifier,request['file'])
        saved=self._json(self.store._read(identifier,'literature.json'))
        return manifest,saved

    def next_literature_page(self,search_artifact_id):
        manifest,saved=self._load(search_artifact_id)
        if manifest['kind']!='literature_search':
            raise ServiceError('wrong_artifact_type','Expected a literature search')
        if manifest['synthetic']!=self.demo:
            raise ServiceError('invalid_request','Pagination source mode must match the snapshot')
        if saved['next_cursor'] is None:
            raise ServiceError('no_next_page','No further page in this search snapshot')
        if saved['page']>=10:
            raise ServiceError('page_limit','At most 10 pages per chain; narrow the search')
        return self._search(saved['provider'],saved['query'],saved['page_size'],saved['next_cursor'],
                            saved['page']+1,search_artifact_id,saved['seen_cursors'])

    def get_article(self,provider,article_id,source='MED'):
        if provider not in {'pubmed','europepmc'} or not isinstance(source,str) or not re.fullmatch(r'[A-Z]{2,6}',source):
            raise ServiceError('invalid_request','Invalid provider or source code')
        pattern=r'[1-9]\d{0,8}' if provider=='pubmed' or source=='MED' else r'[A-Za-z0-9_.-]{1,64}'
        if not isinstance(article_id,str) or not re.fullmatch(pattern,article_id) or (provider=='pubmed' and source!='MED'):
            raise ServiceError('invalid_request','Supply a valid provider article ID; PubMed uses numeric PMID and MED source')
        payloads,requests={},[]
        if provider=='pubmed':
            records=self._pubmed_records([article_id],payloads,requests)
        else:
            records,_,_,_=self._epmc(f'EXT_ID:{article_id} AND SRC:{source}',2,'*',payloads,requests)
            if not records:
                raise ServiceError('not_found','Article not found in Europe PMC')
            if len(records)!=1 or records[0]['id']!=article_id or records[0]['source']!=source:
                raise bad('Article identity mismatch')
        saved={'provider':provider,'records':records}
        artifact=self._save('literature_article',saved,payloads,requests)
        return {'artifact':artifact,'article':saved['records'][0],
                'record_uri':f"biostat://artifacts/{artifact['artifact_id']}/literature",'notice':NOTICE,'rights':RIGHTS}

    def read_record(self,identifier):
        self._load(identifier)
        return self.store._read(identifier,'literature.json').decode()

    def build_reference_list(self,artifact_ids):
        if not isinstance(artifact_ids,list) or not 1<=len(artifact_ids)<=10:
            raise ServiceError('invalid_request','Supply 1–10 saved literature artifacts')
        records,inputs,modes=[],[],set()
        for identifier in dict.fromkeys(artifact_ids):
            manifest,saved=self._load(identifier); modes.add(manifest['synthetic'])
            inputs.append({'artifact_id':identifier,'provider':manifest['provider'],'requests':manifest['requests'],
                           'query':saved.get('query'),'page':saved.get('page'),'total_count':saved.get('total_count')})
            for record in saved['records']:
                records.append({'artifact_id':identifier,**record})
        if len(modes)>1:
            raise ServiceError('invalid_request','Do not combine synthetic and live records')
        if not records or len(records)>200:
            raise ServiceError('size_limit','Reference lists require 1–200 source records')
        parents=list(range(len(records))); aliases={}
        def find(i):
            while parents[i]!=i:
                parents[i]=parents[parents[i]];i=parents[i]
            return i
        for i,r in enumerate(records):
            keys=[f"native:{r['provider']}:{r['source']}:{r['id']}"]
            keys += [f'{k}:{str(r[k]).lower()}' for k in ('pmid','pmcid','doi') if r[k]]
            for key in keys:
                if key in aliases: parents[find(i)]=find(aliases[key])
                aliases[key]=i
        groups=defaultdict(list)
        for i,r in enumerate(records): groups[find(i)].append(r)
        references=[]
        for variants in groups.values():
            pmids={r['pmid'] for r in variants if r['pmid']}
            if len(pmids)>1:
                raise ServiceError('identifier_conflict','Shared DOI/PMCID connects different PMIDs; review source records before merging')
            differences={key:sorted({json.dumps(r[key],ensure_ascii=False,sort_keys=True) for r in variants})
                         for key in ('title','doi','publication_date','is_retracted','publication_types')}
            references.append({'identifiers':{k:sorted({r[k] for r in variants if r[k]}) for k in ('pmid','pmcid','doi')},
                               'title':variants[0]['title'],'source_records':variants,
                               'metadata_differences':{k:v for k,v in differences.items() if len(v)>1},
                               'trial_id_mentions':sorted({n for r in variants for n in r['trial_id_mentions']})})
        summary={'references':references,'inputs':inputs,'input_records':len(records),'unique_references':len(references),
                 'duplicates_grouped':len(records)-len(references),'synthetic':True in modes,
                 'scope':'Selected source snapshots only; identifier matching, no fuzzy title matching or systematic-review completeness claim.',
                 'notice':NOTICE,'rights':RIGHTS}
        out=io.StringIO(newline='');writer=csv.writer(out)
        writer.writerow(['title','pmids','pmcids','dois','providers','trial_id_mentions','metadata_differences'])
        lines=['# Literature reference list','','SYNTHETIC FIXTURE' if True in modes else 'PubMed / Europe PMC snapshots','',
               f"{len(records)} source records grouped into {len(references)} references.",'',summary['scope'],'',NOTICE,'',RIGHTS,'',
               '| Reference | Title | Sources | Trial-ID mentions |','|---|---|---|---|']
        def safe(cell):
            return "'"+cell if cell.lstrip().startswith(('=','+','-','@')) else cell
        def md(cell):
            return str(cell or 'Not reported').replace('&','&amp;').replace('<','&lt;').replace('|','&#124;').replace('\n',' ')
        for i,r in enumerate(references,1):
            ids=r['identifiers']; providers=sorted({s['provider'] for s in r['source_records']})
            writer.writerow([safe(r['title'] or ''),'; '.join(ids['pmid']),'; '.join(ids['pmcid']),'; '.join(ids['doi']),
                             '; '.join(providers),'; '.join(r['trial_id_mentions']),json.dumps(r['metadata_differences'],ensure_ascii=False)])
            links=[]
            for source_record in r['source_records']:
                label=f"{source_record['provider']}:{source_record['source']}:{source_record['id']}"
                link=f"[{label}]({source_record['source_url']})" if source_record['source_url'] else label
                if link not in links:links.append(link)
            lines.append(f"| {i} | {md(r['title'])} | {'; '.join(links)} | {md(', '.join(r['trial_id_mentions']))} |")
        artifact=self.store._save('literature_references',{'references.json':json_bytes(summary),'references.csv':out.getvalue().encode(),
                                  'references.md':('\n'.join(lines)+'\n').encode()},
                                  {'inputs':inputs,'synthetic':True in modes,'input_records':len(records),'unique_references':len(references),
                                   'duplicates_grouped':len(records)-len(references),'rights':RIGHTS})
        return {'artifact':artifact,'unique_references':len(references),'duplicates_grouped':len(records)-len(references),
                'reference_uri':f"biostat://artifacts/{artifact['artifact_id']}/references",'notice':NOTICE}

    def read_references(self,identifier):
        if self.store._manifest(identifier)['kind']!='literature_references':
            raise ServiceError('wrong_artifact_type','Expected a reference list')
        return self.store._read(identifier,'references.json').decode()
