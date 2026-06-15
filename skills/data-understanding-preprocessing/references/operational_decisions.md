# Data Provenance and Analysis Operations

Use this reference to record where the data came from, how it was derived, and what must be
saved for the analysis to be reproducible — and, for prediction models intended for real use,
how the model will be maintained. Reproducibility starts with knowing exactly what data you have.

## Data provenance

- **Source and version:** system of record (EHR, registry, claims, trial database, survey), the
  extract/query date, and a version or snapshot identifier. Data revised after extraction can
  silently change results.
- **Coding dictionaries:** the versioned code systems in use (ICD-9/10, SNOMED, LOINC, ATC/RxNorm,
  CPT) and any mapping tables, with their versions.
- **Derivation rules:** how derived variables were computed (e.g. eGFR formula, comorbidity
  index, BMI categories), including units and reference ranges.
- **Linkage:** keys used to join sources, join type, expected cardinality, and the allowed time
  direction of each join (no future information joined onto a baseline row).
- **Eligibility provenance:** the exact filters that produced the analysis cohort, in order, with
  counts (the attrition / participant-flow table).

## Reproducibility artifacts (save these)

- Raw data version or extract timestamp (never overwrite the raw extract).
- The analysis-table build script or query.
- The split manifest: which subjects/rows are in train / validation / test (or internal /
  external), with random seeds.
- The column-role manifest.
- The preprocessing pipeline artifact (the fitted `recipe` / `ColumnTransformer`).
- The fitted model object and its configuration.
- The analysis report and the exact definitions of every outcome and effect measure.
- An environment lockfile (`renv.lock` / `requirements.txt` / `sessionInfo()`).

## Maintenance — only for prediction models intended for ongoing use

A clinical prediction model that will be used prospectively (not a one-time inferential analysis)
needs a maintenance plan; an etiologic/inferential analysis usually does not.

- **Case-mix / distribution shift:** monitor whether the population the model sees drifts from the
  development population (new sites, new eras, changed coding).
- **Calibration drift:** monitor calibration-in-the-large and slope over time; recalibration is
  often needed before full refitting.
- **Update policy:** when to recalibrate vs refit, the validation design for an update, and
  whether imputers/encoders are refit or frozen.
- **Versioning:** version the model, the preprocessing pipeline, and the input contract together
  so a prediction can always be traced to the exact pipeline that produced it.

## Specification output

Record each decision as a requirement, not a note. Where known, name the artifact, script, or
owner that enforces it. Distinguish what is needed for *this analysis to be reproducible* from
what is needed for a *deployed model to stay valid*.
