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

- Day 10 - measured values and simulator
    - Measured: GPS error sigma 5.1 m, road gap 15 m, speed main 26.9 m/s (97 km/h), service 15.3 m/s (55 km/h).
    - Simulator copy of reality: 
        The simulated speeds match the real ones within 0.1 m/s. Main road is 26.8 against 26.9 m/s and service road is 15.2 against 15.3 m/s. The simulated trips are smoother than real ones. The standard deviation is 5.3 against 6.7 on the main road and 3.5 against 6.8 on the service road. So the simulator is a slightly easier version of reality.
    - Why the simulator matters: 
        There are only five real trips, and one of them is service-only and one is main-only. That is too little to train a classifier and also test it fairly. The simulator makes many trips with this noise and gap, so the classifier has enough to learn from. The five real trips are kept for testing only.

- Day 11 - classifier
    - Simulated validation accuracy: nearest 0.816, HMM 0.862, classifier 0.974, combined (hybrid) 0.986. The classifier on its own scores 0.969 in 5-fold cross-validation with whole trips held out.
    - Classifier on real data: accuracy 0.89 (HMM: 0.86, nearest road: 0.86). Macro F1 is 0.89 against 0.86. Per dataset, the classifier is best on Dataset4: 0.92 against 0.66 for the HMM, where the position-based methods fail. It is worse than the HMM on Dataset1 (0.92 against 1.00), Dataset2 (0.86 against 1.00), Dataset3 (0.93 against 0.98) and Dataset5 (0.73 against 0.87). Dataset4's main-road distance error falls from 4,517 m to 656 m.
    - Most important features: sp_mean (0.318), sp_max (0.258) and sp_min (0.149). These are the mean, maximum and minimum speed over the window. Speed carries about 72% of the classifier's weight. The next features are dHS_mean and dHS (0.088 each), the distance to the highway and to the service road.
    - Chosen fusion weight: 2. On the simulated validation set, accuracy was 0.925 at weight 0.25, 0.949 at 0.5, 0.974 at 1, 0.986 at 2 and 0.984 at 4.
    - Gap between simulated and real accuracy: 0.974 → 0.89 (about 8.4 points). Possible reasons:
        - The simulator is smoother than real driving. The service-road speed standard deviation is 3.5 in the simulator against 6.8 in the real data. Real service roads have slow traffic, junctions and stops. The classifier relies on speed, so real slowdowns on the main road or fast stretches on the service road confuse it.
        - Dataset2 (service-only) scores 0.86, with 10 extra switches and 1,009 m of false main-road distance. The classifier sometimes calls fast service-road stretches "main".
        - Dataset5 (flyover) scores 0.73. The flyover has main-road speeds on a road that is labelled service in our rules, so speed gives the wrong answer there.
        - The classifier has no smoothing. Its extra road changes (5, 10, 5, 10, 8) are higher than the HMM's. The hybrid fixes this by combining it with the HMM.

- Day 12 - final table
    - Pooled accuracy: nearest 0.858 , HMM 0.860 , classifier 0.889 , combined 0.948 .
    - Distance on main road, error (m): nearest 1136 , HMM 1149 , combined 417 .
    - Combined vs HMM: better by 8.8 accuracy points (0.948 against 0.860) and a macro F1 of 0.948 against 0.856, because the HMM keeps the path smooth but cannot tell the roads apart when the GPS is noisy, and the classifier tells them apart from speed but switches too often. Together they fix Dataset4 (0.661 → 0.946, main-road distance error 4,517 m → 628 m) and keep the HMM's low number of false road changes (10 in total for both). .
        - Extra road changes (all trips, found within 5 s): nearest 74, HMM 10, classifier 38, combined 10.
        - Road changes found: combined finds 3 of 6 (D3 1/2, D4 2/2, D5 0/2). Dataset4 is the only trip where it finds both.
        - Simulated to real gap: 0.986 → 0.948 (3.8 points) for combined, against 0.974 → 0.889 (8.5 points) for the classifier alone. The combination is also more robust.

- Day 13 - flyover and failures
    - Flyover: height rises by 6.7 m (the peak above the base height of 686.9 m) between points 10 and 272 of Dataset5 (49 points are more than 3 m above the base); 0 % of the points matched to bridge roads, because OpenStreetMap has no separate flyover road here; accuracy on the flyover 1.000 for the HMM and the hybrid (nearest road 0.980, classifier alone 0.694). The HMM is right because of the road-name rule for this area (AREA_RULES), not because it detects the bridge.
    - Failure 1: Delay at road changes. The matcher needs several points to trust a change, so it switches late. Hybrid: 57 wrong points near a road change, for example Dataset5 points 55–72 (18 points) and Dataset3 points 93–107 (15 points).
    - Failure 2: Noisy GPS in Dataset4. Points 521–552 (32 points, the longest wrong run) are true service road but predicted main. The speed is 22.4 m/s, like the expressway's, and the points lie nearer the expressway because the GPS here is about 5 m from the nearest road.
    - Failure 3: Dataset5 flyover area. Points 79–98 (20 points) and 236–250 (15 points) are true main but predicted service, 24 m and 46 m from a road change, at 18.6 and 23.3 m/s. The flyover and the road below almost overlap, so position cannot separate them.
    - What would help (future work): denser and more accurate GPS (for example dual-frequency GPS, or 5 Hz instead of 1 Hz); a better road map with the flyover and the service road drawn separately; more real trips for training, since the simulator is smoother than real driving; using the dashcam video (lane or road-sign detection) or a phone gyroscope to tell the two levels apart; and a shorter smoothing window that adapts at road changes, so the delay shrinks without adding false switches.

    Totals to quote: hybrid has 133 wrong points out of 2,565 (5.2 %): 76 far from a road change and 57 near one. The HMM has 360 and nearest road has 364.