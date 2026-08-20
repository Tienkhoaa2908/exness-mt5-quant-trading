# V33 multi-task neural diagnostic — accepted result

Date: 2026-08-20

Uploaded diagnostic ZIP SHA-256: `16db78c40543495c790d83019999169d566206a591cc4ec570c6b7056df8fefa`.

Protocol: causal expanding monthly training, labels only from trades whose exits precede calibration-month start, no reconstructed PnL.

12 OOS months / 4,845 rows. Mean chronological metrics:

- expected-R Spearman: `+0.0249`;
- MFE Spearman: `-0.0050`;
- adverse/MAE Spearman: `-0.0366`;
- giveback Spearman: `-0.0132`.

The entry snapshot therefore does not contain stable information sufficient to predict the future intra-trade path. Expected-R retains weak ranking information, but MFE/MAE/giveback heads do not justify an entry-snapshot neural exit controller.

Decision:

1. keep the V32 DeepMLP signal as a quality/risk input;
2. do not enlarge an entry-snapshot MLP to solve exit timing;
3. collect causal **intra-trade M15 sequences**: unrealized R, peak R, MAE, giveback, stop R, TP R, age plus causal market/tick state;
4. train GRU, causal TCN and Transformer only after path telemetry exists;
5. sequence-model metrics remain diagnostics; any selected policy must return to exact MT5 Strategy Tester for economics.

Candidate-level expected-R rank correlations are also weak and unstable; no candidate family demonstrates a robust entry-snapshot MFE/giveback model. This supports the V34/V35 architecture change toward independent alpha generation plus routing, rather than relying on a single larger neural predictor.
