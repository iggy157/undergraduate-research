# Linear probes on pre-utterance hidden states (hidden/main_qwen38; ridge, penalty chosen by nested grouped CV from [1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0], 5-fold by setup)

## single-batch: 52 games (38 unmatched), 3100 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.376 | -0.009 | 0.797 | 0.793 | 0.795 | 0.681 |
| yield (acc) | 0.893 | 0.893 | 0.978 | 0.983 | 0.985 | 0.990 |
| left_self (R2) | 1.000 | 0.000 | 0.977 | 0.974 | 0.951 | 0.907 |
| left_game (R2) | 0.961 | -0.000 | 0.974 | 0.974 | 0.969 | 0.950 |
| winner (acc) | 0.987 | 0.987 | 0.987 | 0.987 | 0.987 | 0.987 |

## single-batch-stepped: 90 games (0 unmatched), 4854 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.325 | -0.008 | 0.775 | 0.783 | 0.784 | 0.712 |
| yield (acc) | 0.931 | 0.931 | 0.987 | 0.988 | 0.990 | 0.993 |
| left_self (R2) | 0.997 | -0.000 | 0.974 | 0.968 | 0.939 | 0.879 |
| left_game (R2) | 0.978 | -0.003 | 0.960 | 0.960 | 0.953 | 0.928 |
| winner (acc) | 0.990 | 0.751 | 0.990 | 0.990 | 0.989 | 0.988 |

## single-online: 90 games (0 unmatched), 4872 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.193 | -0.015 | 0.334 | 0.372 | 0.436 | 0.425 |
| yield (acc) | 0.995 | 0.995 | 0.995 | 0.995 | 0.996 | 0.998 |
| left_self (R2) | 1.000 | -0.000 | 0.952 | 0.969 | 0.959 | 0.896 |
| left_game (R2) | 0.974 | -0.002 | 0.952 | 0.971 | 0.962 | 0.948 |
| winner (acc) | 0.957 | 0.782 | 0.960 | 0.967 | 0.960 | 0.966 |

## multi-public: 90 games (0 unmatched), 4836 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.318 | -0.014 | 0.338 | 0.398 | 0.456 | 0.398 |
| yield (acc) | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 |
| left_self (R2) | 1.000 | 0.000 | 0.965 | 0.977 | 0.967 | 0.911 |
| left_game (R2) | 0.985 | -0.003 | 0.975 | 0.972 | 0.970 | 0.952 |
| winner (acc) | 0.989 | 0.755 | 0.989 | 0.989 | 0.989 | 0.989 |

## multi-private: 90 games (0 unmatched), 4996 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.243 | -0.010 | 0.337 | 0.367 | 0.434 | 0.388 |
| yield (acc) | 0.995 | 0.995 | 0.995 | 0.995 | 0.997 | 0.997 |
| left_self (R2) | 1.000 | 0.000 | 0.963 | 0.979 | 0.973 | 0.923 |
| left_game (R2) | 0.960 | -0.002 | 0.952 | 0.952 | 0.951 | 0.930 |
| winner (acc) | 0.938 | 0.783 | 0.938 | 0.938 | 0.934 | 0.930 |

## multi-private-stepped: 90 games (0 unmatched), 5012 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.307 | -0.025 | 0.737 | 0.727 | 0.739 | 0.604 |
| yield (acc) | 0.967 | 0.967 | 0.993 | 0.994 | 0.995 | 0.997 |
| left_self (R2) | 1.000 | 0.000 | 0.982 | 0.979 | 0.958 | 0.923 |
| left_game (R2) | 0.939 | -0.002 | 0.916 | 0.916 | 0.916 | 0.897 |
| winner (acc) | 0.926 | 0.794 | 0.917 | 0.916 | 0.907 | 0.904 |

## multi-private-stepped-process: 90 games (0 unmatched), 5120 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.347 | -0.010 | 0.728 | 0.734 | 0.723 | 0.581 |
| yield (acc) | 0.977 | 0.977 | 0.995 | 0.996 | 0.997 | 0.998 |
| left_self (R2) | 1.000 | 0.000 | 0.980 | 0.979 | 0.960 | 0.915 |
| left_game (R2) | 0.885 | -0.001 | 0.861 | 0.862 | 0.860 | 0.815 |
| winner (acc) | 0.921 | 0.780 | 0.916 | 0.918 | 0.915 | 0.920 |

## multi-public-stepped: 90 games (0 unmatched), 4812 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.323 | -0.012 | 0.745 | 0.751 | 0.761 | 0.669 |
| yield (acc) | 0.955 | 0.955 | 0.988 | 0.989 | 0.991 | 0.995 |
| left_self (R2) | 0.990 | -0.000 | 0.970 | 0.964 | 0.945 | 0.893 |
| left_game (R2) | 0.975 | -0.002 | 0.949 | 0.948 | 0.947 | 0.929 |
| winner (acc) | 0.989 | 0.756 | 0.989 | 0.989 | 0.988 | 0.989 |

