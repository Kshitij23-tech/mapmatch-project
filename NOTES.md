- DAY 03
    - Ques- what does groupby("trip") do, why does the first row of each trip have NaN, and which trip is faster?
        - Answer - groupby("trip") splits the table into two groups here a and b, so rather than having 10 items in the table, we see grouped items, a much cleaner representation. First row of each trip have NaN value because of diff() function, it subtracts previous row from the current row and both trips's first row have no previous row, so giving an unknown(NaN) value. Trip a is faster than trip b because Trip a's mean is greater than trip b's.

- DAY 04 (dataset factos)
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