# Day-2 textwrap import fix

This fixes:

NameError: name 'textwrap' is not defined

Install:
1. Extract this ZIP directly inside your project root:
   E:\VS Code\O+E+S+C+L
2. Allow replace/merge.
3. Re-run:
   python main.py --config config/day2_ieee_optica_config.yaml --mode day2

Manual fix:
Open src\oescl\day2.py and add this line near the top:

import textwrap
