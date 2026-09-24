"""Trial-linked literature retrieval and deduplication over real MCP stdio."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

from mcp import Client, StdioServerParameters


async def run_demo(output: Path, live=False):
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    args=['-m','biostat_mcp.server','--artifact-dir',str(output/'artifacts')]
    if not live:args+=['--offline','--demo-literature','--demo-trials']
    events=[];pages=[];details=[]
    trial_id='NCT03548935' if live else 'NCT00000001'
    async with Client(StdioServerParameters(command=sys.executable,args=args)) as client:
        discovery=await client.list_tools()
        async def call(name,**arguments):
            response=await client.call_tool(name,arguments)
            payload=response.structured_content or json.loads(response.content[0].text)
            events.append({'tool':name,'arguments':arguments,'is_error':response.is_error})
            if response.is_error:raise RuntimeError(payload)
            return payload['result']
        trial=await call('get_trial',nct_id=trial_id)
        for provider in ('pubmed','europepmc'):
            first=await call('search_literature',provider=provider,query=trial_id,page_size=3 if live else 2)
            pages.append(first)
            if first['has_next_page']:
                pages.append(await call('next_literature_page',search_artifact_id=first['artifact']['artifact_id']))
            detail=await call('get_article',provider=provider,article_id='33567185' if live else '90000001')
            details.append(detail)
            await client.read_resource(detail['record_uri'])
        references=await call('build_reference_list',artifact_ids=[r['artifact']['artifact_id'] for r in pages+details])
        await client.read_resource(references['reference_uri'])
        rejected=await client.call_tool('get_article',{'provider':'pubmed','article_id':'../invalid'})
        if not rejected.is_error:raise AssertionError('Invalid article ID must be rejected')
    report={'mode':'live' if live else 'synthetic','transport':'MCP stdio subprocess',
            'tools_discovered':[t.name for t in discovery.tools],'trial':trial,'search_pages':pages,'details':details,
            'references':references,'calls':events,'invalid_identifier_rejected':rejected.is_error,
            'notice':'Trial-ID keyword search and mentions are not verified article-to-trial relationships.'}
    (output/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('outputs/literature-demo'))
    args=parser.parse_args();report=asyncio.run(run_demo(args.output,args.live))
    print(json.dumps({'mode':report['mode'],'source_totals':{p['artifact']['provider']:p['artifact']['total_count'] for p in report['search_pages']},
                      'unique_references':report['references']['unique_references'],
                      'duplicates_grouped':report['references']['duplicates_grouped'],
                      'artifacts':report['references']['artifact']['local_directory'],'report':str(args.output.resolve()/'run.json')},indent=2))


if __name__=='__main__':main()
