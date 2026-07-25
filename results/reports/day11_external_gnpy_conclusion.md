# Day-11 External GNPy Reference Conclusion

Day-11 generated an independent GNPy reference for the accepted Day-10 C-band case.

## Case

- Scenario: C
- Band: C
- Spans: 10
- Span length: 80 km
- Launch power: +2 dBm
- Baud rate: 64 GBd
- Channel spacing: 75 GHz
- Center wavelength: 1550 nm
- Spectrum: 9 C-band channels centered at 1550 nm

## Result

- GNPy reference GSNR: 18.780000 dB
- O-E-S-C-L uniform GSNR: 12.863055 dB
- Error: -5.916945 dB
- External RMSE: 5.916945 dB

## Decision

The Day-10 external reference gate does not pass. The result must not be reported as formal GNPy validation.

The correct interpretation is that Day-10 supports internal repeated-seed symbol-count convergence for the C-band PCS gain, while Day-11 shows that absolute GSNR alignment against GNPy is still incomplete.

## Next Step

Proceed to Day-12 external alignment sweep across multiple C-band span counts to determine whether the GNPy mismatch is a nearly constant conservative offset or a span-dependent modeling error.
