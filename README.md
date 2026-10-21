# Graph Theory Coding Task (Week 6–8)

## Team Members
| Name | NRP | Kelas |
| --- | --- | --- |
| Ahmad Farras Favian Al Efasi | 5025251005 | IUP |
| Daniel Pedrosaputra| 5025251171 | IUP |


## Introduction

this project implements three graph theory problems: the Travelling Salesman Problem (TSP), Chinese Postman Problem (CPP), and Knight’s Tour.

TSP finds an efficient route that visits every destination exactly once and returns to the starting point. CPP minimizes the cost of traversing every required road at least once, while Knight’s Tour finds a sequence of legal knight moves that visits every chessboard square exactly once.

The project applies these problems to real-world scenarios, including MBG meal delivery and DLH garbage collection in Surabaya. It explores pathfinding algorithms, route optimization, computational complexity, and solution performance.

## Algorithms

### Travelling Salesman Problem (TSP) 

The Travelling Salesman Problem (TSP) finds the shortest closed route that visits every selected school exactly once and returns to the SPPG. This project applies TSP to MBG mealbox delivery in Surabaya using a weighted directed road network, where edge weights represent road distances and may differ by direction.

Dijkstra’s algorithm calculates the shortest road distances between the SPPG and selected schools to build an asymmetric distance matrix. The TSP solver then determines the delivery order and expands each route into its corresponding road paths.

Algorithms:

**Held–Karp (up to 12 schools)**: Uses dynamic programming to find the optimal tour, with time complexity (O(2^k k^2)).

**Nearest Neighbour + 2-opt/Or-opt (larger instances)**: Builds an initial tour and improves it by rearranging stops. A time-limited search keeps the best tour found.

The simulator displays the delivery route, visit order, total distance, estimated travel time, and algorithm execution time.


### Chinese Postman Problem (CPP)

The Chinese Postman Problem (CPP) finds the shortest closed route that traverses every required road segment at least once and returns to the starting point. This project applies CPP to a dump truck simulator for planning garbage collection routes across trunk, primary, secondary, and tertiary roads in Surabaya.

The road network is represented as a weighted directed multigraph, where vertices represent intersections and edges represent road segments. Edge weights represent road distances, and edge directions account for one-way streets. Since the network may be unbalanced, some road segments must be traversed more than once to form a valid closed route.

Algorithm:

**Minimum-Cost Flow Balancing:** Calculates the additional road traversals required to balance the directed graph while minimizing the extra travel distance.

**Hierholzer’s Algorithm:** Constructs an Euler circuit on the balanced graph, ensuring every required road segment is traversed at least once and the route returns to the starting point.

Checking strong connectivity and constructing the Euler circuit take (O(V+E)) time, where (V) is the number of vertices and (E) is the number of edges. The balancing step uses minimum-cost flow, whose computational cost depends on the network and solver implementation.

### Knight's Tour Problem

The Knight's Tour Problem finds a sequence of knight moves on a chessboard such that the knight visits every square exactly once. This project applies the Knight's Tour to a dynamic chessboard simulator, where the board size and the knight's starting position are given as input.

The chessboard is represented as an undirected graph, where vertices represent squares and edges represent legal knight moves. A Knight's Tour is therefore a Hamiltonian path in this graph, a path that visits every vertex exactly once. Not every board and starting square has a valid tour, so the solver reports `path not found` when none exists.

Algorithms:

**Backtracking:** Builds the tour one move at a time. When the knight reaches a dead end with unvisited squares remaining, it undoes the last move and tries another option. In the worst case, the time complexity is (O(8^N)), where (N) is the number of squares on the board.

**Warnsdorff's Rule:** A heuristic that guides the backtracking search. At each step, the knight moves to the unvisited square with the fewest onward moves, which visits hard-to-reach squares such as corners first. This usually finds a tour with little or no backtracking.

The simulator displays the knight's tour on the chessboard, including the visit order of each square, the current move number, and the coordinates visited in order.

## Implementation and Output

### SPPG Simulator

The SPPG Simulator is implemented in Python using OSMnx, NetworkX, Streamlit, and Folium. OSMnx retrieves Surabaya’s drivable road network and school locations from OpenStreetMap (OSM), while Streamlit and Folium provide an interactive map. Downloaded data is cached locally to reduce repeated downloads.

Users select an SPPG location by clicking the map and set a delivery radius (x) km. Schools within that radius, measured by straight-line distance, are selected and snapped to their nearest road vertices. The road network is represented as a weighted directed graph that accounts for one-way streets. Dijkstra’s algorithm calculates the shortest road distances and constructs a directed distance matrix. The solver then determines the school visiting order using Held–Karp for smaller instances or Nearest Neighbour with local-search improvements for larger instances.

The resulting route is expanded into actual road paths and displayed on the map. The simulator reports the school visiting order, total route distance, estimated travel time, and solver execution time. Distance is calculated from road-segment lengths, while travel time is estimated using speed limits or default speeds based on road types, without live traffic data.

Test Configuration:

* SPPG location: [Name or coordinates]

* Delivery radius: [(x)] km

* Number of schools selected: [(k)]

* Solver used: [Held–Karp / heuristic]

* Total route distance: [Result]

* Estimated travel time: [Result]

* Solver execution time: [Result]

<img width="1876" height="856" alt="image" src="https://github.com/user-attachments/assets/200299d3-c8e2-4666-bff0-ef7beba0f598" />

*map showing the selected SPPG location, delivery radius, school locations, and suggested delivery route.*

### Dumptruck Simulator

The Dumptruck Simulator CPP is implemented in Python using OSMnx, NetworkX, Streamlit, and Folium. OSMnx retrieves Surabaya’s drivable road network from OpenStreetMap (OSM), while Streamlit and Folium provide an interactive mapping and control interface. Downloaded data is cached locally to avoid redundant network requests.

Users define a zone or target area by selecting boundaries or entering parameters on the map. The road network is extracted as a directed/undirected graph representation. The application identifies required edges, handles odd-degree balancing via the C++ solver module, and computes the optimal postman tour.

The resulting traversal path is highlighted on the map alongside performance telemetry.

Test Configuration:

- Zone / Region: [Name or coordinates]

- Total edges to traverse: [(k)]

- Solver used: [C++ backend / Python fallback]

- Total route distance: [Result]

- Estimated completion time: [Result]

- Solver execution time: [Result]

<img width="1919" height="905" alt="image" src="https://github.com/user-attachments/assets/a572a808-ecf2-4626-aaa7-9ace29f76a9b" />

*map showing the selected dump truck base location, service radius, road network segments, and the optimized Chinese Postman route.*

### Knight's Tour Simulator

The Knight's Tour Simulator is implemented in Python using Tkinter for the visualization. The solver takes the chessboard size (columns and rows) and the knight's starting position as input. The chessboard is represented as a graph, where each square is a vertex and each legal knight move is an edge.

The tour is built with backtracking guided by Warnsdorff's rule. At each step, the knight moves to the unvisited square with the fewest onward moves, which visits hard-to-reach squares such as corners first. If the knight reaches a dead end, the solver undoes the last move and tries another option. If every square is visited exactly once, the solver returns the full sequence of coordinates. Otherwise, it prints `path not found`.

The resulting tour is shown in two ways. The console prints the coordinates in visiting order, written as `column,row` with `0,0` as the top-left square. The Tkinter window animates the same tour on the chessboard, drawing the knight's path as arrows, marking each square with its move number, and highlighting the current square. The animation can be paused, restarted, skipped to the finished tour, and sped up or slowed down.

Test Configuration:

- Chessboard size: 5 × 5 (25 squares)
- Starting position: (2, 2)
- Solver used: Backtracking with Warnsdorff's rule
- Squares visited: 25 of 25
- Total moves: 24
- Final position: (4, 0)
- Solver execution time: [Result]

Console output:

```
2,2
3,4
4,2
3,0
1,1
0,3
2,4
4,3
3,1
1,0
0,2
1,4
3,3
4,1
2,0
0,1
1,3
3,2
4,4
2,3
0,4
1,2
0,0
2,1
4,0
```

<img width="585" height="792" alt="image" src="https://github.com/user-attachments/assets/baf309e6-a983-4533-b3b0-bb69adc1627a" />


*chessboard showing the starting position, the numbered visit order of each square, and the knight's path.*

## How To Run

### SPPG Simulator


### Requirements
- Python 3.10 or newer
- Internet connection (the first run downloads the Surabaya road network and school data from OpenStreetMap)

### 1. Open the TSP folder
Download the `tsp-sppg/` folder inside the  `src/task1/` (or the repository as a ZIP from GitHub and extract it), then open a terminal inside it:
```bash
cd tsp-sppg
```

### 2. Create a virtual environment
Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\activate
```
macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the simulator
```bash
python -m streamlit run app.py
```
The app opens in your browser at `http://localhost:8501`.

> **First launch:** the app downloads the road network and school locations, which can take a few minutes.
> The data is saved in the `cache/` folder, so later launches take only seconds. Keep the browser tab open until loading finishes.

### 5. Using the simulator
1. Click anywhere on the map to place the **SPPG**.
2. Set the **delivery radius (x km)** with the sidebar slider. Only state (negeri) schools inside the radius are used.
3. Click **Find TSP route**.
4. The app shows the route on the map, the school visiting order, total distance, estimated travel time, and solver execution time.

Use **Reset** in the sidebar to clear the SPPG and the route.

### Troubleshooting
| Problem | Fix |
|---|---|
| `streamlit` is not recognized | Run it as `python -m streamlit run app.py` |
| `pip install` fails | Run `python -m pip install --upgrade pip`, then try again |
| Data download fails or hangs | Check your internet connection, delete the `cache/` folder, and rerun |
| `AttributeError` from osmnx | Run `pip install -U osmnx` |

### Dump Truck Simulator 

#### Requirements
- Python 3.10 or newer
- Internet connection (roads are downloaded from OpenStreetMap the first time you press **Find CPP route**)

#### 1. Open the CPP folder
Download the `src/task2/` folder (or the repository as a ZIP from GitHub and extract it), then open a terminal inside it:
```bash
cd src/task2
```

#### 2. Create a virtual environment
Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\activate
```
macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
### Knight's Tour Simulator

**Requirements**

- Python 3.x
- Tkinter (included with the standard Python installer on Windows and macOS)

No extra packages are needed.

**1. Go to the task folder**

```bash
cd src/task3
```

**2. Run the solver**

```bash
python knights_tour.py
```

Enter the input when prompted:

```
5 5
2 2
```

| Line | Meaning |
|------|---------|
| `5 5` | Columns and rows of the chessboard |
| `2 2` | Starting position of the knight (column, row) |

The program prints the coordinates the knight visits, one per line, written as `column,row`. If no tour exists, it prints `path not found`.

**3. Run the visualization**

```bash
python knights_tour_visual.py
```

Enter the board size and starting position when prompted, for example `5 5` and then `2 2`. A window opens and animates the knight's tour.

> `knights_tour_visual.py` imports the solver, so `knights_tour.py` must be in the same folder. On macOS/Linux, use `python3` instead of `python`.
