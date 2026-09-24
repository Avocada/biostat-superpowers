# Paired CPTAC ccRCC exploratory analysis

72 paired ccRCC cases; 8,219 of 10,033 tested proteins have BH q < 0.05 (4,491 higher; 3,728 lower). RNA: 15,118 of 19,015 tested genes. Across 9,475 genes tested in both layers, 7,205 (76.0%) share effect direction; descriptive Spearman correlation of mean differences is 0.697.

CA9 and NNMT show substantial increases in both layers; NDUFA4L2 (current UniProt symbol COXFA4L2) is the strongest eligible exploratory protein increase, while MT1H shows a large decrease. MTOR total abundance decreases modestly in protein and also decreases in RNA; total abundance is not kinase activity. VEGFA RNA increases, but its protein estimate has only one finite pair and is not inferentially interpretable. Different RNA/protein significance does not test a difference between their effects, and their raw scales are not interchangeable. Opposite directions occur in 2,270 jointly tested genes, including 1,087 with q < 0.05 in both layers. Illustrative, post hoc examples with all 72 pairs are SLC4A1 (protein +1.651; RNA −4.153) and GM2A (protein −1.980; RNA +1.711). These separate-scale contrasts can reflect regulation, tissue composition, or processing; they do not identify a mechanism.

## Cohort and methods

The unit is the case, with tumor and normal-adjacent tissue paired by exact case identifier. Authoritative workbook-derived histology excludes seven non-ccRCC cases. The contaminated C3N-00314 normal (CPT0012090003) is excluded; its tumor remains in availability counts. The intersection of all four assays defines 72 cases. Per gene/layer, only pairs with both values finite are used. Genes require at least 20 such pairs. Mean differences, sample SD, two-sided paired t p-values and pointwise t 95% CIs use n−1 degrees of freedom. BH correction is separate for each layer’s valid tested family. Zero-variance differences retain their mean but have undefined CI/p/q and an explicit status; no automatic p=0 or p=1 assignment. T inference assumes independent cases and approximately normal sampling of the mean; CIs are not simultaneous or selection-adjusted. No outlier deletion, imputation or predictive split is used.

Protein: supplied processed TMT log2 reference ratios. RNA: supplied log2 FPKM. Seven histology exclusions leave 103 tumors; protein NAT 84 → 81 → 80, RNA NAT 75 → 73 → 72 after histology and contamination filters. Nine file SHA256 hashes, byte counts and combined manifest fingerprint verified.

## Shortlist

Up to two non-prespecified genes with protein q<0.05, >=90% finite pairs, RNA test available; rank descending absolute protein mean difference, tie by gene. No RNA direction or drug filter. CA9, NNMT, VEGFA and MTOR were prespecified by the user; NDUFA4L2 and MT1H are selected from these data and subject to winner’s curse. None of these selections has been independently validated as a tissue contrast in this analysis.

|Gene|Layer|n|Mean Δ|95% CI|BH q|
|---|---|---:|---:|---|---:|
|CA9|protein|72|2.34|2.18 to 2.51|1.68e-38|
|CA9|rna|72|6.45|6.2 to 6.71|1.23e-54|
|NNMT|protein|72|2.78|2.59 to 2.98|1.68e-38|
|NNMT|rna|72|4.74|4.42 to 5.06|5.68e-40|
|VEGFA|protein|1|1.07|— to —|—|
|VEGFA|rna|72|3.01|2.78 to 3.24|1.53e-36|
|MTOR|protein|72|-0.175|-0.212 to -0.137|1.62e-13|
|MTOR|rna|72|-0.778|-0.844 to -0.713|5.91e-34|
|NDUFA4L2|protein|72|3.91|3.69 to 4.13|4.79e-43|
|NDUFA4L2|rna|72|6.91|6.66 to 7.16|3.02e-57|
|MT1H|protein|72|-3.18|-3.51 to -2.85|6.84e-29|
|MT1H|rna|72|-5.39|-5.84 to -4.93|8.28e-34|

VEGFA protein has insufficient pairs; its descriptive mean is not a tested result.

## Evidence and prioritization

**CA9**: Prioritize orthogonal abundance/localization work. Large concordant increase; CAIX-targeted girentuximab literature supplies independent imaging evidence, not proof of therapeutic benefit.

**NNMT**: Prioritize metabolic and cell-type follow-up. Concordant increase and nicotinamide-related annotation. Retrieved mechanistic abstracts are supportive but their multiomics cohort overlap was not audited; do not label those components independent replication.

**VEGFA**: RNA-supported pathway candidate only: protein is effectively unavailable (n=1). VEGF-pathway trial evidence is independent, but receptor inhibitor efficacy does not validate VEGFA abundance as a response biomarker.

**MTOR**: Pathway benchmark rather than overexpression lead. Decreased total abundance does not establish pathway inactivity. Independent temsirolimus trial supports historical RCC pathway relevance, not efficacy inferred from these tissue values.

**NDUFA4L2**: Exploratory abundance lead; UniProt renamed it COXFA4L2. Retrieved renal cell/model literature motivates mechanistic work; observational cohort overlap is unverified. No tractability query performed for this target.

**MT1H**: Exploratory decrease suitable for orthogonal validation; examine metallothionein isoform specificity and cellular composition. No independent target-specific paper or tractability assessment in this bounded search.

[Temsirolimus, interferon alfa, or both for advanced renal-cell carcinoma.](https://pubmed.ncbi.nlm.nih.gov/17538086/) — Independent randomized trial, not CPTAC. 626 poor-prognosis metastatic RCC patients; temsirolimus versus interferon reported an overall-survival HR of 0.73 (95% CI 0.58–0.92). Historical trial context, not a recommendation or an abundance-response link.

[Sunitinib versus interferon alfa in metastatic renal-cell carcinoma.](https://pubmed.ncbi.nlm.nih.gov/17215529/) — Independent randomized trial, not CPTAC. 750 untreated metastatic RCC patients; sunitinib versus interferon reported progression-free-survival HR 0.42 (95% CI 0.32–0.54). Multi-target receptor inhibition provides pathway-level context, not direct validation of VEGFA protein or a ligand-specific effect.

[Performance of [&lt;sup&gt;89&lt;/sup&gt;Zr]girentuximab PET/CT in Predicting the Presence of Any Renal Malignancy: A Reanalysis of the ZIRCON Trial.](https://pubmed.ncbi.nlm.nih.gov/42025513/) — Independent of CPTAC; reanalysis of ZIRCON, not a new trial. CAIX-directed radiotracer study supports imaging/localization relevance. Reanalysis is not independent of the original ZIRCON trial; diagnostic performance is not drug efficacy.

[Nicotinamide N-Methyltransferase Epigenetically Activates Fibronectin 1 Through H3K9me3 Remodeling in Clear Cell Renal Cell Carcinoma.](https://pubmed.ncbi.nlm.nih.gov/42440812/) — Mechanistic abstract; cohort overlap unverified. Reports NNMT/FN1 experiments and clinical specimens. Functional model evidence is distinct from this association analysis; independent human tissue replication and drug selectivity were not established here.

[NDUFA4L2 acts as a mitochondrial checkpoint against ferroptosis in hypoxic clear cell renal cell carcinoma.](https://pubmed.ncbi.nlm.nih.gov/42331208/) — Mechanistic abstract; cohort overlap unverified. Reports knockdown/rescue, cell and in vivo work concerning ferroptosis. Supports research motivation; abstract-level evidence does not establish clinical benefit.

UniProt annotations obtained for all six targets; NDUFA4L2 resolved explicitly through its synonym to COXFA4L2. Open Targets assessed CA9, VEGFA and MTOR only. Stage labels and candidates span all indications and can include imaging agents or multi-target drugs; they are not jurisdiction-specific approvals or kidney efficacy. MTOR candidate rows omit temsirolimus in this snapshot; literature supplies its independent historical context. No enrichment claim. Original cohort: Clark et al., Cell 2019, PMID 31675502, is provenance rather than independent validation.

## Diagnostics and limitations

Protein missingness is 21.38% of tumor entries and 21.38% of normal entries across all 11,710 rows; 1,677 protein genes fail the 20-pair threshold. RNA entries are finite throughout, but 260 genes have zero-variance paired differences and are not tested. Paired protein completeness has median 72 and lower quartile 43. Complete RNA values do not imply complete biological detection. Same-finite-case cross-layer sensitivity yields 76.05% direction agreement among 9,482 genes with ≥20 joint finite pairs (includes seven constant RNA genes; denominator differs from tested-only comparison). Layer-specific protein sensitivity uses 80 pairs; shortlisted tested protein directions persist. Leave-one-pair-out means retain direction for all tested shortlist effects; bootstrap CIs and skewness diagnostics are in shortlist.csv. These checks do not solve MNAR or batch confounding.

These are exploratory tissue associations, not causal effects, treatment-response predictions or clinical advice. Adjacent tissue is not healthy-donor kidney. Cell composition, tumor purity, clinical heterogeneity and unmodeled processing/batch effects may explain differences. Pairing controls stable case characteristics but does not remove tissue-confounded technical effects. TMT reference ratios may show ratio compression; supplied RNA normalization and original processing are accepted, not reproduced. No extra log transform was applied. Protein missingness may depend on abundance (MNAR); available-pair results need not represent all 72 cases or all ccRCC. The common-assay cohort may be selected. Many significant genes can reflect broad tissue and technical differences. No enrichment analysis was performed; pathway annotations are not enrichment evidence.

Two initial Europe PMC searches returned HTTP 503; bounded replacement queries succeeded. A guessed PMID (17476008) resolved to an unrelated cardiac trial and was rejected after title/abstract checking; raw record retained for audit. MT1H lacks target-specific independent literature in this bounded review. Full-text cohort-overlap checks, explicit MNAR modeling, batch adjustment and independent artifact review remain unresolved.

## Reproduce

`/tmp/biostat-rhc-analysis-env/bin/python analysis.py` then `.../python supplement_evidence.py` (uses cached original and supplemental responses), then `.../python build_report.py`. No installs. Package versions and choices are in analysis_config.json; source bytes, request URLs, retrieval dates and SHA256 are in sources/. Full aggregate tables and PNGs are in outputs/. report.html embeds plots and data and works offline. Method review is same-agent only.
