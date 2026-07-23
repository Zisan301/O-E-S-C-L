import pandas as pd
from pathlib import Path

candidates = [
    Path("results/tables/day15_cs_primary_holdout_predictions.csv"),
    Path("results/tables/day15_cs_predictions.csv"),
    Path("results/tables/day15_cs_external_reference.csv"),
    Path("results/tables/day8_raw_band_metrics.csv"),
]

required = ["launch_power_dbm", "spans", "oesc_uniform_gsnr_mean_db"]

src = None
df = None

for p in candidates:
    if not p.exists():
        continue

    temp = pd.read_csv(p)
    print("\nChecking:", p)
    print("Columns:", list(temp.columns))

    if all(c in temp.columns for c in required):
        src = p
        df = temp
        break

if src is None:
    raise RuntimeError(
        "No table found with required OESC columns: "
        + ", ".join(required)
    )

print("\nUsing source:", src)

df["launch_power_dbm"] = pd.to_numeric(df["launch_power_dbm"], errors="coerce")
df["spans"] = pd.to_numeric(df["spans"], errors="coerce")
df["oesc_uniform_gsnr_mean_db"] = pd.to_numeric(df["oesc_uniform_gsnr_mean_db"], errors="coerce")

if "oesc_uniform_gsnr_std_db" not in df.columns:
    df["oesc_uniform_gsnr_std_db"] = ""
if "n_seeds" not in df.columns:
    df["n_seeds"] = ""
if "scenario_group" not in df.columns:
    df["scenario_group"] = "C+S"
if "band" not in df.columns:
    df["band"] = "C+S"

# Keep only Day-16 C+S validation cases
df = df[
    (df["launch_power_dbm"].isin([-2, 0, 2, 4])) &
    (df["spans"] == 12)
].copy()

df["scenario_group"] = "C+S"
df["band"] = "C+S"

cols = [
    "launch_power_dbm",
    "spans",
    "oesc_uniform_gsnr_mean_db",
    "oesc_uniform_gsnr_std_db",
    "n_seeds",
    "scenario_group",
    "band"
]

out = Path("results/tables/day16_cs_oesc_source.csv")
out.parent.mkdir(parents=True, exist_ok=True)

clean = (
    df[cols]
    .dropna(subset=["launch_power_dbm", "spans", "oesc_uniform_gsnr_mean_db"])
    .drop_duplicates("launch_power_dbm")
    .sort_values("launch_power_dbm")
)

if len(clean) != 4:
    raise RuntimeError(f"Expected 4 OESC C+S rows, got {len(clean)}")

clean.to_csv(out, index=False)

print("\nCreated:", out)
print(clean)
