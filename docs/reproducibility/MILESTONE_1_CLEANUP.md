# Milestone 1 Reproducibility Cleanup

Date: 2026-08-02 22:41:18 +06:00

Baseline commit before cleanup:

f5b8786e667191d384bf632f4e1d5ccba03e3e58

This cleanup starts the publication-grade improvement branch.

Actions:
- Preserved a local baseline backup under the ignored baseline directory.
- Added .gitignore.
- Audited virtual environments, Python cache files, compiled binaries, and generated model artifacts from Git tracking.
- Did not remove local working files.
- Did not rewrite Git history yet.

Next scientific fixes:
1. Resolve Day-16 Fiber vs RamanFiber topology.
2. Centralize entropy-corrected BMD metrics.
3. Replace simplified C+S stress penalty with ISRS-aware C+S modelling.
4. Expand GNPy validation and confirmation runs.
