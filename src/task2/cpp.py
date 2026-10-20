"""
Task 2: Chinese Postman Problem (CPP) solver.

Goal: find the shortest closed route that drives along EVERY road (edge)
at least once and returns to the start (the dump truck base).

Idea for a DIRECTED road network (what the assignment asks for):
  1. A closed route that uses every edge exactly once exists only if, at every
     intersection, the number of roads coming in equals the number going out.
  2. Real roads are not balanced, so we must repeat some roads. We choose the
     cheapest set of roads to repeat using a min-cost flow:
       - an intersection with MORE roads coming in than going out has a
         surplus of "arrivals", so it must send extra traversals out
         (it is a supply node);
       - an intersection with MORE roads going out needs extra traversals
         coming in (it is a demand node).
  3. After adding those repeated roads, every intersection is balanced, so an
     Euler circuit exists. We build it with Hierholzer's algorithm
     (networkx.eulerian_circuit).

For an UNDIRECTED graph (like the example on the slide) the balancing step is
different: pair up the odd-degree nodes with minimum total distance.
Both versions are in this file.
"""

import math
import time

import networkx as nx

# Road types the assignment wants us to cover.
MAJOR_ROADS = {
    "trunk", "primary", "secondary", "tertiary",
    "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}


# --------------------------------------------------------------------------
# Preparing the road network (used by the map app)
# --------------------------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2):
    """Straight-line distance in meters between two lat/lon points."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def is_major(highway):
    """OSM 'highway' can be a string or a list of strings."""
    if isinstance(highway, (list, tuple, set)):
        return any(h in MAJOR_ROADS for h in highway)
    return highway in MAJOR_ROADS


def prepare_graph(G, base_lat, base_lon, radius_km):
    """
    From a full OSMnx road graph (MultiDiGraph) build the graph the truck must cover:
      - keep only trunk/primary/secondary/tertiary roads,
      - keep only roads whose both ends are within radius_km of the base,
      - keep the largest strongly connected part (a closed route needs it;
        the brief says unconnected segments may be ignored),
      - snap the base to the nearest intersection of that part.
    Returns (H, base_node).
    """
    radius_m = radius_km * 1000.0

    inside = set()
    for n, d in G.nodes(data=True):
        if haversine_m(base_lat, base_lon, d["y"], d["x"]) <= radius_m:
            inside.add(n)

    H = nx.MultiDiGraph()
    H.graph.update(G.graph)
    for u, v, k, d in G.edges(keys=True, data=True):
        if u in inside and v in inside and u != v and is_major(d.get("highway")):
            H.add_node(u, **G.nodes[u])
            H.add_node(v, **G.nodes[v])
            H.add_edge(u, v, key=k, **d)

    if H.number_of_edges() == 0:
        raise ValueError("No trunk/primary/secondary/tertiary roads inside this radius.")

    largest = max(nx.strongly_connected_components(H), key=len)
    H = H.subgraph(largest).copy()
    if H.number_of_edges() == 0:
        raise ValueError("No connected set of major roads around this base. Try a bigger radius.")

    base = min(
        H.nodes,
        key=lambda n: haversine_m(base_lat, base_lon, H.nodes[n]["y"], H.nodes[n]["x"]),
    )
    return H, base


# --------------------------------------------------------------------------
# Directed CPP
# --------------------------------------------------------------------------

def solve_directed_cpp(H, base, weight="length"):
    """
    H: nx.MultiDiGraph that is strongly connected, each edge has `weight` (meters).
    Returns a dict with the route and its statistics.
    """
    t0 = time.perf_counter()

    if base not in H:
        raise ValueError("Base node is not in the graph.")
    if not nx.is_strongly_connected(H):
        raise ValueError("Directed CPP needs a strongly connected graph.")

    # Cheapest parallel edge for every (u, v): extra traversals use that one.
    cheapest = {}
    for u, v, k, d in H.edges(keys=True, data=True):
        w = d.get(weight, 0.0)
        if (u, v) not in cheapest or w < cheapest[(u, v)][0]:
            cheapest[(u, v)] = (w, k)

    # Min-cost flow network. Costs are integers (decimeters) so the result is exact.
    F = nx.DiGraph()
    for (u, v), (w, _k) in cheapest.items():
        if u != v:
            F.add_edge(u, v, cost=int(round(w * 10)))
    for n in H.nodes:
        F.add_node(n)
        # out - in > 0: needs extra arrivals (demand). out - in < 0: must send extra (supply).
        F.nodes[n]["demand"] = H.out_degree(n) - H.in_degree(n)

    flow = nx.min_cost_flow(F, demand="demand", weight="cost")

    # Add the repeated roads.
    E = nx.MultiDiGraph(H)
    repeated_m = 0.0
    repeats = 0
    for u, targets in flow.items():
        for v, f in targets.items():
            if f > 0:
                w, k = cheapest[(u, v)]
                data = dict(H[u][v][k])
                data["repeated"] = True
                for _ in range(f):
                    E.add_edge(u, v, **data)
                    repeated_m += w
                    repeats += 1

    if not nx.is_eulerian(E):
        raise RuntimeError("Internal error: graph is not Eulerian after balancing.")

    steps = []
    for u, v, k in nx.eulerian_circuit(E, source=base, keys=True):
        d = E[u][v][k]
        steps.append({
            "from": u,
            "to": v,
            "name": _street_name(d),
            "length_m": float(d.get(weight, 0.0)),
            "repeated": bool(d.get("repeated", False)),
            "geometry": d.get("geometry"),
        })

    # The Euler circuit marks repeats by edge key, so recount repeated steps from E.
    total_m = sum(s["length_m"] for s in steps)
    required_m = sum(d.get(weight, 0.0) for _, _, d in H.edges(data=True))

    return {
        "route": steps,
        "total_m": total_m,
        "required_m": required_m,
        "repeated_m": total_m - required_m,
        "n_edges": H.number_of_edges(),
        "n_repeats": repeats,
        "solver_seconds": time.perf_counter() - t0,
    }


def _street_name(d):
    name = d.get("name")
    if isinstance(name, (list, tuple)):
        name = ", ".join(str(x) for x in name)
    return name or "(unnamed road)"


# --------------------------------------------------------------------------
# Undirected CPP (for the example on the slide)
# --------------------------------------------------------------------------

def solve_undirected_cpp(G, base, weight="length"):
    """
    G: nx.Graph or nx.MultiGraph, connected, each edge has `weight`.
    Pairs up odd-degree nodes with minimum total distance, then builds an Euler circuit.
    """
    t0 = time.perf_counter()
    M = nx.MultiGraph(G)

    if not nx.is_connected(M):
        raise ValueError("Undirected CPP needs a connected graph.")

    cheapest = {}
    for u, v, k, d in M.edges(keys=True, data=True):
        w = d.get(weight, 0.0)
        key = frozenset((u, v))
        if key not in cheapest or w < cheapest[key][0]:
            cheapest[key] = (w, u, v, k)

    simple = nx.Graph()
    for key, (w, u, v, _k) in cheapest.items():
        if u != v:
            simple.add_edge(u, v, **{weight: w})

    odd = [n for n in M.nodes if M.degree(n) % 2 == 1]

    paths = {}
    dists = {}
    for a in odd:
        d_a, p_a = nx.single_source_dijkstra(simple, a, weight=weight)
        dists[a] = d_a
        paths[a] = p_a

    E = nx.MultiGraph(M)
    if odd:
        K = nx.Graph()
        for i, a in enumerate(odd):
            for b in odd[i + 1:]:
                K.add_edge(a, b, w=dists[a][b])
        matching = nx.min_weight_matching(K, weight="w")
        for a, b in matching:
            path = paths[a][b]
            for x, y in zip(path, path[1:]):
                w, u, v, k = cheapest[frozenset((x, y))]
                data = dict(M[u][v][k])
                data["repeated"] = True
                E.add_edge(x, y, **data)

    steps = []
    for u, v, k in nx.eulerian_circuit(E, source=base, keys=True):
        d = E[u][v][k]
        steps.append({
            "from": u,
            "to": v,
            "name": _street_name(d),
            "length_m": float(d.get(weight, 0.0)),
            "repeated": bool(d.get("repeated", False)),
            "geometry": d.get("geometry"),
        })

    total_m = sum(s["length_m"] for s in steps)
    required_m = sum(d.get(weight, 0.0) for _, _, d in M.edges(data=True))
    return {
        "route": steps,
        "total_m": total_m,
        "required_m": required_m,
        "repeated_m": total_m - required_m,
        "n_edges": M.number_of_edges(),
        "n_repeats": len(odd) // 2,
        "solver_seconds": time.perf_counter() - t0,
    }


# --------------------------------------------------------------------------
# Travel time
# --------------------------------------------------------------------------

def estimated_minutes(total_m, speed_kmh=30.0):
    """Assumption: the truck drives at a constant speed (default 30 km/h)."""
    return (total_m / 1000.0) / speed_kmh * 60.0


# --------------------------------------------------------------------------
# Small demo: the example from the assignment slide (answer: 69)
# --------------------------------------------------------------------------

if __name__ == "__main__":
    g = nx.MultiGraph()
    for a, b, w in [("A", "C", 6), ("C", "B", 12), ("B", "D", 7),
                    ("B", "E", 17), ("D", "E", 18), ("A", "D", 2)]:
        g.add_edge(a, b, length=w)
    res = solve_undirected_cpp(g, "A")
    print("Slide example, total cost:", res["total_m"], "(expected 69)")
    print("Route:", " -> ".join([res["route"][0]["from"]] + [s["to"] for s in res["route"]]))
