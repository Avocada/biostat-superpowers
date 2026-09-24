"""Trial search → pagination → detail → comparison over real MCP stdio."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

from mcp import Client, StdioServerParameters


async def run_demo(output: Path, live: bool = False):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    args = ["-m", "biostat_mcp.server", "--artifact-dir", str(output / "artifacts")]
    if not live:
        args.extend(["--offline", "--demo-trials"])
    events = []
    async with Client(StdioServerParameters(command=sys.executable, args=args)) as client:
        discovered = await client.list_tools()

        async def call(tool, **arguments):
            response = await client.call_tool(tool, arguments)
            payload = response.structured_content or json.loads(response.content[0].text)
            events.append({"tool": tool, "arguments": arguments, "is_error": response.is_error})
            if response.is_error:
                raise RuntimeError(payload)
            return payload["result"]

        first = await call("search_trials", condition="obesity", intervention="semaglutide", phase="PHASE3", page_size=5 if live else 2)
        pages = [first]
        if first["has_next_page"]:
            pages.append(await call("next_trial_page", search_artifact_id=first["artifact"]["artifact_id"]))
        if not first["studies"]:
            raise RuntimeError("No trial matches; query may need updating")
        detail = await call("get_trial", nct_id=first["studies"][0]["nct_id"])
        await client.read_resource(detail["raw_record_uri"])
        comparison = await call("compare_trials", artifact_ids=[p["artifact"]["artifact_id"] for p in pages])
        await client.read_resource(comparison["comparison_uri"])
        await client.read_resource(f"biostat://artifacts/{comparison['artifact']['artifact_id']}/figure")
        bad = await client.call_tool("get_trial", {"nct_id": "invalid"})
        if not bad.is_error:
            raise AssertionError("Malformed NCT ID must fail")
    report = {"mode": "live" if live else "synthetic", "transport": "MCP stdio subprocess",
              "tools_discovered": [t.name for t in discovered.tools], "calls": events,
              "search_pages": pages, "detail": detail, "comparison": comparison,
              "invalid_identifier_rejected": bad.is_error}
    (output / "run.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Contact ClinicalTrials.gov instead of synthetic fixtures")
    parser.add_argument("--output", type=Path, default=Path("outputs/trials-demo"))
    args = parser.parse_args()
    report = asyncio.run(run_demo(args.output, args.live))
    print(json.dumps({"mode": report["mode"], "matched_at_source": report["search_pages"][0]["artifact"]["total_count"],
                      "trials_compared": report["comparison"]["artifact"]["unique_trials"],
                      "status_counts": report["comparison"]["status_counts"],
                      "artifacts": report["comparison"]["artifact"]["local_directory"],
                      "report": str(args.output.resolve() / "run.json")}, indent=2))


if __name__ == "__main__":
    main()
