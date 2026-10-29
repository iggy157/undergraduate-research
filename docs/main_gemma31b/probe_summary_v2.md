# Linear probes on pre-utterance hidden states (hidden/main_gemma31b; ridge, penalty chosen by nested grouped CV from [1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0], 5-fold by setup)

## single-batch: 72 games (18 unmatched), 3455 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.385 | -0.001 | 0.804 | 0.847 | 0.858 | 0.845 |
| yield (acc) | 0.832 | 0.769 | 0.965 | 0.971 | 0.980 | 0.991 |
| left_self (R2) | 0.788 | -0.000 | 0.912 | 0.930 | 0.910 | 0.877 |
| left_game (R2) | 0.847 | -0.000 | 0.950 | 0.954 | 0.936 | 0.895 |
| winner (acc) | 1.000 | 0.699 | 1.000 | 1.000 | 1.000 | 1.000 |

## single-batch-stepped: 84 games (6 unmatched), 4118 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.396 | -0.001 | 0.808 | 0.856 | 0.866 | 0.851 |
| yield (acc) | 0.826 | 0.765 | 0.964 | 0.975 | 0.981 | 0.991 |
| left_self (R2) | 0.788 | -0.000 | 0.913 | 0.925 | 0.911 | 0.871 |
| left_game (R2) | 0.875 | -0.004 | 0.956 | 0.959 | 0.950 | 0.927 |
| winner (acc) | 1.000 | 0.757 | 1.000 | 1.000 | 0.999 | 1.000 |

## single-online: 90 games (0 unmatched), 4670 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.313 | -0.005 | 0.691 | 0.739 | 0.800 | 0.777 |
| yield (acc) | 0.910 | 0.903 | 0.963 | 0.966 | 0.979 | 0.982 |
| left_self (R2) | 0.909 | -0.000 | 0.882 | 0.916 | 0.907 | 0.853 |
| left_game (R2) | 0.934 | -0.003 | 0.951 | 0.965 | 0.963 | 0.925 |
| winner (acc) | 1.000 | 0.743 | 1.000 | 1.000 | 1.000 | 1.000 |

## multi-public: 90 games (0 unmatched), 4536 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.217 | -0.003 | 0.737 | 0.775 | 0.820 | 0.771 |
| yield (acc) | 0.881 | 0.867 | 0.964 | 0.969 | 0.971 | 0.965 |
| left_self (R2) | 0.854 | -0.000 | 0.851 | 0.878 | 0.880 | 0.815 |
| left_game (R2) | 0.925 | -0.003 | 0.945 | 0.959 | 0.950 | 0.927 |
| winner (acc) | 1.000 | 0.735 | 1.000 | 1.000 | 1.000 | 1.000 |

## multi-private: 90 games (0 unmatched), 4982 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.296 | -0.001 | 0.666 | 0.699 | 0.726 | 0.633 |
| yield (acc) | 0.972 | 0.947 | 0.984 | 0.984 | 0.987 | 0.980 |
| left_self (R2) | 0.928 | -0.000 | 0.909 | 0.923 | 0.912 | 0.841 |
| left_game (R2) | 0.934 | -0.001 | 0.946 | 0.956 | 0.949 | 0.918 |
| winner (acc) | 0.867 | 0.841 | 0.868 | 0.880 | 0.878 | 0.846 |

## multi-private-stepped: 90 games (0 unmatched), 4998 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.349 | -0.007 | 0.735 | 0.792 | 0.815 | 0.797 |
| yield (acc) | 0.878 | 0.854 | 0.959 | 0.963 | 0.978 | 0.988 |
| left_self (R2) | 0.987 | -0.000 | 0.964 | 0.967 | 0.948 | 0.915 |
| left_game (R2) | 0.958 | -0.002 | 0.940 | 0.946 | 0.938 | 0.907 |
| winner (acc) | 0.906 | 0.812 | 0.889 | 0.898 | 0.896 | 0.895 |

## multi-private-stepped-process: 90 games (0 unmatched), 4992 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.269 | -0.006 | 0.747 | 0.807 | 0.810 | 0.762 |
| yield (acc) | 0.906 | 0.906 | 0.975 | 0.983 | 0.987 | 0.987 |
| left_self (R2) | 0.981 | -0.000 | 0.963 | 0.967 | 0.947 | 0.912 |
| left_game (R2) | 0.956 | -0.002 | 0.945 | 0.946 | 0.939 | 0.920 |
| winner (acc) | 0.926 | 0.795 | 0.920 | 0.924 | 0.921 | 0.912 |

## multi-public-stepped: 90 games (0 unmatched), 4434 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.373 | -0.000 | 0.816 | 0.862 | 0.872 | 0.858 |
| yield (acc) | 0.848 | 0.765 | 0.969 | 0.974 | 0.981 | 0.993 |
| left_self (R2) | 0.837 | -0.001 | 0.910 | 0.933 | 0.910 | 0.874 |
| left_game (R2) | 0.895 | -0.002 | 0.944 | 0.948 | 0.936 | 0.922 |
| winner (acc) | 1.000 | 0.732 | 1.000 | 1.000 | 1.000 | 1.000 |

