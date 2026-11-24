# Results summary

## All five datasets together (every scored point)

| method | acc | f1_macro | prec_main | rec_main | prec_serv | rec_serv | n |
|---|---|---|---|---|---|---|---|
| Nearest road | 0.858 | 0.855 | 0.814 | 0.949 | 0.929 | 0.755 | 2565 |
| HMM matcher | 0.860 | 0.856 | 0.810 | 0.960 | 0.943 | 0.746 | 2565 |
| Classifier (trained on simulation) | 0.889 | 0.889 | 0.907 | 0.882 | 0.870 | 0.898 | 2565 |
| HMM + classifier | 0.948 | 0.948 | 0.969 | 0.932 | 0.926 | 0.967 | 2565 |

## Accuracy per dataset

| trip | Nearest road | HMM matcher | Classifier (trained on simulation) | HMM + classifier |
|---|---|---|---|---|
| Dataset1 | 0.961 | 1.000 | 0.918 | 1.000 |
| Dataset2 | 0.997 | 1.000 | 0.863 | 1.000 |
| Dataset3 | 0.978 | 0.981 | 0.931 | 0.977 |
| Dataset4 | 0.675 | 0.661 | 0.916 | 0.946 |
| Dataset5 | 0.857 | 0.865 | 0.733 | 0.809 |

## Distance on the main road per dataset (metres)

| trip | Reference | Nearest road | HMM matcher | Classifier (trained on simulation) | HMM + classifier |
|---|---|---|---|---|---|
| Dataset1 | 5833.000 | 5603.000 | 5833.000 | 5529.000 | 5833.000 |
| Dataset2 | 0.000 | 0.000 | 0.000 | 1009.000 | 0.000 |
| Dataset3 | 14251.000 | 14468.000 | 14468.000 | 15061.000 | 14171.000 |
| Dataset4 | 11462.000 | 15622.000 | 15979.000 | 12118.000 | 12091.000 |
| Dataset5 | 5026.000 | 3953.000 | 4014.000 | 3137.000 | 3650.000 |

## Error of the main-road distance (metres)

| trip | Nearest road | HMM matcher | Classifier (trained on simulation) | HMM + classifier |
|---|---|---|---|---|
| Dataset1 | 230.000 | 0.000 | 303.000 | 0.000 |
| Dataset2 | 0.000 | 0.000 | 1009.000 | 0.000 |
| Dataset3 | 217.000 | 217.000 | 810.000 | 81.000 |
| Dataset4 | 4160.000 | 4517.000 | 656.000 | 628.000 |
| Dataset5 | 1073.000 | 1012.000 | 1889.000 | 1376.000 |

## Road changes found within 5 s (found / true / extra predicted)

| trip | Nearest road | HMM matcher | Classifier (trained on simulation) | HMM + classifier |
|---|---|---|---|---|
| Dataset1 | 0 / 0 / 12 | 0 / 0 / 0 | 0 / 0 / 5 | 0 / 0 / 0 |
| Dataset2 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 10 | 0 / 0 / 0 |
| Dataset3 | 1 / 2 / 1 | 1 / 2 / 1 | 1 / 2 / 5 | 1 / 2 / 1 |
| Dataset4 | 1 / 2 / 53 | 1 / 2 / 5 | 1 / 2 / 10 | 2 / 2 / 3 |
| Dataset5 | 0 / 2 / 8 | 0 / 2 / 4 | 0 / 2 / 8 | 0 / 2 / 6 |

## Simulated validation trips (training ground)

| method | acc | f1_macro | n |
|---|---|---|---|
| Nearest road | 0.816 | 0.802 | 15321 |
| HMM matcher | 0.862 | 0.852 | 15321 |
| Classifier (trained on simulation) | 0.974 | 0.971 | 15321 |
| HMM + classifier | 0.986 | 0.985 | 15321 |

## Feature importance of the classifier

| feature | importance |
|---|---|
| sp_mean | 0.318 |
| sp_max | 0.258 |
| sp_min | 0.149 |
| dHS_mean | 0.088 |
| dHS | 0.088 |
| dH | 0.036 |
| dS | 0.025 |
| hd_rate | 0.019 |
| sp_std | 0.011 |
| acc_absmax | 0.009 |
| stop_frac | 0.000 |
