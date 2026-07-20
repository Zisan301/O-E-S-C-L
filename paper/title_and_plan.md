# Proposed conference paper title

**A Reproducible Simulation Framework for Joint Probabilistic Shaping and Lightweight Neural NLI Mitigation in Multi-Band O/E/S/C/L Optical Links**

## Core conference-level contribution points

1. **Problem**
   - Multi-band O/E/S/C/L optical systems can increase usable spectrum, but nonlinear interference, amplified-spontaneous-emission noise, and band-dependent impairments reduce achievable information rate.

2. **Gap**
   - Many studies report optimistic capacity numbers without enough validation gates, reproducibility scripts, or ablation baselines.

3. **Proposed idea**
   - Combine probabilistic constellation shaping with a lightweight neural residual NLI compensator and evaluate the combination under a reproducible multi-band simulation framework.

4. **Baselines**
   - Uniform signalling
   - PCS only
   - neural NLI mitigation only
   - proposed PCS + neural NLI mitigation

5. **Metrics**
   - GSNR
   - estimated pre-FEC BER
   - GMI / NGMI
   - net achievable rate
   - inference latency
   - model complexity

6. **Figures**
   - O/E/S/C/L system architecture
   - band/channel allocation
   - GSNR comparison
   - BER comparison
   - NGMI/GMI comparison
   - achievable-rate comparison
   - complexity/performance trade-off

7. **Claims to use**
   - "The proposed simulation framework improves reproducibility and provides validation-aware rate estimation."
   - "The joint PCS + neural NLI approach improves estimated NGMI and rate compared with unshaped uniform transmission in the simulated setting."
   - "The framework is suitable for preliminary conference/workshop evaluation."

8. **Claims to avoid**
   - Do not claim confirmed 485 Tb/s capacity.
   - Do not claim experimental validation.
   - Do not claim Q2/Q3 journal readiness without stronger external validation.
