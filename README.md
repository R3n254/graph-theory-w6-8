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

## Implementation and Output

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
