# CPTAC ccRCC paired RNA/protein exploratory report

72 matched ccRCC cases; 8,219 proteins at BH q < 0.05 (4,491 higher, 3,728 lower in tumor).

CA9 and NNMT are higher in tumor in both layers; MTOR total abundance is lower in both, without establishing reduced pathway activity. VEGFA RNA is higher, but its protein has only one finite pair and is not testable. NDUFA4L2 (current UniProt COXFA4L2) is higher and MT1H lower in both layers; these were selected exploratorily.

Among 9,475 genes tested in both layers, 76.0% have the same estimated direction (descriptive Spearman ρ=0.697). Restricting each gene to the exact same finite cases in all four matrices gives 76.1% agreement across 9,475 genes.

## Cohort and method

Primary analysis uses the intersection of four assay case sets after excluding seven non-ccRCC cases by authoritative histology and the contaminated C3N-00314 normal specimen. Its tumor remains eligible in the inventory. 72 common cases contribute; each gene uses only its finite tumor/normal pairs. No extra log transformation or imputation. For n ≥ 20, Δ is the arithmetic mean of paired differences, SE = SD(d)/√n, nominal 95% CI = Δ ± t(0.975,n−1)×SE, and a two-sided paired t test addresses mean difference zero. BH correction uses all successfully tested genes separately within protein and RNA. Genes with fewer than 20 pairs, zero paired variance, or nonfinite failures have no p/q/CI and explicit status; descriptive means remain available. Nominal CIs are not simultaneous or adjusted for shortlist selection.

Download: 110 tumors, 84 protein normals, 75 RNA normals. After exclusions: 80 protein pairs and 72 RNA pairs; primary common cohort 72. All nine file hashes/sizes verified against input/manifest.json. The workbook contamination note and specimen mapping were checked.

## Shortlist

Among non-prespecified protein genes with n >= 90% of common cohort and q < 0.05, select two largest absolute protein mean differences; ties alphabetical. RNA does not determine selection.

| Gene | Layer | n | Mean Δ | 95% CI | p | BH q | Status |
|---|---|---:|---:|---|---:|---:|---|
| CA9 | protein | 72 | 2.34 | 2.18, 2.51 | 6.21e-41 | 1.68e-38 | tested |
| NNMT | protein | 72 | 2.78 | 2.59, 2.98 | 5.85e-41 | 1.68e-38 | tested |
| VEGFA | protein | 1 | 1.07 | —, — | — | — | insufficient_pairs |
| MTOR | protein | 72 | -0.175 | -0.212, -0.137 | 5.44e-14 | 1.62e-13 | tested |
| NDUFA4L2 | protein | 72 | 3.91 | 3.69, 4.13 | 4.77e-47 | 4.79e-43 | tested |
| MT1H | protein | 72 | -3.18 | -3.51, -2.85 | 4.49e-30 | 6.84e-29 | tested |
| CA9 | rna | 72 | 6.45 | 6.2, 6.71 | 2e-57 | 1.23e-54 | tested |
| NNMT | rna | 72 | 4.74 | 4.42, 5.06 | 6.84e-42 | 5.68e-40 | tested |
| VEGFA | rna | 72 | 3.01 | 2.78, 3.24 | 3.41e-38 | 1.53e-36 | tested |
| MTOR | rna | 72 | -0.778 | -0.844, -0.713 | 1.99e-35 | 5.91e-34 | tested |
| NDUFA4L2 | rna | 72 | 6.91 | 6.66, 7.16 | 2.86e-60 | 3.02e-57 | tested |
| MT1H | rna | 72 | -5.39 | -5.84, -4.93 | 2.86e-35 | 8.28e-34 | tested |

Protein Δ is on processed TMT log2 reference-ratio scale; RNA Δ is on supplied log2 FPKM scale.

## Research evidence

**CA9** — Strong tissue-contrast research candidate; separate imaging/biology from therapy. ARISER: 864 randomized patients; no significant DFS advantage (HR 0.97, 95% CI 0.79–1.18) or OS advantage (HR 0.99, 0.74–1.32) for adjuvant girentuximab. This independent trial limits therapeutic extrapolation; it does not negate differential expression.
[Adjuvant Weekly Girentuximab Following Nephrectomy for High-Risk Renal Cell Carcinoma: The ARISER Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/27787547/) (PMID 27787547).
**NNMT** — Prioritize metabolic biology and orthogonal tissue validation. Kim et al. 2025: a separate 14-patient paired RNA study reported NNMT upregulation, with knockdown experiments in SNU1272/Caki-1 cells. TCGA survival analysis is a separate secondary component. This supports biological follow-up, not validated prognosis or human efficacy. Wang et al. 2026 report NNMT/FN1 experiments and clinical specimens; independence of their reused multiomics data from CPTAC is not established from the abstract.
[Prognostic and Therapeutic Potential of Nicotinamide N-Methyltransferase and Hypoxia Inducible Lipid Droplet Associated in Clear Cell Renal Cell Carcinoma.](https://pubmed.ncbi.nlm.nih.gov/41399267/) (PMID 41399267).
[Nicotinamide N-Methyltransferase Epigenetically Activates Fibronectin 1 Through H3K9me3 Remodeling in Clear Cell Renal Cell Carcinoma.](https://pubmed.ncbi.nlm.nih.gov/42440812/) (PMID 42440812).
**VEGFA** — RNA upregulation; protein is untestable (only one finite pair), so protein prioritization is unsupported here. No independent VEGFA-specific outcome study retrieved in this bounded search. Live pathway/target annotations support context only.
**MTOR** — Pathway-context comparator; total abundance is not kinase activity. No independent MTOR-specific outcome study retrieved in this bounded search. Protein abundance alone cannot establish pathway activation or drug sensitivity.
**NDUFA4L2** — Large concordant upward contrast; current UniProt symbol is COXFA4L2 (legacy matrix symbol NDUFA4L2), accession Q9NRX3. No Reactome pathways returned; this is not evidence of no pathway membership. No candidate-specific independent literature retrieved in bounded search; annotation is not validation.
**MT1H** — Large concordant downward contrast; metal-binding annotation supports a tissue-biology hypothesis, not therapeutic targeting. No candidate-specific independent literature retrieved in bounded search; annotation is not validation.

Live UniProt identifiers/pathways and Open Targets records for CA9, VEGFA and MTOR are in evidence_records.json. Open Targets returns all-indication records (first 10); CA9 includes girentuximab and an iodine-124 imaging agent, VEGFA includes bevacizumab, and MTOR includes multiple investigational kinase inhibitors. Database stage labels are not jurisdiction/indication-specific approval statements. NNMT and the two exploratory candidates were not queried for drug records. Reactome annotations are not enrichment evidence.

## Limitations and follow-up

Missingness may depend on abundance and tissue (MNAR); the observed-pair mean need not represent unobserved values or all eligible cases. Common-assay selection further limits generalizability. Independent cases and sufficiently regular paired-difference means underpin t inference; pairing controls stable case characteristics but does not remove tissue composition, purity, processing or batch artifacts. TMT reference ratios can be compressed and are not directly calibrated to RNA log2 FPKM. No raw processing reconstruction or batch-adjusted model was performed. Adjacent tissue is not healthy-donor tissue. Gene dependence limits generic BH guarantees. Differences in significance do not test differences between RNA/protein effects; no cross-layer effect-equality test was performed. Direction discordance can reflect missingness, composition, processing and post-transcriptional regulation; it does not establish a mechanism. No enrichment test, causal claim, drug efficacy claim or clinical recommendation is made.

Independent evaluation is pending, with the controller blocked at evaluation. Same-session numerical and artifact checks do not confer scientific approval. Next: independent code/results review, investigate batch/purity and missingness, verify candidate expression orthogonally, and review full texts before translating prioritization.

Reproduce offline: `/tmp/biostat-rhc-analysis-env/bin/python analysis.py` then `/tmp/biostat-rhc-analysis-env/bin/python render_report.py`. Runtime code path is recorded in analysis.py. Read runtime_context.json and memory_retrieval.json before follow-up. Full aggregate tables are under tables/; raw evidence, dates, queries, URLs and checksums are under mcp_artifacts/ and source_index.json.

Examples with opposite directions and q < 0.05 in both layers (exploratory; not tests of layer-effect differences): NDUFS4, GYPA, GM2A, HBE1, TLR10. Full estimates: tables/discordant_examples.csv.
