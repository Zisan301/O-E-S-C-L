# Day-4 seed syntax clean fix

This fixes the SyntaxError caused by a literal `\n` being inserted into:

src\oescl\day4_calibration.py

Install:
1. Extract this ZIP directly inside:
   E:\VS Code\O+E+S+C+L
2. Allow replace/merge.
3. Re-run:
   python main.py --config config/day4_calibrated_config.yaml --mode day4cal

Manual fix:
Open:
src\oescl\day4_calibration.py

Find the broken line containing:
\n                rng = np.random.default_rng(rng_seed)

Replace the broken part with two real Python lines:

rng_seed = int(seed * 100000 + (power + 100.0) * 1000 + len(regime) * 17)
rng = np.random.default_rng(rng_seed)

Make sure the second line has the same indentation level as the first line inside the loop.
