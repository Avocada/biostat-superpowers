"""Real MCP subprocess demo; default fixture is synthetic and needs no network."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

from mcp import Client, StdioServerParameters


async def run_demo(output: Path, dataset: str = "demo"):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    args = ["-m", "biostat_mcp.server", "--artifact-dir", str(output / "artifacts")]
    if dataset == "demo":
        args.append("--offline")
    events = []
    async with Client(StdioServerParameters(command=sys.executable, args=args)) as client:
        discovery = await client.list_tools()
        await client.read_resource("biostat://catalog")

        async def call(name, **arguments):
            response = await client.call_tool(name, arguments)
            payload = response.structured_content
            if payload is None:
                payload = json.loads(response.content[0].text)
            events.append({"tool": name, "arguments": arguments, "is_error": response.is_error})
            if response.is_error:
                raise RuntimeError(payload)
            return payload["result"]

        await call("list_datasets")
        data = await call("fetch_dataset", dataset_id=dataset)
        profile = await call("profile_dataset", artifact_id=data["artifact_id"])
        await call("list_chart_examples")
        columns = {"demo": ("baseline_score", "followup_score"),
                   "uci:53": ("sepal length", "petal length"), "uci:45": ("age", "chol")}
        x, y = columns[dataset]
        chart = await call("render_chart", artifact_id=data["artifact_id"],
                           profile_id=profile["artifact"]["artifact_id"], example_id="scatter", x=x, y=y,
                           title=f"{data['name']}: exploratory scatter")
        await call("inspect_artifact", artifact_id=chart["artifact_id"])
        await client.read_resource(chart["manifest_uri"])
        await client.read_resource(f"biostat://artifacts/{chart['artifact_id']}/figure")
        rejected = await client.call_tool("fetch_dataset", {"dataset_id": "unsupported"})
        if not rejected.is_error:
            raise AssertionError("Unsupported dataset should return a protocol tool error")
    report = {"transport": "MCP stdio subprocess", "tools_discovered": [t.name for t in discovery.tools],
              "dataset": data, "profile": profile, "chart": chart, "calls": events,
              "unsupported_dataset_rejected": rejected.is_error,
              "notice": "Exploratory artifacts; no LLM, clinical inference or token-savings measurement."}
    (output / "run.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/mcp-demo"))
    parser.add_argument("--dataset", choices=["demo", "uci:53", "uci:45"], default="demo")
    args = parser.parse_args()
    report = asyncio.run(run_demo(args.output, args.dataset))
    print(json.dumps({"dataset": args.dataset, "rows": report["dataset"]["rows"],
                      "rows_plotted": report["chart"]["rows_used"],
                      "figure": str(Path(report["chart"]["local_directory"]) / "figure.png"),
                      "report": str(args.output.resolve() / "run.json")}, indent=2))


if __name__ == "__main__":
    main()
