# Linear probes on pre-utterance hidden states (hidden/main_qwen38; ridge lam=10.0, 5-fold by setup)

## single-batch: 52 games (38 unmatched), 3100 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.376 | -0.009 | 0.513 | 0.526 | 0.476 | 0.416 |
| yield (acc) | 0.893 | 0.893 | 0.977 | 0.985 | 0.978 | 0.989 |
| left_self (R2) | 1.000 | 0.000 | 0.972 | 0.970 | 0.941 | 0.876 |
| left_game (R2) | 0.961 | -0.000 | 0.972 | 0.971 | 0.967 | 0.945 |
| winner (acc) | 0.987 | 0.987 | 0.987 | 0.987 | 0.987 | 0.987 |

## single-batch-stepped: 90 games (0 unmatched), 4854 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.325 | -0.008 | 0.399 | 0.342 | 0.288 | 0.278 |
| yield (acc) | 0.931 | 0.931 | 0.985 | 0.983 | 0.985 | 0.991 |
| left_self (R2) | 0.997 | -0.000 | 0.966 | 0.955 | 0.909 | 0.809 |
| left_game (R2) | 0.978 | -0.003 | 0.953 | 0.949 | 0.933 | 0.893 |
| winner (acc) | 0.990 | 0.751 | 0.990 | 0.990 | 0.989 | 0.989 |

## single-online: 90 games (0 unmatched), 4872 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.193 | -0.015 | -1.656 | -1.445 | -0.821 | -0.916 |
| yield (acc) | 0.995 | 0.995 | 0.995 | 0.995 | 0.997 | 0.998 |
| left_self (R2) | 1.000 | -0.000 | 0.947 | 0.961 | 0.948 | 0.843 |
| left_game (R2) | 0.974 | -0.002 | 0.954 | 0.970 | 0.957 | 0.933 |
| winner (acc) | 0.957 | 0.782 | 0.967 | 0.967 | 0.961 | 0.966 |

## multi-public: 90 games (0 unmatched), 4836 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.318 | -0.014 | -1.454 | -0.911 | -0.757 | -1.179 |
| yield (acc) | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 |
| left_self (R2) | 1.000 | 0.000 | 0.957 | 0.971 | 0.956 | 0.873 |
| left_game (R2) | 0.985 | -0.003 | 0.976 | 0.973 | 0.968 | 0.937 |
| winner (acc) | 0.989 | 0.755 | 0.989 | 0.989 | 0.989 | 0.989 |

## multi-private: 90 games (0 unmatched), 4996 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.243 | -0.010 | -1.094 | -0.856 | -0.674 | -0.876 |
| yield (acc) | 0.995 | 0.995 | 0.997 | 0.996 | 0.997 | 0.998 |
| left_self (R2) | 1.000 | 0.000 | 0.956 | 0.976 | 0.963 | 0.882 |
| left_game (R2) | 0.960 | -0.002 | 0.941 | 0.947 | 0.934 | 0.913 |
| winner (acc) | 0.938 | 0.783 | 0.921 | 0.916 | 0.910 | 0.928 |

## multi-private-stepped: 90 games (0 unmatched), 5012 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.308 | -0.025 | 0.351 | 0.239 | 0.278 | 0.166 |
| yield (acc) | 0.967 | 0.967 | 0.994 | 0.993 | 0.994 | 0.996 |
| left_self (R2) | 1.000 | 0.000 | 0.975 | 0.971 | 0.938 | 0.878 |
| left_game (R2) | 0.940 | -0.002 | 0.897 | 0.879 | 0.866 | 0.842 |
| winner (acc) | 0.925 | 0.794 | 0.902 | 0.896 | 0.864 | 0.876 |

## multi-private-stepped-process: 90 games (0 unmatched), 5120 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.347 | -0.010 | 0.318 | 0.294 | 0.228 | 0.199 |
| yield (acc) | 0.977 | 0.977 | 0.996 | 0.996 | 0.996 | 0.998 |
| left_self (R2) | 1.000 | 0.000 | 0.973 | 0.970 | 0.942 | 0.859 |
| left_game (R2) | 0.884 | -0.001 | 0.848 | 0.798 | 0.763 | 0.722 |
| winner (acc) | 0.922 | 0.780 | 0.911 | 0.885 | 0.876 | 0.882 |

## multi-public-stepped: 90 games (0 unmatched), 4812 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.324 | -0.012 | 0.312 | 0.234 | 0.245 | 0.201 |
| yield (acc) | 0.955 | 0.955 | 0.988 | 0.990 | 0.989 | 0.994 |
| left_self (R2) | 0.990 | -0.000 | 0.959 | 0.951 | 0.917 | 0.834 |
| left_game (R2) | 0.975 | -0.002 | 0.940 | 0.935 | 0.928 | 0.904 |
| winner (acc) | 0.989 | 0.756 | 0.989 | 0.989 | 0.988 | 0.989 |

