"""Offline contract tests; only the explicitly run live demo contacts UCI."""
import asyncio
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from biostat_mcp.core import (MAX_BYTES, ServiceError, Toolkit, describe_columns,
                              download_uci, parse_csv)

HAS_MCP = importlib.util.find_spec("mcp") is not None
HAS_RENDERER = importlib.util.find_spec("vl_convert") is not None


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.toolkit = Toolkit(self.root, offline=True)

    def tearDown(self):
        self.temp.cleanup()

    def expect_error(self, code, function, *args, **kwargs):
        with self.assertRaises(ServiceError) as ctx:
            function(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_catalog_and_offline_boundary(self):
        self.assertEqual(len(self.toolkit.list_datasets()["datasets"]), 3)
        self.assertFalse(self.toolkit.list_datasets("Iris")["datasets"][0]["available"])
        self.expect_error("offline", self.toolkit.fetch_dataset, "uci:53")
        self.expect_error("unsupported_dataset", self.toolkit.fetch_dataset, "../../secret")
        self.expect_error("invalid_request", self.toolkit.list_datasets, "x" * 201)

    def test_profile_missingness_and_identifier_roles(self):
        dataset = self.toolkit.fetch_dataset("demo")
        response = self.toolkit.profile_dataset(dataset["artifact_id"])
        variables = {v["name"]: v for v in response["profile"]["variables"]}
        self.assertEqual(response["profile"]["rows"], 12)
        self.assertEqual(variables["baseline_score"]["missing"], 1)
        self.assertEqual(variables["age"]["missing"], 1)
        self.assertEqual(variables["participant_id"]["kind"], "identifier")
        self.assertEqual(response["artifact"]["metadata_sha256"], dataset["metadata_sha256"])
        self.assertEqual(dataset["status"], "exploratory_unreviewed")

    def test_declared_categorical_numbers_not_continuous(self):
        profile = describe_columns(["sex"], [["0"], ["1"]], [{"name": "sex", "type": "Categorical"}])
        self.assertEqual(profile[0]["kind"], "categorical")
        self.assertNotIn("summary", profile[0])

    def test_invalid_numeric_not_silently_coerced(self):
        profile = describe_columns(["x"], [["1"], ["inf"], ["bad"]], [{"name": "x", "type": "Continuous"}])
        self.assertEqual(profile[0]["invalid_numeric"], 2)
        self.assertEqual(profile[0]["summary"]["mean"], 1)

    def test_csv_validation(self):
        for data in (b"", b"a,a\n1,2\n", b"a,b\n1\n", b"a\n", b"\xff"):
            with self.subTest(data=data):
                self.expect_error("invalid_dataset", parse_csv, data)
        self.expect_error("size_limit", parse_csv, b"a" * (MAX_BYTES + 1))
        with patch("biostat_mcp.core.MAX_ROWS", 1):
            self.expect_error("size_limit", parse_csv, b"x\n1\n2\n")

    def test_artifact_integrity(self):
        dataset = self.toolkit.fetch_dataset("demo")
        (Path(dataset["local_directory"]) / "data.csv").write_text("x\n1\n")
        self.expect_error("artifact_changed", self.toolkit.profile_dataset, dataset["artifact_id"])

    def test_source_metadata_integrity(self):
        dataset = self.toolkit.fetch_dataset("demo")
        (Path(dataset["local_directory"]) / "source.json").write_text("{}")
        self.expect_error("artifact_changed", self.toolkit.profile_dataset, dataset["artifact_id"])

    def test_path_and_symlink_rejection(self):
        self.expect_error("invalid_artifact", self.toolkit.inspect_artifact, "../secrets")
        (self.root / ("a" * 32)).symlink_to(self.root, target_is_directory=True)
        self.expect_error("not_found", self.toolkit.inspect_artifact, "a" * 32)
        dataset = self.toolkit.fetch_dataset("demo")
        path = Path(dataset["local_directory"]) / "data.csv"
        path.unlink()
        path.symlink_to(self.root / "outside.csv")
        self.expect_error("invalid_artifact", self.toolkit.profile_dataset, dataset["artifact_id"])

    def test_mock_uci_retrieval_and_provenance(self):
        metadata = {"status": 200, "data": {"uci_id": 53, "name": "Iris",
                    "data_url": "https://archive.ics.uci.edu/static/public/53/data.csv",
                    "repository_url": "https://archive.ics.uci.edu/dataset/53/iris", "variables": []}}
        calls = []
        def fetch(url):
            calls.append(url)
            return json.dumps(metadata).encode() if "/api/" in url else b"x\n1\n2\n"
        data = Toolkit(self.root, fetch=fetch).fetch_dataset("uci:53")
        self.assertEqual(data["rows"], 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(data["data_sha256"]), 64)
        metadata["data"]["data_url"] = "https://example.com/data.csv"
        self.expect_error("invalid_source_response", Toolkit(self.root, fetch=fetch).fetch_dataset, "uci:53")
        self.assertEqual(len(calls), 3)

    def test_malformed_metadata(self):
        for body in (b"not json", b"{}", b"[]", b'{"status":200,"data":null}'):
            with self.subTest(body=body):
                self.expect_error("invalid_source_response", Toolkit(self.root, fetch=lambda _: body).fetch_dataset, "uci:53")

    def test_network_url_boundary(self):
        for url in ("file:///etc/passwd", "https://example.com/data.csv", "https://archive.ics.uci.edu.evil/api/dataset"):
            self.expect_error("invalid_source", download_uci, url)

    @patch("biostat_mcp.core.time.sleep")
    @patch("biostat_mcp.core.build_opener")
    def test_timeout_retry_is_bounded(self, opener, sleep):
        opener.return_value.open.side_effect = URLError("timeout")
        self.expect_error("source_unavailable", download_uci, "https://archive.ics.uci.edu/api/dataset?id=53")
        self.assertEqual(opener.return_value.open.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    @patch("biostat_mcp.core.build_opener")
    def test_redirect_and_not_found_not_retried(self, opener):
        url = "https://archive.ics.uci.edu/api/dataset?id=53"
        for status, code in ((302, "source_unavailable"), (404, "not_found")):
            opener.return_value.open.reset_mock()
            opener.return_value.open.side_effect = HTTPError(url, status, "error", {}, None)
            self.expect_error(code, download_uci, url)
            self.assertEqual(opener.return_value.open.call_count, 1)

    @patch("biostat_mcp.core.build_opener")
    def test_download_size_limit(self, opener):
        opener.return_value.open.return_value = io.BytesIO(b"12345")
        self.expect_error("size_limit", download_uci, "https://archive.ics.uci.edu/api/dataset?id=53", max_bytes=4)

    def test_profile_snapshot_gate(self):
        first = self.toolkit.fetch_dataset("demo")
        second = self.toolkit.fetch_dataset("demo")
        profile = self.toolkit.profile_dataset(first["artifact_id"])["artifact"]
        self.expect_error("profile_required", self.toolkit.render_chart, second["artifact_id"],
                          profile["artifact_id"], "histogram", "age")

    def test_plot_type_and_arguments(self):
        data = self.toolkit.fetch_dataset("demo")
        profile = self.toolkit.profile_dataset(data["artifact_id"])["artifact"]
        args = (data["artifact_id"], profile["artifact_id"])
        self.expect_error("incompatible_column", self.toolkit.render_chart, *args, "histogram", "group")
        self.expect_error("invalid_request", self.toolkit.render_chart, *args, "scatter", "age")
        self.expect_error("unsupported_chart", self.toolkit.render_chart, *args, "custom-code", "age")
        self.expect_error("invalid_request", self.toolkit.render_chart, *args, "histogram", "unknown")

    @unittest.skipUnless(HAS_RENDERER, "Install .[mcp] for local rendering tests")
    def test_all_chart_templates_and_omissions(self):
        data = self.toolkit.fetch_dataset("demo")
        profile = self.toolkit.profile_dataset(data["artifact_id"])["artifact"]
        for template, x, y, omitted in (("histogram", "age", None, 1),
                                        ("scatter", "age", "baseline_score", 2),
                                        ("boxplot", "group", "followup_score", 0)):
            with self.subTest(template=template):
                chart = self.toolkit.render_chart(data["artifact_id"], profile["artifact_id"], template, x, y)
                self.assertEqual(chart["rows_omitted"], omitted)
                self.assertEqual(chart["rows_used"], 12 - omitted)
                self.assertIn("<svg", self.toolkit.read_figure(chart["artifact_id"]))
                self.assertTrue(self.toolkit._read(chart["artifact_id"], "figure.png").startswith(b"\x89PNG"))
                spec = json.loads(self.toolkit._read(chart["artifact_id"], "chart.vl.json"))
                self.assertNotIn("url", spec["data"])
                self.assertEqual(set(spec["data"]["values"][0]), {"x", "y"} if y else {"x"})


@unittest.skipUnless(HAS_MCP and HAS_RENDERER, "Install .[mcp] for protocol integration")
class ProtocolTests(unittest.TestCase):
    def test_actual_stdio_client_server_roundtrip(self):
        from biostat_mcp.demo import run_demo
        with tempfile.TemporaryDirectory() as temp:
            report = asyncio.run(asyncio.wait_for(run_demo(Path(temp)), timeout=60))
            self.assertTrue({"list_datasets", "fetch_dataset", "profile_dataset", "list_chart_examples",
                             "render_chart", "inspect_artifact"}.issubset(report["tools_discovered"]))
            self.assertTrue(report["unsupported_dataset_rejected"])
            self.assertEqual(report["chart"]["rows_used"], 11)
            self.assertTrue((Path(temp) / "run.json").is_file())


if __name__ == "__main__":
    unittest.main()
