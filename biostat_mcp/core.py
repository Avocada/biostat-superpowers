"""Bounded data/reproducibility operations, independent of the MCP protocol.

Exploratory artifacts are never marked as reviewed statistical results. No
arbitrary filesystem paths, remote URLs, or executable chart specs are accepted.
"""
from copy import deepcopy
import csv
from datetime import datetime, timezone
import hashlib
from importlib.resources import files
import io
import json
import math
from pathlib import Path
import re
import shutil
import statistics
import time
from typing import Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 20000
MAX_COLUMNS = 100
MISSING = {"", "?", "na", "n/a", "null", "nan"}
DATASETS = (
    {"id": "demo", "name": "Synthetic study fixture", "provider": "bundled", "network_required": False},
    {"id": "uci:53", "name": "Iris", "provider": "UCI", "network_required": True},
    {"id": "uci:45", "name": "Heart Disease", "provider": "UCI", "network_required": True},
)


class ServiceError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code, self.retryable = code, retryable


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(data: bytes):
    return hashlib.sha256(data).hexdigest()


def packaged_json(name):
    return json.loads(files("biostat_mcp").joinpath("data", name).read_text())


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_uci(url: str, max_bytes: int = MAX_BYTES) -> bytes:
    """Only UCI HTTPS, no redirects; two attempts, bounded size/read time."""
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "archive.ics.uci.edu"
            or not parts.path.startswith(("/api/dataset", "/static/public/"))):
        raise ServiceError("invalid_source", "Only the configured UCI source is allowed")
    return download_bounded(url, "UCI", max_bytes)


def download_bounded(url: str, provider: str, max_bytes: int = MAX_BYTES, *, before_request=None) -> bytes:
    """Internal transport; callers must validate their own source allowlist."""
    opener = build_opener(NoRedirect)
    for attempt in range(2):
        try:
            if before_request is not None:
                before_request()
            request = Request(url, headers={"User-Agent": "biostat-superpowers/0.2.0"})
            with opener.open(request, timeout=10) as response:
                deadline = time.monotonic() + 15
                chunks, size = [], 0
                while True:
                    chunk = response.read(min(65536, max_bytes + 1 - size))
                    size += len(chunk)
                    if size > max_bytes:
                        raise ServiceError("size_limit", "Source exceeds download limit")
                    if time.monotonic() > deadline:
                        raise ServiceError("source_timeout", "Source exceeded read deadline", True)
                    if not chunk:
                        return b"".join(chunks)
                    chunks.append(chunk)
        except HTTPError as exc:
            code = "not_found" if exc.code == 404 else "source_unavailable"
            retryable = exc.code == 429 or exc.code >= 500
            if not retryable or attempt == 1:
                raise ServiceError(code, f"{provider} returned HTTP {exc.code}", retryable) from exc
        except (URLError, TimeoutError, OSError) as exc:
            if attempt == 1:
                raise ServiceError("source_unavailable", f"{provider} request failed or timed out", True) from exc
        time.sleep(0.2)
    raise AssertionError("unreachable")


def parse_csv(raw: bytes):
    if len(raw) > MAX_BYTES:
        raise ServiceError("size_limit", "Dataset exceeds byte limit")
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
        header = next(reader)
        if (not header or len(header) > MAX_COLUMNS or any(not h or len(h) > 128 for h in header)
                or len(set(header)) != len(header)):
            raise ServiceError("invalid_dataset", "CSV needs unique nonempty column names within limits")
        rows = []
        for row in reader:
            if len(row) != len(header):
                raise ServiceError("invalid_dataset", "CSV row width does not match its header")
            if len(rows) >= MAX_ROWS or any(len(cell) > 10000 for cell in row):
                raise ServiceError("size_limit", "Dataset exceeds row or cell limits")
            rows.append([None if value.strip().lower() in MISSING else value for value in row])
        if not rows:
            raise ServiceError("invalid_dataset", "CSV contains no observations")
        return header, rows
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise ServiceError("invalid_dataset", "Source is not a supported UTF-8 CSV") from exc


def numeric(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError, OverflowError):
        return None


def describe_columns(header, rows, variables):
    by_name = {v["name"]: v for v in variables if isinstance(v, dict) and "name" in v}
    profiles = []
    for i, name in enumerate(header):
        values = [row[i] for row in rows if row[i] is not None]
        declared = by_name.get(name, {})
        declared_type = str(declared.get("type", "")).lower()
        converted = [numeric(value) for value in values]
        invalid = sum(value is None for value in converted)
        role = declared.get("role", "unknown")
        if str(role).lower() == "id":
            kind = "identifier"
        elif declared_type in ("categorical", "binary", "ordinal"):
            kind = "categorical"
        elif declared_type in ("continuous", "integer", "real", "numeric"):
            kind = "numeric"
        else:
            kind = "numeric" if values and invalid == 0 else "categorical"
        profile = {"name": name, "kind": kind, "role": role, "units": declared.get("units"),
                   "type_source": "metadata" if declared_type or str(role).lower() == "id" else "inferred",
                   "nonmissing": len(values), "missing": len(rows) - len(values),
                   "unique_nonmissing": len(set(values))}
        if kind == "numeric":
            finite = [n for n in converted if n is not None]
            profile["invalid_numeric"] = invalid
            profile["summary"] = (dict(min=min(finite), max=max(finite), mean=statistics.fmean(finite),
                                       median=statistics.median(finite)) if finite else None)
        profiles.append(profile)
    return profiles


class Toolkit:
    def __init__(self, artifact_root: Path, *, offline: bool = False,
                 fetch: Callable[[str], bytes] = download_uci, input_dir: Optional[Path] = None):
        self.root = Path(artifact_root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.offline, self.fetch = offline, fetch
        self.input_dir = Path(input_dir).expanduser().resolve() if input_dir is not None else None

    def list_datasets(self, query: str = ""):
        if len(query) > 200:
            raise ServiceError("invalid_request", "Query must be at most 200 characters")
        return {"scope": "Curated starter catalog, not the complete UCI repository",
                "datasets": [dict(item, available=not (self.offline and item["network_required"]))
                             for item in DATASETS if query.lower() in (item["id"] + item["name"]).lower()]}

    def list_chart_examples(self, query: str = ""):
        if len(query) > 200:
            raise ServiceError("invalid_request", "Query must be at most 200 characters")
        return {"scope": "Project-authored Vega-Lite examples, not a scraped gallery",
                "examples": [item for item in packaged_json("charts.json")
                             if query.lower() in json.dumps(item).lower()]}

    def _save(self, kind: str, payloads: dict[str, bytes], metadata: dict):
        artifact_id = uuid4().hex
        pending = self.root / (".pending-" + artifact_id)
        pending.mkdir()
        try:
            for name, contents in payloads.items():
                (pending / name).write_bytes(contents)
            manifest = {"schema_version": 1, "artifact_id": artifact_id, "kind": kind,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "status": "exploratory_unreviewed", **metadata,
                        "files": {name: {"sha256": digest(data), "bytes": len(data)}
                                  for name, data in payloads.items()}}
            (pending / "manifest.json").write_bytes(json_bytes(manifest))
            pending.rename(self.root / artifact_id)
            return self.inspect_artifact(artifact_id)
        except BaseException:
            if pending.exists():
                shutil.rmtree(pending)
            raise

    def _directory(self, artifact_id):
        if not isinstance(artifact_id, str) or not re.fullmatch(r"[0-9a-f]{32}", artifact_id):
            raise ServiceError("invalid_artifact", "Expected a server-issued artifact ID")
        directory = self.root / artifact_id
        if directory.is_symlink() or not directory.is_dir():
            raise ServiceError("not_found", "Artifact is not available in this server's store")
        return directory

    def _manifest(self, artifact_id):
        directory = self._directory(artifact_id)
        path = directory / "manifest.json"
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ServiceError("invalid_artifact", "Artifact manifest is unavailable")
        try:
            manifest = json.loads(path.read_text())
            if (not isinstance(manifest, dict) or manifest.get("artifact_id") != artifact_id
                    or manifest.get("schema_version") != 1 or manifest.get("kind") not in {"dataset", "profile", "chart", "trial_search", "trial_detail", "trial_comparison", "literature_search", "literature_article", "literature_references", "review_handoff"}
                    or not isinstance(manifest.get("files"), dict)):
                raise ValueError("manifest identity")
            return manifest
        except (ValueError, KeyError) as exc:
            raise ServiceError("invalid_artifact", "Invalid artifact manifest") from exc

    def _read(self, artifact_id, filename):
        manifest = self._manifest(artifact_id)
        if filename not in manifest["files"]:
            raise ServiceError("not_found", "Artifact does not contain the requested file")
        path = self._directory(artifact_id) / filename
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 20 * MAX_BYTES:
            raise ServiceError("invalid_artifact", "Artifact file is unavailable or exceeds limits")
        data = path.read_bytes()
        if digest(data) != manifest["files"][filename]["sha256"]:
            raise ServiceError("artifact_changed", "Artifact contents changed; retrieve or generate a new artifact")
        return data

    def inspect_artifact(self, artifact_id):
        manifest = self._manifest(artifact_id)
        return {**manifest, "manifest_uri": f"biostat://artifacts/{artifact_id}/manifest",
                "local_directory": str(self._directory(artifact_id))}

    def fetch_dataset(self, dataset_id: str):
        if dataset_id not in {item["id"] for item in DATASETS}:
            raise ServiceError("unsupported_dataset", "Choose a dataset ID from list_datasets")
        if dataset_id == "demo":
            raw = files("biostat_mcp").joinpath("data", "demo.csv").read_bytes()
            variables = [dict(name=name, role="ID" if name == "participant_id" else "Feature",
                              type="Categorical" if name in ("participant_id", "group") else "Continuous")
                         for name in ["participant_id", "age", "baseline_score", "followup_score", "group"]]
            source = {"provider": "bundled", "dataset_id": "demo", "name": "Synthetic study fixture",
                      "source_url": "package://biostat_mcp/data/demo.csv", "license": "MIT",
                      "variables": variables, "notice": "Synthetic; not real participants or treatment evidence"}
        else:
            if self.offline:
                raise ServiceError("offline", "Network retrieval is disabled for this server")
            uci_id = int(dataset_id.split(":")[1])
            url = f"https://archive.ics.uci.edu/api/dataset?id={uci_id}"
            try:
                envelope = json.loads(self.fetch(url))
                if not isinstance(envelope, dict):
                    raise ValueError("metadata envelope must be an object")
                source = envelope["data"]
                if envelope.get("status") != 200 or not isinstance(source, dict) or source.get("uci_id") != uci_id:
                    raise ValueError("wrong metadata identity")
                expected = f"https://archive.ics.uci.edu/static/public/{uci_id}/data.csv"
                if source.get("data_url") != expected or not isinstance(source.get("variables"), list):
                    raise ValueError("unsupported data location or schema")
                if any(not isinstance(v, dict) or not isinstance(v.get("name"), str) for v in source["variables"]):
                    raise ValueError("invalid variable metadata")
                source = {**source, "provider": "UCI", "dataset_id": dataset_id, "metadata_url": url,
                          "license_note": "Check the linked UCI dataset page for dataset-specific reuse terms."}
                raw = self.fetch(expected)
                variables = source["variables"]
            except (ValueError, KeyError, TypeError) as exc:
                raise ServiceError("invalid_source_response", "UCI returned unsupported dataset metadata") from exc
        header, rows = parse_csv(raw)
        metadata = {"dataset_id": dataset_id, "name": source.get("name"), "rows": len(rows), "columns": header,
                    "source": source.get("repository_url", source.get("source_url")),
                    "data_sha256": digest(raw), "metadata_sha256": digest(json_bytes(source)),
                    "missing_tokens": sorted(MISSING)}
        return self._save("dataset", {"data.csv": raw, "source.json": json_bytes(source)}, metadata)

    def import_local_csv(self, filename: str, source_reference: str = "", synthetic: bool = False):
        """Snapshot one host-staged CSV from the explicit input directory, never arbitrary paths."""
        if self.input_dir is None:
            raise ServiceError("local_import_disabled", "Host must configure --input-dir before importing CSV files")
        if (not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.csv", filename)
                or ".." in filename):
            raise ServiceError("invalid_request", "Use a plain CSV filename in the configured input directory")
        if not isinstance(source_reference, str) or len(source_reference) > 1000 or type(synthetic) is not bool:
            raise ServiceError("invalid_request", "Source reference must be at most 1000 characters; synthetic must be boolean")
        path = self.input_dir / filename
        if path.is_symlink() or not path.is_file() or path.resolve().parent != self.input_dir:
            raise ServiceError("invalid_source", "Only regular files directly inside the configured input directory are allowed")
        if path.stat().st_size > MAX_BYTES:
            raise ServiceError("size_limit", "Dataset exceeds byte limit")
        # No-follow protects the final path component if it changes between the checks and open.
        import os
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
        except OSError as exc:
            raise ServiceError("invalid_source", "Local CSV could not be opened as a regular source") from exc
        header, rows = parse_csv(raw)
        source = {"provider": "host-staged-local", "source_filename": filename,
                  "source_reference": source_reference, "reference_verified": False, "variables": [],
                  "synthetic": synthetic,
                  "notice": "Source reference is host-supplied, not independently verified. CSV bytes are copied without normalization."}
        return self._save("dataset", {"data.csv": raw, "source.json": json_bytes(source)},
            {"dataset_id": "local:" + filename, "name": filename, "rows": len(rows), "columns": header,
             "source": source_reference, "synthetic": synthetic, "data_sha256": digest(raw),
             "metadata_sha256": digest(json_bytes(source)), "missing_tokens": sorted(MISSING)})

    def _dataset(self, artifact_id):
        manifest = self._manifest(artifact_id)
        if manifest["kind"] != "dataset":
            raise ServiceError("wrong_artifact_type", "This operation requires a dataset artifact")
        header, rows = parse_csv(self._read(artifact_id, "data.csv"))
        source = json.loads(self._read(artifact_id, "source.json"))
        return manifest, header, rows, source

    def profile_dataset(self, artifact_id: str):
        manifest, header, rows, source = self._dataset(artifact_id)
        profile = {"dataset_artifact_id": artifact_id, "rows": len(rows), "columns": len(header),
                   "data_sha256": manifest["data_sha256"],
                   "variables": describe_columns(header, rows, source["variables"]),
                   "interpretation": "Descriptive profile only; inferred types and study validity require specialist review.",
                   "missing_tokens": sorted(MISSING)}
        artifact = self._save("profile", {"profile.json": json_bytes(profile)},
                              {"dataset_artifact_id": artifact_id, "data_sha256": manifest["data_sha256"],
                               "metadata_sha256": manifest["metadata_sha256"]})
        return {"artifact": artifact, "profile": profile}

    def render_chart(self, artifact_id: str, profile_id: str, example_id: str, x: str,
                     y: Optional[str] = None, title: str = ""):
        manifest, header, rows, source = self._dataset(artifact_id)
        profile_manifest = self._manifest(profile_id)
        if (profile_manifest["kind"] != "profile" or profile_manifest.get("dataset_artifact_id") != artifact_id
                or profile_manifest.get("data_sha256") != manifest["data_sha256"]
                or profile_manifest.get("metadata_sha256") != manifest["metadata_sha256"]):
            raise ServiceError("profile_required", "Profile this dataset snapshot before rendering")
        self._read(profile_id, "profile.json")
        examples = {item["id"]: item for item in packaged_json("charts.json")}
        if example_id not in examples:
            raise ServiceError("unsupported_chart", "Choose a chart from list_chart_examples")
        if len(title) > 160 or x not in header or (y is not None and y not in header):
            raise ServiceError("invalid_request", "Unknown column or title exceeds 160 characters")
        example = examples[example_id]
        if (example_id == "histogram" and y is not None) or (example_id != "histogram" and y is None):
            raise ServiceError("invalid_request", "Histogram uses x only; other templates require x and y")
        profiles = {item["name"]: item for item in describe_columns(header, rows, source["variables"])}
        for axis, column in (("x", x), ("y", y)):
            if column is None:
                continue
            p = profiles[column]
            if p["kind"] != example["requirements"][axis] or p.get("invalid_numeric", 0):
                raise ServiceError("incompatible_column", f"{column} must be {example['requirements'][axis]} with valid values")
            if p["kind"] == "categorical" and p["unique_nonmissing"] > 20:
                raise ServiceError("size_limit", "Grouped plots support at most 20 categories")
        values = []
        for row in rows:
            point = {}
            for axis, column in (("x", x), ("y", y)):
                if column is not None:
                    value = row[header.index(column)]
                    if value is None:
                        break
                    if profiles[column]["kind"] == "categorical" and len(value) > 80:
                        raise ServiceError("size_limit", "Category labels exceed 80 characters")
                    point[axis] = numeric(value) if profiles[column]["kind"] == "numeric" else value
            else:
                values.append(point)
        if not values:
            raise ServiceError("no_plottable_rows", "No complete observations for selected columns")
        spec = deepcopy(example["spec"])
        omitted = len(rows) - len(values)
        spec.update({"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "width": 600, "height": 360,
                     "data": {"values": values},
                     "title": {"text": title or example["name"],
                               "subtitle": f"Exploratory | n={len(values)} | omitted for missing selected values: {omitted}"}})
        for axis, column in (("x", x), ("y", y)):
            if column is not None:
                units = profiles[column].get("units")
                spec["encoding"][axis]["title"] = column + (f" ({units})" if units else "")
        try:
            import vl_convert as vlc
        except ImportError as exc:
            raise ServiceError("missing_dependency", "Install the mcp optional dependencies to render charts") from exc
        try:
            svg = vlc.vegalite_to_svg(spec, allowed_base_urls=[]).encode()
            png = vlc.vegalite_to_png(spec, allowed_base_urls=[])
        except Exception as exc:
            raise ServiceError("render_failed", "Local Vega-Lite rendering failed") from exc
        provenance = {"dataset_artifact_id": artifact_id, "profile_artifact_id": profile_id,
                      "data_sha256": manifest["data_sha256"], "metadata_sha256": manifest["metadata_sha256"],
                      "template_id": example_id, "template_sha256": digest(json_bytes(example)),
                      "template_source": example["source"], "renderer": "vl-convert-python",
                      "renderer_version": vlc.__version__, "rows_used": len(values), "rows_omitted": omitted,
                      "omission_rule": "Exclude only rows missing a selected axis; preserve original dataset",
                      "x": x, "y": y}
        return self._save("chart", {"chart.vl.json": json_bytes(spec), "figure.svg": svg,
                                    "figure.png": png, "provenance.json": json_bytes(provenance)}, provenance)

    def read_figure(self, artifact_id):
        return self._read(artifact_id, "figure.svg").decode()
