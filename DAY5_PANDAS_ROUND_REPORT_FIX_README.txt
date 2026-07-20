# Day-5 Pandas report rounding fix

This fixes:

TypeError: Expected numeric dtype, got object instead.

Reason:
The Day-5 run completed the experiment but crashed while writing the selected stress row into Markdown. The row contains both text and numbers, and `Series.round()` fails on mixed object dtype.

Install:
1. Extract this ZIP directly inside:
   E:\VS Code\O+E+S+C+L
2. Allow replace/merge.
3. Re-run:
   python main.py --config config/day5_optica_evidence_config.yaml --mode day5

Manual fix:
Open:
src\oescl\day5.py

Find:
lines.append(sel.round(6).to_frame().T.to_markdown(index=False))

Replace with:
sel_df = pd.DataFrame([sel.to_dict()])
lines.append(sel_df.round(6).to_markdown(index=False))

Keep the indentation inside the `_write_reports` function.
