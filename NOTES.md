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

Day 09 - HMM matcher
    - HMM accuracy, all datasets together: 0.86 (nearest road: 0.86). Macro F1 is 0.86 for the HMM against 0.85 for nearest road. Chosen sigma 5 m, beta 5 m. sigma 10 made the HMM too sticky: Dataset4 fell to 0.49.
    - Distance on the main road, error in metres (HMM): D1 0 (nearest road: 230), D2 0 (0), D3 217 (217), D4 4,517 (4,160), D5 1,012 (1,073).
    - Extra road changes (HMM): D1 0, D2 0, D3 1, D4 5, D5 4, which is 10 in total. Nearest road: 12 + 0 + 1 + 53 + 8 = 74 in total. The HMM removes about 86% of the false switches. This is its clearest gain.
    - Where the HMM still goes wrong:
        - Dataset4: accuracy is 0.66. The GPS is noisier here, about 5 m from the nearest road against 1.4–2.4 m in Dataset3. In the service-road stretch most points are nearer the expressway than the service road, so any method that works from position alone fails. This is a finding about the data, not a bug.
        - Dataset5 (flyover area): accuracy is 0.87, the main-road distance is off by about 1 km, and there are 4 extra switches. The flyover and the road beneath it lie almost on top of each other.
        - Road changes: the HMM found only 1 of the 2 true changes in D3, D4 and D5 (D5: 0 of 2). The changes it finds are late or missed.
        - Dataset2: the matcher cannot be told apart from nearest road here, because it is a single-road trip.
    - What the switch cost means on a real road: BETA is the metres of disagreement between straight-line and route distance that cost one unit of log-probability. With beta 5, the HMM doubts a jump to a road whose route is 5 m longer than the straight line. A bigger beta tolerates detours and makes the HMM jump more easily. A smaller beta makes it stay on its road. NO_ROUTE_PENALTY 30 means "switching to a road with no driveable path is about as unlikely as being 30 units off". On the highway this stops the matcher hopping between the expressway and the parallel service road unless it has a real path between them.