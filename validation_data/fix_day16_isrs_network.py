import json
from pathlib import Path

src = Path("validation_data/gnpy_CS_12span_full_raman_network.json")
dst = Path("validation_data/gnpy_CS_12span_isrs_network.json")

data = json.loads(src.read_text(encoding="utf-8"))

changed = 0
for element in data.get("elements", []):
    if element.get("type") == "RamanFiber":
        element["type"] = "Fiber"
        element.pop("operational", None)
        changed += 1

data["network_name"] = data.get("network_name", "Day16 C+S ISRS network") + " - Fiber with Raman/ISRS sim_params"

dst.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Created {dst}")
print(f"Converted RamanFiber elements to Fiber: {changed}")
