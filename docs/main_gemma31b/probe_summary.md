# Linear probes on pre-utterance hidden states (hidden/main_gemma31b; ridge lam=10.0, 5-fold by setup)

## single-batch: 72 games (18 unmatched), 3455 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.385 | -0.001 | 0.594 | 0.638 | 0.687 | 0.689 |
| yield (acc) | 0.832 | 0.769 | 0.953 | 0.957 | 0.978 | 0.986 |
| left_self (R2) | 0.788 | -0.000 | 0.890 | 0.887 | 0.848 | 0.816 |
| left_game (R2) | 0.848 | -0.000 | 0.946 | 0.940 | 0.906 | 0.855 |
| winner (acc) | 1.000 | 0.699 | 1.000 | 1.000 | 1.000 | 1.000 |

## single-batch-stepped: 84 games (6 unmatched), 4118 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.396 | -0.001 | 0.630 | 0.591 | 0.655 | 0.679 |
| yield (acc) | 0.826 | 0.765 | 0.957 | 0.957 | 0.979 | 0.988 |
| left_self (R2) | 0.788 | -0.000 | 0.887 | 0.867 | 0.831 | 0.783 |
| left_game (R2) | 0.875 | -0.004 | 0.953 | 0.945 | 0.923 | 0.900 |
| winner (acc) | 1.000 | 0.757 | 1.000 | 1.000 | 0.999 | 1.000 |

## single-online: 90 games (0 unmatched), 4670 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.313 | -0.005 | 0.313 | 0.283 | 0.477 | 0.384 |
| yield (acc) | 0.911 | 0.903 | 0.940 | 0.944 | 0.976 | 0.971 |
| left_self (R2) | 0.909 | -0.000 | 0.801 | 0.871 | 0.830 | 0.718 |
| left_game (R2) | 0.934 | -0.003 | 0.945 | 0.966 | 0.946 | 0.904 |
| winner (acc) | 1.000 | 0.743 | 1.000 | 1.000 | 1.000 | 1.000 |

## multi-public: 90 games (0 unmatched), 4536 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.217 | -0.003 | 0.311 | 0.445 | 0.588 | 0.428 |
| yield (acc) | 0.882 | 0.867 | 0.919 | 0.944 | 0.958 | 0.946 |
| left_self (R2) | 0.854 | -0.000 | 0.750 | 0.814 | 0.775 | 0.651 |
| left_game (R2) | 0.925 | -0.003 | 0.937 | 0.952 | 0.932 | 0.895 |
| winner (acc) | 1.000 | 0.735 | 1.000 | 1.000 | 1.000 | 1.000 |

## multi-private: 90 games (0 unmatched), 4982 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.298 | -0.001 | 0.222 | 0.366 | 0.337 | 0.145 |
| yield (acc) | 0.972 | 0.947 | 0.981 | 0.981 | 0.983 | 0.979 |
| left_self (R2) | 0.928 | -0.000 | 0.860 | 0.886 | 0.849 | 0.711 |
| left_game (R2) | 0.934 | -0.001 | 0.933 | 0.944 | 0.924 | 0.878 |
| winner (acc) | 0.868 | 0.841 | 0.863 | 0.873 | 0.873 | 0.868 |

