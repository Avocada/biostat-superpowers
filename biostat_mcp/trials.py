"""ClinicalTrials.gov v2 snapshots and bounded descriptive comparisons."""
from collections import Counter
import csv
from datetime import datetime, timezone
import io
import json
import re
from urllib.parse import urlencode, urlsplit, parse_qs

from .core import MAX_BYTES, ServiceError, Toolkit, digest, download_bounded, json_bytes, packaged_json

BASE = "https://clinicaltrials.gov/api/v2/studies"
STATUSES = {"RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING", "COMPLETED",
            "ENROLLING_BY_INVITATION", "SUSPENDED", "TERMINATED", "WITHDRAWN", "UNKNOWN",
            "AVAILABLE", "NO_LONGER_AVAILABLE", "TEMPORARILY_NOT_AVAILABLE", "APPROVED_FOR_MARKETING"}
PHASES = {"EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4", "NA"}
NOTICE = "Registry records are source-reported, not independently reviewed evidence of efficacy or safety."


def invalid(message):
    return ServiceError("invalid_source_response", message)


def download_trials(url):
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "clinicaltrials.gov" or parts.fragment
            or not re.fullmatch(r"/api/v2/studies(?:/NCT[0-9]{8})?", parts.path)):
        raise ServiceError("invalid_source", "Only the configured ClinicalTrials.gov v2 endpoints are allowed")
    return download_bounded(url, "ClinicalTrials.gov")


def nct_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"NCT[0-9]{8}", value):
        raise ServiceError("invalid_request", "Expected an NCT identifier, for example NCT03548935")
    return value


def module(parent, key):
    value = parent.get(key, {})
    if not isinstance(value, dict):
        raise invalid(f"Unsupported {key} object")
    return value


def array(parent, key, item_type):
    value = parent.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, item_type) for item in value):
        raise invalid(f"Unsupported {key} list")
    return value


def normalize(study):
    if not isinstance(study, dict):
        raise invalid("Study must be an object")
    protocol = module(study, "protocolSection")
    ident = module(protocol, "identificationModule")
    try:
        identifier = nct_id(ident.get("nctId"))
    except ServiceError as exc:
        raise invalid("Study has no valid NCT identifier") from exc
    status = module(protocol, "statusModule")
    design = module(protocol, "designModule")
    eligibility = module(protocol, "eligibilityModule")
    outcomes = module(protocol, "outcomesModule")
    locations = array(module(protocol, "contactsLocationsModule"), "locations", dict)
    interventions = array(module(protocol, "armsInterventionsModule"), "interventions", dict)
    results = module(study, "resultsSection")
    has_results = study.get("hasResults")
    if has_results is not None and not isinstance(has_results, bool):
        raise invalid("hasResults must be boolean when supplied")
    overall = status.get("overallStatus")
    if overall is not None and not isinstance(overall, str):
        raise invalid("overallStatus must be text")
    return {"nct_id": identifier, "title": ident.get("briefTitle"),
            "source_url": f"https://clinicaltrials.gov/study/{identifier}",
            "overall_status": overall, "last_update_posted": module(status, "lastUpdatePostDateStruct").get("date"),
            "conditions": array(module(protocol, "conditionsModule"), "conditions", str),
            "interventions": [{k: item.get(k) for k in ("name", "type")} for item in interventions],
            "study_type": design.get("studyType"), "phases": array(design, "phases", str),
            "design": module(design, "designInfo"), "enrollment": module(design, "enrollmentInfo"),
            "eligibility": {k: eligibility.get(k) for k in
                            ("eligibilityCriteria", "sex", "minimumAge", "maximumAge", "healthyVolunteers")},
            "primary_outcomes": array(outcomes, "primaryOutcomes", dict),
            "locations": [{k: loc.get(k) for k in ("facility", "city", "state", "country", "status")} for loc in locations],
            "has_results": has_results, "results_sections": sorted(results),
            "results_notice": "Posted results are available in the raw record resource; availability is not a quality assessment."}


def compact(study):
    return {key: study[key] for key in ("nct_id", "title", "source_url", "overall_status", "phases",
                                       "enrollment", "has_results", "last_update_posted")}


class TrialService:
    def __init__(self, store: Toolkit, *, fetch=download_trials, demo=False):
        if demo and not store.offline:
            raise ValueError("Synthetic trial mode requires offline=True")
        self.store, self.fetch, self.demo = store, fetch, demo

    def _get(self, url):
        if self.demo:
            raw = self._fixture(url)
        elif self.store.offline:
            raise ServiceError("offline", "ClinicalTrials.gov retrieval is disabled for this server")
        else:
            raw = self.fetch(url)
        if len(raw) > MAX_BYTES:
            raise ServiceError("size_limit", "Trial response exceeds 5 MiB; reduce page_size")
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise invalid("ClinicalTrials.gov returned invalid JSON") from exc
        if not isinstance(body, dict):
            raise invalid("ClinicalTrials.gov response must be an object")
        return raw, body

    def _fixture(self, url):
        """Explicit synthetic mode; no silent fallback after a live-source failure."""
        studies = packaged_json("trials-demo.json")["studies"]
        parts = urlsplit(url)
        if parts.path != "/api/v2/studies":
            identifier = parts.path.rsplit("/", 1)[1]
            match = next((s for s in studies if normalize(s)["nct_id"] == identifier), None)
            if match is None:
                raise ServiceError("not_found", "Synthetic trial ID not found")
            return json_bytes(match)
        params = {k: v[0] for k, v in parse_qs(parts.query).items()}
        selected = []
        for study in studies:
            item = normalize(study)
            if params.get("query.cond", "").lower() not in " ".join(item["conditions"]).lower():
                continue
            if params.get("query.intr", "").lower() not in " ".join(i["name"] for i in item["interventions"]).lower():
                continue
            if params.get("filter.overallStatus") and item["overall_status"] != params["filter.overallStatus"]:
                continue
            if params.get("filter.advanced") and params["filter.advanced"].removeprefix("AREA[Phase]") not in item["phases"]:
                continue
            selected.append(study)
        offset = int(params.get("pageToken", "0")); size = int(params["pageSize"])
        result = {"studies": selected[offset:offset + size], "totalCount": len(selected)}
        if offset + size < len(selected):
            result["nextPageToken"] = str(offset + size)
        return json_bytes(result)

    def search_trials(self, condition="", intervention="", status=None, phase=None, page_size=10):
        for value in (condition, intervention):
            if not isinstance(value, str) or len(value) > 200 or any(ord(c) < 32 for c in value):
                raise ServiceError("invalid_request", "Search terms must be text of at most 200 characters without control characters")
        if status is not None and status not in STATUSES:
            raise ServiceError("invalid_request", "Unsupported recruitment status")
        if phase is not None and phase not in PHASES:
            raise ServiceError("invalid_request", "Phase must be EARLY_PHASE1, PHASE1–PHASE4, or NA")
        if type(page_size) is not int or not 1 <= page_size <= 20:
            raise ServiceError("invalid_request", "page_size must be between 1 and 20")
        query = {"condition": condition.strip(), "intervention": intervention.strip(),
                 "status": status, "phase": phase, "page_size": page_size}
        return self._search(query)

    def _search(self, query, token=None, previous=None, page=1):
        params = {"format": "json", "pageSize": query["page_size"], "countTotal": "true"}
        for key, field in (("condition", "query.cond"), ("intervention", "query.intr"), ("status", "filter.overallStatus")):
            if query[key]:
                params[field] = query[key]
        if query["phase"]:
            params["filter.advanced"] = "AREA[Phase]" + query["phase"]
        if token:
            params["pageToken"] = token
        url = BASE + "?" + urlencode(params)
        raw, body = self._get(url)
        if "studies" not in body:
            raise invalid("Search response has no studies array")
        studies = [self._normalize(s) for s in array(body, "studies", dict)]
        if len(studies) > query["page_size"] or len({s["nct_id"] for s in studies}) != len(studies):
            raise invalid("Search returned too many or duplicate studies")
        next_token, total = body.get("nextPageToken"), body.get("totalCount")
        if next_token is not None and (not isinstance(next_token, str) or not next_token or len(next_token) > 8192 or next_token == token):
            raise invalid("Unsupported or repeated pagination token")
        if total is not None and (type(total) is not int or total < len(studies)):
            raise invalid("Unsupported totalCount")
        saved = {"query": query, "studies": studies, "next_page_token": next_token,
                 "total_count": total, "page": page, "previous_search_id": previous}
        artifact = self.store._save("trial_search", {"response.json": raw, "trials.json": json_bytes(saved)},
                                   self._provenance(url, raw, returned_count=len(studies), total_count=total,
                                                    page=page, has_next_page=bool(next_token), query=query,
                                                    previous_search_id=previous))
        return {"artifact": artifact, "studies": [compact(s) for s in studies],
                "has_next_page": bool(next_token), "notice": NOTICE,
                "scope": "One registry search page; total_count is the source-reported total, not the number downloaded."}

    def next_trial_page(self, search_artifact_id):
        manifest, saved = self._load(search_artifact_id, {"trial_search"})
        if manifest["synthetic"] != self.demo:
            raise ServiceError("invalid_request", "Pagination mode must match the source snapshot")
        if not saved["next_page_token"]:
            raise ServiceError("no_next_page", "This snapshot has no next page")
        if saved["page"] >= 10:
            raise ServiceError("page_limit", "At most 10 pages per search chain; narrow the query")
        return self._search(saved["query"], saved["next_page_token"], search_artifact_id, saved["page"] + 1)

    def get_trial(self, identifier):
        identifier = nct_id(identifier)
        url = BASE + "/" + identifier
        raw, body = self._get(url)
        study = self._normalize(body)
        if study["nct_id"] != identifier:
            raise invalid("Retrieved trial ID does not match the request")
        artifact = self.store._save("trial_detail", {"response.json": raw, "trials.json": json_bytes({"studies": [study]})},
                                   self._provenance(url, raw, nct_id=identifier))
        return {"artifact": artifact, "trial": study, "raw_record_uri": f"biostat://artifacts/{artifact['artifact_id']}/trial-record",
                "notice": NOTICE}

    def _normalize(self, body):
        study = normalize(body)
        if self.demo:
            # Test IDs may exist in the real registry; never link a fixture to them.
            study["source_url"] = None
        return study

    def _provenance(self, url, raw, **extra):
        return {"provider": "Synthetic trial fixture" if self.demo else "ClinicalTrials.gov API v2",
                "synthetic": self.demo, "source_url": "package://biostat_mcp/data/trials-demo.json" if self.demo else url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "response_sha256": digest(raw), **extra}

    def _load(self, identifier, kinds):
        manifest = self.store._manifest(identifier)
        if manifest["kind"] not in kinds:
            raise ServiceError("wrong_artifact_type", "Expected a saved trial search or detail")
        self.store._read(identifier, "response.json")
        saved = json.loads(self.store._read(identifier, "trials.json"))
        return manifest, saved

    def read_record(self, identifier):
        self._load(identifier, {"trial_search", "trial_detail"})
        return self.store._read(identifier, "response.json").decode()

    def compare_trials(self, artifact_ids):
        if not isinstance(artifact_ids, list) or not 1 <= len(artifact_ids) <= 10:
            raise ServiceError("invalid_request", "Supply 1–10 trial search/detail artifact IDs")
        unique, inputs, duplicates, modes = {}, [], 0, set()
        for identifier in dict.fromkeys(artifact_ids):
            manifest, saved = self._load(identifier, {"trial_search", "trial_detail"})
            modes.add(manifest["synthetic"])
            inputs.append({"artifact_id": identifier, "response_sha256": manifest["response_sha256"],
                           "retrieved_at": manifest["retrieved_at"], "source_url": manifest["source_url"],
                           "query": manifest.get("query"), "page": manifest.get("page"),
                           "has_next_page": manifest.get("has_next_page"), "total_count": manifest.get("total_count")})
            for study in saved["studies"]:
                key = study["nct_id"]
                if key in unique:
                    if unique[key] != study:
                        raise ServiceError("snapshot_conflict", f"Conflicting snapshots for {key}; select one version")
                    duplicates += 1
                unique[key] = study
        if len(modes) > 1:
            raise ServiceError("invalid_request", "Do not mix synthetic and live records")
        if not unique:
            raise ServiceError("no_trials", "No trials in the selected snapshots")
        if len(unique) > 100:
            raise ServiceError("size_limit", "Compare at most 100 unique trials")
        studies = [unique[key] for key in sorted(unique)]
        counts = dict(sorted(Counter(s["overall_status"] or "NOT_REPORTED" for s in studies).items()))
        scope = f"Selected snapshots only: {len(studies)} unique trials; not a registry-wide distribution."
        summary = {"studies": studies, "status_counts": counts, "inputs": inputs,
                   "duplicates_removed": duplicates, "scope": scope, "notice": NOTICE, "synthetic": True in modes}
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(studies[0]))
        writer.writeheader()
        for study in studies:
            row = {}
            for key, value in study.items():
                cell = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else ("" if value is None else str(value))
                # Escape spreadsheet formulas; canonical JSON preserves the original text.
                row[key] = "'" + cell if cell.lstrip().startswith(("=", "+", "-", "@")) else cell
            writer.writerow(row)
        def md(value):
            return str(value if value is not None else "Not reported").replace("&", "&amp;").replace("<", "&lt;").replace("|", "&#124;").replace("\n", " ")
        lines = ["# Trial comparison", "", "SYNTHETIC FIXTURE" if True in modes else "ClinicalTrials.gov registry snapshots", "", scope, "", NOTICE, "",
                 "| Trial | Status | Phase | Enrollment (type) | Results posted |", "|---|---|---|---|---|"]
        for s in studies:
            enrollment = s["enrollment"]
            label = s["nct_id"] if True in modes else f"[{s['nct_id']}]({s['source_url']})"
            lines.append(f"| {label} | {md(s['overall_status'])} | {md(', '.join(s['phases']) or None)} | {md(enrollment.get('count'))} ({md(enrollment.get('type'))}) | {md(s['has_results'])} |")
        lines += ["", "Full titles, design, eligibility, primary outcomes, locations and provenance are preserved in comparison.json and comparison.csv.",
                  "Missing values mean not reported; unknown results availability is not converted to false."]
        spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "width": 580, "height": {"step": 34},
                "title": {"text": "Recruitment status — selected trial snapshots",
                          "subtitle": [("Synthetic demo | " if True in modes else "") + f"n={len(studies)} unique trials; not all registry matches",
                                       "Retrieved " + max(i["retrieved_at"] for i in inputs)[:10] + " (UTC)"]},
                "data": {"values": [{"status": k.replace("_", " "), "count": v} for k, v in counts.items()]},
                "mark": "bar", "encoding": {"y": {"field": "status", "type": "nominal", "title": None, "sort": "-x"},
                "x": {"field": "count", "type": "quantitative", "title": "Number of trials", "axis": {"tickMinStep": 1}}}}
        try:
            import vl_convert as vlc
        except ImportError as exc:
            raise ServiceError("missing_dependency", "Install .[mcp] to render comparison figures") from exc
        try:
            svg = vlc.vegalite_to_svg(spec, allowed_base_urls=[]).encode()
            png = vlc.vegalite_to_png(spec, allowed_base_urls=[])
        except Exception as exc:
            raise ServiceError("render_failed", "Trial comparison chart rendering failed") from exc
        artifact = self.store._save("trial_comparison", {"comparison.json": json_bytes(summary),
                    "comparison.csv": output.getvalue().encode(), "comparison.md": ("\n".join(lines) + "\n").encode(),
                    "chart.vl.json": json_bytes(spec), "figure.svg": svg, "figure.png": png},
                    {"inputs": inputs, "unique_trials": len(studies), "duplicates_removed": duplicates,
                     "synthetic": True in modes, "scope": scope, "renderer_version": vlc.__version__})
        return {"artifact": artifact, "status_counts": counts, "scope": scope,
                "comparison_uri": f"biostat://artifacts/{artifact['artifact_id']}/trial-comparison", "notice": NOTICE}

    def read_comparison(self, identifier):
        if self.store._manifest(identifier)["kind"] != "trial_comparison":
            raise ServiceError("wrong_artifact_type", "Expected a trial comparison artifact")
        return self.store._read(identifier, "comparison.json").decode()
