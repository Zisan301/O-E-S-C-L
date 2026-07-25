from __future__ import annotations


Number = float | int


def achievable_rate_tbps(
    bmd_gmi_bits_per_symbol: Number | None = None,
    baud_rate_gbaud: Number | None = None,
    polarizations: int = 2,
    **aliases,
) -> float:
    """Return information-theoretic achievable information rate in Tb/s.

    This is the correct publication-facing rate quantity when FEC rate,
    distribution-matcher loss, pilot overhead, framing overhead, and other
    implementation overheads are not explicitly modeled.

    AIR = R_BMD * R_s * N_pol.

    The ``bmd_gmi`` keyword is accepted as a convenience alias because several
    publication scripts use that shorter name internally.
    """
    if bmd_gmi_bits_per_symbol is None:
        bmd_gmi_bits_per_symbol = aliases.pop("bmd_gmi", None)
    if aliases:
        unknown = ", ".join(sorted(aliases))
        raise TypeError(f"Unexpected keyword argument(s): {unknown}")
    if bmd_gmi_bits_per_symbol is None:
        raise TypeError("bmd_gmi_bits_per_symbol is required.")
    if baud_rate_gbaud is None:
        raise TypeError("baud_rate_gbaud is required.")

    bmd_gmi_value = float(bmd_gmi_bits_per_symbol)
    baud_rate_value = float(baud_rate_gbaud)

    if baud_rate_value <= 0:
        raise ValueError("baud_rate_gbaud must be positive.")
    if polarizations <= 0:
        raise ValueError("polarizations must be positive.")
    if bmd_gmi_value < 0:
        raise ValueError("bmd_gmi_bits_per_symbol must be non-negative.")

    return float(
        bmd_gmi_value
        * baud_rate_value
        * 1e9
        * int(polarizations)
        / 1e12
    )


def achievable_rate_gain_tbps(
    pcs_bmd_gmi_bits_per_symbol: Number,
    uniform_bmd_gmi_bits_per_symbol: Number,
    baud_rate_gbaud: Number,
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
