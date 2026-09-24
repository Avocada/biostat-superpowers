"""Explicit synthetic responses for protocol demos; never a network fallback."""
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree as ET

from .core import json_bytes, packaged_json


def response(url):
    p=urlsplit(url); q={k:v[0] for k,v in parse_qs(p.query).items()}
    data=packaged_json('literature-demo.json')
    if p.netloc=='eutils.ncbi.nlm.nih.gov':
        records=data['pubmed']
        if p.path.endswith('esearch.fcgi'):
            records=[r for r in records if q['term'].lower() in (r['title']+' '+r['abstract']).lower()]
            start,size=int(q['retstart']),int(q['retmax'])
            return json_bytes({'syntheticFixtureNotice':'Synthetic records, not PubMed data',
                              'esearchresult':{'count':str(len(records)),'idlist':[r['id'] for r in records[start:start+size]],'querytranslation':q['term']}})
        root=ET.Element('PubmedArticleSet')
        root.append(ET.Comment('Synthetic test records, not retrieved from PubMed'))
        for record in records:
            if record['id'] not in q['id'].split(','):continue
            item=ET.SubElement(root,'PubmedArticle');cite=ET.SubElement(item,'MedlineCitation')
            ET.SubElement(cite,'PMID').text=record['id'];article=ET.SubElement(cite,'Article')
            ET.SubElement(article,'ArticleTitle').text=record['title']
            journal=ET.SubElement(article,'Journal');ET.SubElement(journal,'Title').text='Synthetic journal'
            issue=ET.SubElement(journal,'JournalIssue');date=ET.SubElement(issue,'PubDate');ET.SubElement(date,'Year').text='2026'
            authors=ET.SubElement(article,'AuthorList');author=ET.SubElement(authors,'Author');ET.SubElement(author,'CollectiveName').text='Synthetic research group'
            abstract=ET.SubElement(article,'Abstract');ET.SubElement(abstract,'AbstractText',Label='BACKGROUND').text=record['abstract']
            types=ET.SubElement(article,'PublicationTypeList');ET.SubElement(types,'PublicationType').text='Journal Article'
            ids=ET.SubElement(ET.SubElement(item,'PubmedData'),'ArticleIdList')
            ET.SubElement(ids,'ArticleId',IdType='doi').text=record['doi']
        return ET.tostring(root,encoding='utf-8')
    records=data['europepmc'];query=q['query']
    if query.startswith('EXT_ID:'):
        identifier,source=query.split(' AND SRC:');identifier=identifier.removeprefix('EXT_ID:')
        records=[r for r in records if r['id']==identifier and r['source']==source]
    else:
        records=[r for r in records if query.lower() in (r['title']+' '+r['abstractText']).lower()]
    start=0 if q['cursorMark']=='*' else int(q['cursorMark']);size=int(q['pageSize'])
    result={'syntheticFixtureNotice':'Synthetic records, not Europe PMC data','hitCount':len(records),
            'request':{'queryString':query},'resultList':{'result':records[start:start+size]}}
    if start+size<len(records): result['nextCursorMark']=str(start+size)
    return json_bytes(result)
