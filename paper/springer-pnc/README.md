# Springer Photonic Network Communications submission package

This folder is reserved for the Photonic Network Communications (Springer) journal submission version of the O-E-S-C-L manuscript.

## Manuscript direction

Title:

**Comparative Waveform-Level SSFM Evaluation of Probabilistic Shaping in C-, S-, and C+S-Band Coherent Optical Links**

## Safe claim

PCS gains are band- and operating-region-dependent. The study provides simulation-level C, S, and simplified C+S comparison with paired confidence intervals.

Do not claim:

- full Raman-calibrated WDM/ISRS validation;
- experimental validation;
- record capacity;
- universal PCS improvement.

## Journal-specific formatting target

Photonic Network Communications requires Springer LaTeX source, the `twocolumn` option, editable source files and a compiled PDF version. The full prepared package is in the downloadable artifact from ChatGPT and contains:

- `manuscript/main.tex` using Springer Nature `sn-jnl` style;
- `manuscript/references.bib`;
- `manuscript/figures/Fig1-Fig5`;
- supplementary CSV outputs;
- cover letter;
- submission checklist;
- preview PDF.

## Reproducibility command

```bash
python main.py --config config/day8_q3_band_comparison_config.yaml --mode day8
```

## Before submission

Replace placeholder author affiliations and emails, add ORCID IDs if available, verify all DOI metadata, and archive the code/data release with a persistent DOI if possible.
