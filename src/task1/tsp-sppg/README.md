# TSP SPPG Simulator (Surabaya)

## Run
    python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python -m streamlit run app.py

First launch downloads the Surabaya drive network + schools from OSM (a few minutes),
then caches them in `cache/` so later runs are instant. Needs internet the first time.

## How it works
1. **Data**: OSMnx -> drive network (largest strongly connected component), converted to a
   `networkx.DiGraph` (one-way streets respected). Schools = OSM `amenity=school` (centroids).
2. **Map**: click to place SPPG; slider sets radius x km; schools inside radius (haversine) are selected.
3. **Distance matrix**: SPPG and schools are snapped to nearest graph nodes; Dijkstra from each
   gives the shortest road distance for every ordered pair -> asymmetric matrix
   (A->B != B->A because of one-way roads).
4. **TSP**: <= 12 schools: Held-Karp exact DP. More: nearest neighbour + 2-opt + Or-opt with
   iterated perturbation (6 s budget). All moves evaluate the true asymmetric cost.
5. **Route**: each leg is expanded back to the real shortest path on the road network
   (segments may repeat). Travel time = sum of OSM edge travel times (speed limits / defaults).
6. **Output**: route overlay, numbered visiting order, total distance, ETA, solver time.

## Report notes
- Complexity: Held-Karp O(2^n n^2); heuristic is polynomial per pass, no optimality guarantee.
- Metric closure: the TSP runs on shortest-path distances between stops, so revisiting roads is allowed.
- Limitations: radius is straight-line; travel time ignores live traffic and unloading time.
