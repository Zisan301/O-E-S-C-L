# Day-4 negative seed fix

This fixes:

ValueError: expected non-negative integer

Reason:
The Day-4 calibration sweep used `seed + int(power * 10) + len(regime)`.
When launch power was negative, the generated seed could become negative.

Install:
1. Extract this ZIP directly inside:
   E:\VS Code\O+E+S+C+L
2. Allow replace/merge.
3. Re-run:
   python main.py --config config/day4_calibrated_config.yaml --mode day4cal

Manual fix:
Open:
src\oescl\day4_calibration.py

Find:
rng = np.random.default_rng(seed + int(power * 10) + len(regime))

Replace with:
rng_seed = int(seed * 100000 + (power + 100.0) * 1000 + len(regime) * 17)
rng = np.random.default_rng(rng_seed)
