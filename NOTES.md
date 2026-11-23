- DAY 03
    - Ques- what does groupby("trip") do, why does the first row of each trip have NaN, and which trip is faster?
        - Answer - groupby("trip") splits the table into two groups here a and b, so rather than having 10 items in the table, we see grouped items, a much cleaner representation. First row of each trip have NaN value because of diff() function, it subtracts previous row from the current row and both trips's first row have no previous row, so giving an unknown(NaN) value. Trip a is faster than trip b because Trip a's mean is greater than trip b's.

- DAY 04 (dataset facts)
    - Files per dataset: .pos (GNSS positions, the data we use), .kml (same path, for Google Earth), .mp4 (video)
    - Dataset1: main road only
    - Dataset2: service road only
    - Dataset3: starts on the service road, enters the main road, then exits
    - Dataset4: starts on the main road, detours onto the service road, re-enters
    - Dataset5: main road is a flyover, service road runs underneath
    - README asks for: distance travelled on the main road, per dataset
    - Data is confidential: private repo, never upload the raw files

    1. Only five trips: too few to train a model on. We train on simulated trips and test on these five.
    2. The README wants the distance travelled on the main road, so our output must include that number for each dataset, not only accuracy.
    3. Dataset5 is a flyover: on a flat map it sits directly over the road below, so position alone cannot separate them. We will report it separately as a hard case. The height column may help.

    - Main road (Dataset1): no. of lanes are 3, and speed of vehicles is fast
    - Service road (Dataset2): no. of lanes are 2, and vehicles are moving slow

- DAY 05: converted data

        | Dataset | Points | Duration (s) | Step (s) | Q | Where on the highway |
        |---|---|---|---|---|---|
        | Dataset1 | 256 | 255 | 1.00 | 5 | lat 12.76-12.78, lon 77.32-77.37 |
        | Dataset2 | 293 | 293 | 1.00 | 5 | same stretch as Dataset1 |
        | Dataset3 | 784 | 783 | 1.00 | 5 | lat 12.49-12.55, lon 76.79-76.93 |
        | Dataset4 | 876 | 875 | 1.00 | 5 | lat 12.58-12.64, lon 77.02-77.17 |
        | Dataset5 | 356 | 355 | 1.00 | 5 | lat 12.86-12.90, lon 77.43-77.47 |

    - One position per second in every dataset, about 2,700 points in total.
    - Every point has Q = 5 (single-point solution, the least accurate type). Expect errors of several  metres. That is the same size as the gap between the two roads, which is why the problem is hard.
    - Dataset1 (main road) and Dataset2 (service road) cover the same stretch, so their paths sit on top of each other in the combined plot. That is why I saw four lines, not five.
    - Datasets 3, 4 and 5 are at different places along the highway.

- Day 06
    - Roads downloaded: 2823 edges. Main road tags: "motorway", "motorway_link" . Service road tags: "primary" "primary_link", "secondary", "tertiary", "service" .
    - Sanity check: Dataset1 96 % on main road, Dataset2 100 % on service road.
    - What surprised me: service road speed is only 10 km/h below the main road.

- Day 07
    - Video offsets: Dataset3 = 10, Dataset4 = 14, Dataset5 = 5.
    - Dataset3: service road until point 92, main road until 522, then service road.
    - Dataset4: main road until 387, service road until 828, then main road.
    - Dataset5: ground road until 54, flyover until 295, then ground road.
    - Reference main-road distance (m): D1 5833, D2 0, D3 14251, D4 11462, D5 5026.
    - How sure I am about the boundaries: about 5 points (about 5 seconds).

- Day 08 - baseline: nearest road
    - Accuracy, all datasets together: 0.86 (2201 of 2565 points right). Worst dataset: Dataset4 (0.67).
    - Distance on the main road, error in metres: D1 230 , D2 0 , D3 217 , D4 4160 , D5 1073 .
    - Extra road changes invented: 74 in total (D1 12, D3 1, D4 53, D5 8).
    - Why nearest road fails here: the two roads are only a short distance apart, so the GPS error is of similar size to the gap and the nearest road flips between them. (gap and GPS error in metres: measure on Day 10)
    - Dataset5: the score was 0.04 before the area rule (the flyover is named "Highway" in OpenStreetMap there) and 0.86 after it.