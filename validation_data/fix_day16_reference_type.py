import pandas as pd
from pathlib import Path

csv_path = Path("validation_data/gnpy_day16_cs_raman_reference.csv")

rows = [
    {
        "scenario_group": "C+S",
        "band": "C+S",
        "spans": 12,
        "launch_power_dbm": -2,
        "reference_model": "GNPy Raman/ISRS",
        "reference_source": "GNPy local Day-16 Raman/SRS sim_params run",
        "reference_gsnr_db": 11.29,
        "reference_type": "gnpy_full_raman_isrs",
        "status": "ok",
        "notes": "C+S GNPy reference using Fiber with Raman/SRS sim_params enabled; not RamanFiber pump-amplified"
    },
    {
        "scenario_group": "C+S",
        "band": "C+S",
        "spans": 12,
        "launch_power_dbm": 0,
        "reference_model": "GNPy Raman/ISRS",
        "reference_source": "GNPy local Day-16 Raman/SRS sim_params run",
        "reference_gsnr_db": 12.91,
        "reference_type": "gnpy_full_raman_isrs",
        "status": "ok",
        "notes": "C+S GNPy reference using Fiber with Raman/SRS sim_params enabled; not RamanFiber pump-amplified"
    },
    {
        "scenario_group": "C+S",
        "band": "C+S",
        "spans": 12,
        "launch_power_dbm": 2,
        "reference_model": "GNPy Raman/ISRS",
        "reference_source": "GNPy local Day-16 Raman/SRS sim_params run",
        "reference_gsnr_db": 13.80,
        "reference_type": "gnpy_full_raman_isrs",
        "status": "ok",
        "notes": "C+S GNPy reference using Fiber with Raman/SRS sim_params enabled; not RamanFiber pump-amplified"
    },
    {
        "scenario_group": "C+S",
        "band": "C+S",
        "spans": 12,
        "launch_power_dbm": 4,
        "reference_model": "GNPy Raman/ISRS",
        "reference_source": "GNPy local Day-16 Raman/SRS sim_params run",
        "reference_gsnr_db": 12.95,
        "reference_type": "gnpy_full_raman_isrs",
        "status": "ok",
        "notes": "C+S GNPy reference using Fiber with Raman/SRS sim_params enabled; not RamanFiber pump-amplified"
    },
]

df = pd.DataFrame(rows)
df.to_csv(csv_path, index=False)
print(f"Fixed {csv_path}")
print(df)
