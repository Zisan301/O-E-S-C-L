# Day-16 C+S Topology Verification

## Final topology decision

The existing Day-16 reference CSV states that the C+S GNPy reference was generated using ordinary Fiber with Raman/SRS simulation parameters enabled, not pump-amplified RamanFiber.

Therefore, the correct project claim is:

> The Day-16 C+S benchmark uses an ordinary Fiber topology with GNPy Raman/SRS simulation parameters enabled. It must not be described as a valid RamanFiber pump-amplified topology.

## Original Day-16 reference rows


scenario_group band spans launch_power_dbm reference_model reference_source                           reference_gsnr_db
-------------- ---- ----- ---------------- --------------- ----------------                           -----------------
C+S            C+S  12    -2               GNPy Raman/ISRS GNPy local Day-16 Raman/SRS sim_params run 11.29            
C+S            C+S  12    0                GNPy Raman/ISRS GNPy local Day-16 Raman/SRS sim_params run 12.91            
C+S            C+S  12    2                GNPy Raman/ISRS GNPy local Day-16 Raman/SRS sim_params run 13.8             
C+S            C+S  12    4                GNPy Raman/ISRS GNPy local Day-16 Raman/SRS sim_params run 12.95            




## RamanFiber attempt

A generated RamanFiber topology failed before transmission calculation with this GNPy error:

Invalid network definition: Fiber element uid:fiber_CS_1 defined as RamanFiber without operational parameters

Conclusion: the current RamanFiber network is invalid because required RamanFiber operational parameters are missing.

## Regular Fiber rerun status

A regular Fiber rerun was started locally, but the existing committed Day-16 reference already contains the needed provenance note and GSNR values.

## Required manuscript/project wording

Use:

ordinary Fiber topology with perturbative Raman/SRS-enabled GNPy simulation settings

Avoid:

pump-amplified RamanFiber validation
valid RamanFiber topology
full RamanFiber experiment
