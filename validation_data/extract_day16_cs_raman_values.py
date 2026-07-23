import re
from pathlib import Path
import pandas as pd

log_dir = Path("validation_data/gnpy_day16_cs_raman_logs")
csv_path = Path("validation_data/gnpy_day16_cs_raman_reference.csv")

power_from_name = {
    "cs_raman_-2dBm.log": -2.0,
    "cs_raman_0dBm.log": 0.0,
    "cs_raman_2dBm.log": 2.0,
    "cs_raman_4dBm.log": 4.0,
}

rows = []

for name, power in power_from_name.items():
    path = log_dir / name
    text = path.read_text(encoding="utf-8", errors="ignore")

    # Find the receiver block only
    m = re.search(
        r"Transceiver\s+trx_B(?P<body>.*?)(?:Transmission result|The GSNR per channel)",
        text,
        flags=re.S
    )

    if not m:
        print(f"Could not find trx_B block in {name}")
        gs = None
    else:
        body = m.group("body")
        g = re.search(r"GSNR\s+\(signal bw,\s*dB\):\s*([0-9.+-]+)", body)
        gs = float(g.group(1)) if g else None

    print(f"{name}: launch_power={power}, GSNR_signal_bw={gs}")

    rows.append({
        "scenario_group": "C+S",
        "band": "C+S",
        "spans": 12,
        "launch_power_dbm": power,
        "reference_model": "GNPy Raman/ISRS-enabled",
        "reference_source": "GNPy local Day-16 Raman/SRS sim_params run",
        "reference_gsnr_db": gs,
        "notes": "C+S GNPy reference using Fiber with Raman/SRS sim_params enabled; not RamanFiber pump-amplified"
    })

df = pd.DataFrame(rows)
df.to_csv(csv_path, index=False)
print(f"Updated {csv_path}")
print(df)
