# Follow-up state

The unit is the case, with tumor and normal-adjacent tissue paired by exact case identifier. Authoritative workbook-derived histology excludes seven non-ccRCC cases. The contaminated C3N-00314 normal (CPT0012090003) is excluded; its tumor remains in availability counts. The intersection of all four assays defines 72 cases. Per gene/layer, only pairs with both values finite are used. Genes require at least 20 such pairs. Mean differences, sample SD, two-sided paired t p-values and pointwise t 95% CIs use n−1 degrees of freedom. BH correction is separate for each layer’s valid tested family. Zero-variance differences retain their mean but have undefined CI/p/q and an explicit status; no automatic p=0 or p=1 assignment. T inference assumes independent cases and approximately normal sampling of the mean; CIs are not simultaneous or selection-adjusted. No outlier deletion, imputation or predictive split is used.

Up to two non-prespecified genes with protein q<0.05, >=90% finite pairs, RNA test available; rank descending absolute protein mean difference, tie by gene. No RNA direction or drug filter. CA9, NNMT, VEGFA and MTOR were prespecified by the user; NDUFA4L2 and MT1H are selected from these data and subject to winner’s curse. None of these selections has been independently validated as a tissue contrast in this analysis.

Verified fingerprint: ff08dba38c4df7e1f899b4ebecb713f6aa49d24cb074d9f9c30478a1e1571f0f. Main cohort n=72. Do not inspect other arms. No delegation, installs, MCP, runtime or SQLite used. No scientific approval claimed.

Read report.md, analysis_config.json, method_review.json, sources/evidence_records.json and sources/source_manifest.json first. Raw data remain unchanged. Rerun commands in report.md. Current results: protein tested 10033; RNA tested 19015; zero-variance RNA 260; VEGFA protein n=1. Historical NDUFA4L2 → COXFA4L2 mapping is explicit.

Next work: independent artifact review; verify full-text cohort independence for NNMT/NDUFA4L2; orthogonal assays; detailed batch/provenance audit; justify any MNAR sensitivity before implementing it. No clinical efficacy conclusion from expression.
