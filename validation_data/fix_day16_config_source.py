from pathlib import Path

cfg = Path("config/day16_cs_full_raman_isrs_config.yaml")
text = cfg.read_text(encoding="utf-8")

old_new_pairs = [
    (
        "results/tables/day8_raw_band_metrics.csv",
        "results/tables/day16_cs_oesc_source.csv"
    ),
    (
        "results/tables/day15_cs_external_reference.csv",
        "results/tables/day16_cs_oesc_source.csv"
    ),
]

for old, new in old_new_pairs:
    text = text.replace(old, new)

cfg.write_text(text, encoding="utf-8")
print("Updated Day-16 config source table.")
