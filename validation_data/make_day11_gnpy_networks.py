import json
from pathlib import Path

out = Path("validation_data")
out.mkdir(exist_ok=True)

def loc(city, x):
    return {
        "location": {
            "city": city,
            "region": "",
            "latitude": float(x),
            "longitude": 0.0
        }
    }

def make_network(filename, band, spans, loss_coef):
    elements = []
    connections = []

    tx = "trx_A"
    rx = "trx_B"

    elements.append({
        "uid": tx,
        "type": "Transceiver",
        "metadata": loc("Site_A", 0)
    })

    previous = tx

    span_loss = float(loss_coef) * 80.0

    for i in range(1, spans + 1):
        fiber_uid = f"fiber_{band}_{i}"
        edfa_uid = f"edfa_{band}_{i}"

        elements.append({
            "uid": fiber_uid,
            "type": "Fiber",
            "type_variety": "SSMF",
            "params": {
                "length": 80,
                "length_units": "km",
                "loss_coef": float(loss_coef),
                "con_in": 0,
                "con_out": 0
            },
            "metadata": loc(f"Span_{i}", i)
        })

        elements.append({
            "uid": edfa_uid,
            "type": "Edfa",
            "type_variety": "std_medium_gain",
            "operational": {
                "gain_target": span_loss,
                "tilt_target": 0,
                "out_voa": 0
            },
            "metadata": loc(f"EDFA_{i}", i + 0.1)
        })

        connections.append({"from_node": previous, "to_node": fiber_uid})
        connections.append({"from_node": fiber_uid, "to_node": edfa_uid})
        previous = edfa_uid

    elements.append({
        "uid": rx,
        "type": "Transceiver",
        "metadata": loc("Site_B", spans + 1)
    })

    connections.append({"from_node": previous, "to_node": rx})

    network = {
        "network_name": f"O-E-S-C-L Day11 {band} band external validation",
        "elements": elements,
        "connections": connections
    }

    path = out / filename
    path.write_text(json.dumps(network, indent=2), encoding="utf-8")
    print(f"Created {path}")

make_network("gnpy_C_10span_network.json", "C", 10, 0.19)
make_network("gnpy_S_12span_network.json", "S", 12, 0.22)
