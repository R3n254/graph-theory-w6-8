# Graph Theory Coding Task (Week 6–8)

## Team Members
| Name | NRP | Kelas |
| --- | --- | --- |
| Ahmad Farras Favian Al Efasi | 5025251005 | IUP |
| Daniel Pedrosaputra| 5025251... | IUP |


## Introduction

this project implements three graph theory problems: the Travelling Salesman Problem (TSP), Chinese Postman Problem (CPP), and Knight’s Tour.

TSP finds an efficient route that visits every destination exactly once and returns to the starting point. CPP minimizes the cost of traversing every required road at least once, while Knight’s Tour finds a sequence of legal knight moves that visits every chessboard square exactly once.

The project applies these problems to real-world scenarios, including MBG meal delivery and DLH garbage collection in Surabaya. It explores pathfinding algorithms, route optimization, computational complexity, and solution performance.

## Algorithms

###Travelling Salesman Problem (TSP)###

The Travelling Salesman Problem (TSP) finds the shortest closed route that visits every selected school exactly once and returns to the SPPG. This project applies TSP to MBG mealbox delivery in Surabaya using a weighted directed road network, where edge weights represent road distances and may differ by direction.

Dijkstra’s algorithm calculates the shortest road distances between the SPPG and selected schools to build an asymmetric distance matrix. The TSP solver then determines the delivery order and expands each route into its corresponding road paths.

Algorithms:

**Held–Karp (up to 12 schools)**: Uses dynamic programming to find the optimal tour, with time complexity (O(2^k k^2)).

**Nearest Neighbour + 2-opt/Or-opt (larger instances)**: Builds an initial tour and improves it by rearranging stops. A time-limited search keeps the best tour found.

The simulator displays the delivery route, visit order, total distance, estimated travel time, and algorithm execution time.
