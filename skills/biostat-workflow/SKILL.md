---
name: biostat-workflow
description: Use the optional biostat-superpowers runtime for a biomedical analysis that needs executable lifecycle gates, persistent project decisions, MCP source provenance, or a comparison with an older skill-only analysis. Complements the biostatistics specialist skills.
---

# Biostatistics executable workflow

Use the existing `biostatistics` skill and its specialists for statistical policy. This skill adds runtime mechanics, not alternative statistical guidance. Jev is not installed or required.

## Locate the runtime

The recommended local installation is `~/.codex/biostat-superpowers-v2`, with Python at `.venv/bin/python` under that directory. A user-specified development checkout is also supported. Confirm its `biostat_workflow/` and `biostat_mcp/` directories exist. Read that checkout's `docs/modernization/WORKFLOW_CONTROLLER.md` for the state/result API, and `docs/modernization/REVIEWED_HANDOFF.md` before applying reviewed MCP handoffs. If no runtime is available, explain that the declarative skills still work and report that runtime execution is unavailable.

## Execute and record

- Define the goal, estimand, input checksum and run ID before estimation. Use the controller's typed state and `route`, `advance`, and `settle` functions for actual stage results. Do not fabricate completed prerequisites to fit an existing script.
- Execute the specialist's work in the host; the controller does not call an LLM or fit a model by itself. Record artifact paths/checksums and substantive evidence for each transition. A blocked causal-identification gate can coexist with a separately labeled exploratory associational reproduction; it must not be reported as a completed causal workflow.
- Keep durable project decisions in `MemoryStore` with explicit provenance and an accurately named confirming actor. Agent-authored notes are not user approvals. Retrieve only relevant records for the current goal/stage/input fingerprint. Do not store participant rows in decision memory.
- When MCP is available, use its actual tools for relevant source discovery, retrieval or visualization; do not invoke unrelated tools just to claim coverage. The source catalog is not a universal dataset downloader. Host retrieval of an unsupported dataset must be labeled as such.
- Reviewed handoff proposals do not approve themselves. Only apply an exact proposal through the host after the review/confirmation it represents actually occurred. Preserve source checks, audit records and input fingerprints. Do not claim approval by a human based only on a request to run an analysis.
- Honor no-progress, revision, iteration and budget stops. Save the terminal reason and remaining questions. Report an incomplete or escalated analysis honestly.

## Compare with an older analysis

Preserve the original script. Pin identical input bytes and record software versions, seeds and separate output directories. Distinguish unchanged-script reproduction, workflow instrumentation, and methodological revisions. Compare compatible estimands and list every changed analysis choice. Have `method-evaluation` review the artifacts. Compare model tokens/cost only when actual provider or host telemetry exists; context byte counts and statistical-compute timings do not measure LLM savings. A historical run using a different model is not a controlled experiment.

For installation and limitations see the runtime's `docs/modernization/INSTALL_V2.md` and `ROADMAP.md`.
