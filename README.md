# Main Road vs Service Road: Map-Matching on the Bengaluru–Mysuru Highway

Project-I (AI24300), B.Tech CSE (AIML), BIT Mesra, Patna Campus
Authors: Kshitij Tiwari, Nitin Kumar  
Guide: Dr. Naiyar Iqbal  
Problem source: Smart India Hackathon 2024, PS1740 (ISRO-SAC)

## What this project does

On the Bengaluru–Mysuru highway the main road (expressway) and the service road run side by side, about 15 m apart. Typical GPS error is about 5 m, so "snap to the nearest road" often picks the wrong one.

For every GPS point of a trip this project decides whether the vehicle is on the **main road** or the **service road**. It compares four methods:

| Method | Idea |
|---|---|
| Nearest road | Snap each point to the closest road (baseline) |
| HMM matcher | Hidden Markov Model with Viterbi: also uses road connectivity, so it rarely jumps between roads |
| Classifier | Random Forest on speed, heading and distance features, trained on simulated trips |
| HMM + classifier (hybrid) | The classifier's probability is added to the HMM's emission score (weight 2) |

## Results

Five real trips, 2,565 labelled GPS points. Ground truth was labelled by hand from dashcam video.

| Method | Accuracy | Macro F1 | Extra road changes |
|---|---|---|---|
| Nearest road | 0.858 | 0.855 | 74 |
| HMM matcher | 0.860 | 0.856 | 10 |
| Classifier (trained on simulation) | 0.889 | 0.889 | 38 |
| **HMM + classifier** | **0.948** | **0.948** | **10** |

Average error of the distance driven on the main road: nearest road 1,136 m, HMM 1,149 m, hybrid 417 m.

Per dataset, the hybrid reaches 1.000 on Dataset1 and Dataset2, 0.977 on Dataset3, 0.946 on Dataset4 and 0.809 on Dataset5. The full tables are in `results/summary.md`.

## Known limits

- **Dataset4:** the GPS is noisier (about 5 m from the nearest road), so position-only methods fail. The classifier and hybrid fix most of it.
- **Delay at road changes:** the matcher needs a few points to trust a change, so it switches 3 to 18 points late.
- **Dataset5 flyover:** OpenStreetMap has no separate road for the flyover here (0 % of flyover points matched a bridge road). The HMM is correct there because of a road-name rule (`AREA_RULES` in `src/config.py`), not because it detects the bridge.
- Only 5 trips, so results are indicative.
- The classifier is trained on simulated trips, which are smoother than real driving (simulated accuracy 0.986, real 0.948).
- Works for the Bengaluru–Mysuru corridor only.

## Project layout

```
mapmatch-project/
├── data/
│   ├── raw/ , trips/        (not in the repository)
│   ├── labels.csv           hand-made ground truth (trip, start_idx, end_idx, label, note)
│   └── processed/           points.parquet, network.joblib, model.joblib
├── results/                 tables, figures, summary.md
└── src/
    ├── config.py            all settings (sigma, beta, road rules, simulator values)
    ├── preprocess.py        clean, project to metres, speed and heading
    ├── graph.py             download OpenStreetMap roads, group main / service
    ├── labels.py            per-point ground truth from labels.csv
    ├── candidates.py        nearby road candidates for each point
    ├── baseline.py          nearest-road method
    ├── hmm_matcher.py       HMM with Viterbi
    ├── simulator.py         simulated trips from measured gap, noise, speeds
    ├── features.py          features for the classifier
    ├── classifier.py        Random Forest
    ├── fuse.py              adds classifier probability to the HMM
    ├── train_sim.py         trains the classifier and picks the fusion weight
    ├── eval_real.py         evaluates all methods on the real trips
    ├── flyover.py           flyover analysis (Dataset5)
    ├── failures.py          where the methods go wrong
    ├── static_maps.py       PNG maps of truth and predictions
    └── predict.py           label a new trip
```

## Setup

```
conda create -n mapmatch python=3.11
conda activate mapmatch
pip install pandas numpy pyarrow pyproj osmnx geopandas shapely networkx scikit-learn matplotlib folium joblib
```

Put the raw trip files in `data/trips/` (they are not stored in the repository). An internet connection is needed once, to download the road network from OpenStreetMap.

## How to run

Run from the project folder, in this order:

```
python -m src.preprocess      # clean data, make data/processed/points.parquet
python -m src.graph           # download and group roads, make network.joblib
python -m src.labels          # check labels.csv
python -m src.train_sim       # simulate trips, train classifier, make model.joblib
python -m src.eval_real       # evaluate all methods on the real trips
python -m src.flyover         # flyover analysis
python -m src.failures        # failure analysis
python -m src.static_maps     # PNG maps in results/static_maps/
```

## Use it on your own trip

Input: a CSV with columns `lat`, `lon` and `time` (seconds or a timestamp, about 1 reading per second).

```
python -m src.predict path/to/trip.csv
```

Output, next to the input file:

- `trip_labelled.csv`: every point with `road` (main, service or other) and `p_service`
- `trip_labelled.png`: the trip drawn over the road network

To use another highway: download its network with `src/graph.py`, set the road rules in `src/config.py`, then retrain with `src/train_sim.py`.

## Method notes

- **HMM:** emission score is `-0.5 * (d / sigma)^2` for a point `d` metres from a road. Transition score is `-|straight distance - route distance| / beta`. The best path is found with Viterbi. Chosen values: sigma = 5 m, beta = 5 m.
- **Simulator:** only five real trips exist, so trips are simulated using the measured road gap (15 m), GPS error (5.1 m) and speeds (26.9 m/s main, 15.3 m/s service). The real trips are used only for testing.
- **Classifier:** Random Forest. The most important features are mean, max and min speed over a window (about 72 % of the weight).
- **Fusion:** the classifier's log-probability, times a weight of 2, is added to each candidate road's emission score.

## Libraries used

pandas, NumPy, pyproj, OSMnx, GeoPandas, Shapely, NetworkX, scikit-learn, Matplotlib, Folium, joblib. Road data: OpenStreetMap contributors.

## References

- Newson, P. and Krumm, J. (2009). *Hidden Markov Map Matching Through Noise and Sparseness.* ACM SIGSPATIAL GIS.
- Smart India Hackathon 2024, problem statement PS1740 (ISRO-SAC).