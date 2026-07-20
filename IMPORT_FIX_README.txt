WHY YOU GOT THIS ERROR:
ModuleNotFoundError: No module named 'src.oescl'

It means main.py exists in your project root, but the folder below is missing from the SAME root:

src/oescl/

CORRECT STRUCTURE:
O+E+S+C+L/
  main.py
  requirements.txt
  config/
    conference_config.yaml
  src/
    __init__.py
    oescl/
      __init__.py
      config.py
      channel.py
      constellation.py
      experiments.py
      metrics.py
      neural_nli.py
      pcs.py
      plots.py
      reporting.py
      utils.py
      validation.py

HOW TO FIX:
1. Delete or ignore the previous nested extracted folder.
2. Extract this ZIP directly inside:
   E:\VS Code\O+E+S+C+L
3. Confirm that this file exists:
   E:\VS Code\O+E+S+C+L\src\oescl\config.py
4. Run:
   pip install -r requirements.txt
   python main.py --config config/conference_config.yaml --mode smoke
   python main.py --config config/conference_config.yaml --mode full