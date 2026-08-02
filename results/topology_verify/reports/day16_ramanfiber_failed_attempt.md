# RamanFiber Failed Attempt

Status: failed before transmission calculation.

GNPy error:

Invalid network definition: Fiber element uid:fiber_CS_1 defined as RamanFiber without operational parameters

Interpretation:

The generated RamanFiber network is not a valid GNPy RamanFiber topology because required operational parameters are missing.
The final Day-16 claim should remain ordinary Fiber with Raman/SRS simulation parameters enabled.

Future improvement:

Implement a separate valid RamanFiber topology only after adding correct operational parameters required by GNPy.
