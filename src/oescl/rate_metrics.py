from __future__ import annotations


def achievable_rate_tbps(
    bmd_gmi_bits_per_symbol: float,
    baud_rate_gbaud: float,
    polarizations: int = 2,
) -> float:
    """Return information-theoretic achievable information rate in Tb/s.

    This is the correct publication-facing rate quantity when FEC rate,
    distribution-matcher loss, pilot overhead, framing overhead, and other
    implementation overheads are not explicitly modeled.

    AIR = R_BMD * R_s * N_pol.
    """
    if baud_rate_gbaud <= 0:
        raise ValueError("baud_rate_gbaud must be positive.")
    if polarizations <= 0:
        raise ValueError("polarizations must be positive.")
    if bmd_gmi_bits_per_symbol < 0:
        raise ValueError("bmd_gmi_bits_per_symbol must be non-negative.")

    return float(
        bmd_gmi_bits_per_symbol
        * baud_rate_gbaud
        * 1e9
        * int(polarizations)
        / 1e12
    )


def achievable_rate_gain_tbps(
    pcs_bmd_gmi_bits_per_symbol: float,
    uniform_bmd_gmi_bits_per_symbol: float,
    baud_rate_gbaud: float,
    polarizations: int = 2,
) -> float:
    """Return PCS-minus-uniform AIR gain in Tb/s."""
    pcs_air = achievable_rate_tbps(
        pcs_bmd_gmi_bits_per_symbol,
        baud_rate_gbaud,
        polarizations,
    )
    uniform_air = achievable_rate_tbps(
        uniform_bmd_gmi_bits_per_symbol,
        baud_rate_gbaud,
        polarizations,
    )
    return float(pcs_air - uniform_air)
