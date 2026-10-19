# EDA report — Phase 3 (bmc-v1)

- rows: full 25416 (dropped 888 warmup/tail) | train 17784 / val 3816 / test 3816
- splits: train < 2025-02-10 <= val < 2025-07-19 <= test
- leakage: all lags/rolls shift(1)+ per ward; spot-check PASS; targets are future shifts
- corr w/ demand: {'demand_ml': 1.0, 'population': 0.984, 'density': 0.234, 'available_water_ml': -0.085, 'storage_pct': -0.078, 'lag_1': 0.991, 'lag_7': 0.99, 'roll_7': 0.994, 'roll_30': 0.993}
- seasonal mean demand ML: {'Monsoon': 130.607, 'PostMonsoon': 134.133, 'Summer': 145.779, 'Winter': 128.069}
- per-ward demand stats: {'mean': {'A': 48.136, 'B': 33.444, 'C': 43.532, 'D': 90.712, 'E': 103.383, 'F/N': 138.491, 'F/S': 94.801, 'G/N': 156.578, 'G/S': 98.859, 'H/E': 146.457, 'H/W': 81.491, 'K/E': 216.471, 'K/W': 197.504, 'L': 236.742, 'M/E': 211.99, 'M/W': 107.369, 'N': 162.766, 'P/N': 247.429, 'P/S': 121.9, 'R/C': 146.235, 'R/N': 113.169, 'R/S': 180.22, 'S': 194.327, 'T': 89.569}, 'std': {'A': 3.567, 'B': 2.522, 'C': 3.184, 'D': 6.818, 'E': 7.647, 'F/N': 10.179, 'F/S': 6.986, 'G/N': 11.855, 'G/S': 7.433, 'H/E': 10.945, 'H/W': 6.204, 'K/E': 16.026, 'K/W': 14.878, 'L': 17.615, 'M/E': 15.392, 'M/W': 7.98, 'N': 12.073, 'P/N': 18.945, 'P/S': 9.069, 'R/C': 11.071, 'R/N': 8.53, 'R/S': 13.252, 'S': 14.41, 'T': 6.66}}
- PDF §8 checklist: population/density/growth ✓ lag1/lag7/roll7/roll30/prev-month(lag30) ✓ reservoir level/storage/pct/avail ✓ month/day/dow/year/season/weekend ✓
