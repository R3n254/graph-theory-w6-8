"""
TSP SPPG Simulator - Surabaya
-----------------------------
Pick an SPPG location on the map, choose a radius x km, and the app computes
an efficient closed tour (SPPG -> every school within x km -> SPPG) over the
real, directed road network of Surabaya (OpenStreetMap).

Run:  streamlit run app.py
"""
import itertools
import math
import random
import re
import time
from pathlib import Path

import folium
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

PLACE = "Surabaya, East Java, Indonesia"
CACHE = Path("cache")
CACHE.mkdir(exist_ok=True)
CENTER = (-7.2575, 112.7521)
EXACT_LIMIT = 12  # Held-Karp is used up to this many schools


# ----------------------------------------------------------------------------
# 1. DATA LOADING (OSM) - cached on disk so it is only downloaded once
# ----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading Surabaya road network (first run downloads from OSM, be patient)...")
def load_graph():
    f = CACHE / "surabaya.graphml"
    if f.exists():
        G = ox.load_graphml(f)
    else:
        G = ox.graph_from_place(PLACE, network_type="drive")
        # keep only the strongly connected part so every pair of nodes is reachable
        G = ox.truncate.largest_component(G, strongly=True)
        try:
            G = ox.routing.add_edge_speeds(G)
            G = ox.routing.add_edge_travel_times(G)
        except AttributeError:  # older osmnx
            G = ox.add_edge_speeds(G)
            G = ox.add_edge_travel_times(G)
        ox.save_graphml(G, f)
    # Road network as a simple DiGraph (keeps one-way streets, min-length parallel edge)
    try:
        D = ox.convert.to_digraph(G, weight="length")
    except AttributeError:
        D = ox.get_digraph(G, weight="length")
    return D


# State (public / "negeri") school detection ---------------------------------
# OSM tagging in Indonesia is inconsistent, so we combine two signals:
#   1. operator:type = public/government (or private -> excluded)
#   2. name pattern: SDN, SMPN, SMAN, SMKN, SLBN, MIN, MTsN, MAN, "Negeri", ...
STATE_NAME_RE = re.compile(
    r"(?<![A-Za-z])(?:SDN|SDLB|SMPN|SMAN|SMKN|SLBN|MIN|MTsN|MTSN|MAN)(?![A-Za-z])"
    r"|(?i:\bnegeri\b)"
)


def is_state_school(name, op_type):
    op = str(op_type or "").strip().lower()
    if op in ("public", "government"):
        return True
    if op == "private":
        return False
    if re.search(r"swasta", str(name), re.I):
        return False
    return bool(STATE_NAME_RE.search(str(name)))


@st.cache_data(show_spinner="Loading state school locations from OSM...")
def load_schools():
    f = CACHE / "schools_raw.pkl"  # raw OSM schools; state filter applied below
    if f.exists():
        raw = pd.read_pickle(f)
    else:
        gdf = ox.features_from_place(PLACE, tags={"amenity": "school"}).reset_index(drop=True)
        cent = gdf.to_crs(32749).geometry.centroid.to_crs(4326)  # UTM 49S (Surabaya)

        def col(c):
            return gdf[c].fillna("").astype(str).values if c in gdf.columns else [""] * len(gdf)

        raw = pd.DataFrame({
            "name": col("name"),
            "op_type": col("operator:type"),
            "lat": cent.y.values,
            "lon": cent.x.values,
        }).drop_duplicates(subset=["lat", "lon"]).reset_index(drop=True)
        raw.to_pickle(f)

    keep = raw.apply(lambda r: is_state_school(r["name"], r["op_type"]), axis=1)
    df = raw[keep].copy()
    df["name"] = df["name"].replace("", "(unnamed state school)")
    return df[["name", "lat", "lon"]].reset_index(drop=True)


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ----------------------------------------------------------------------------
# 2. SHORTEST PATHS ON THE DIGRAPH -> (asymmetric) DISTANCE MATRIX
# ----------------------------------------------------------------------------
def build_distance_matrix(G, nodes):
    n = len(nodes)
    D = np.zeros((n, n))
    for i, s in enumerate(nodes):
        dist = nx.single_source_dijkstra_path_length(G, s, weight="length")
        for j, t in enumerate(nodes):
            D[i, j] = dist.get(t, 1e12)
    return D


# ----------------------------------------------------------------------------
# 3. TSP SOLVERS (work on asymmetric matrices; index 0 = SPPG)
# ----------------------------------------------------------------------------
def tour_cost(D, tour):
    t = np.asarray(tour)
    return float(D[t[:-1], t[1:]].sum())


def held_karp(D):
    """Exact DP, O(2^m * m^2). Returns closed tour [0, ..., 0]."""
    n = len(D)
    m = n - 1
    if m == 0:
        return [0, 0]
    INF = float("inf")
    dp = [[INF] * m for _ in range(1 << m)]
    par = [[-1] * m for _ in range(1 << m)]
    for j in range(m):
        dp[1 << j][j] = D[0][j + 1]
    for mask in range(1, 1 << m):
        for j in range(m):
            if not (mask >> j) & 1 or dp[mask][j] == INF:
                continue
            for k in range(m):
                if (mask >> k) & 1:
                    continue
                nm = mask | (1 << k)
                c = dp[mask][j] + D[j + 1][k + 1]
                if c < dp[nm][k]:
                    dp[nm][k] = c
                    par[nm][k] = j
    full = (1 << m) - 1
    best, last = INF, -1
    for j in range(m):
        c = dp[full][j] + D[j + 1][0]
        if c < best:
            best, last = c, j
    order, mask = [], full
    while last != -1:
        order.append(last + 1)
        pj = par[mask][last]
        mask ^= 1 << last
        last = pj
    order.reverse()
    return [0] + order + [0]


def nearest_neighbor(D, rng=None):
    n = len(D)
    unv = set(range(1, n))
    tour = [0]
    cur = 0
    while unv:
        nxt = min(unv, key=lambda j: D[cur][j] + (rng.random() * 1e-6 if rng else 0))
        tour.append(nxt)
        unv.remove(nxt)
        cur = nxt
    tour.append(0)
    return tour


def local_search(D, tour):
    """2-opt (segment reversal) + Or-opt (move 1-3 cities), valid for asymmetric D."""
    tour = list(tour)
    best = tour_cost(D, tour)
    improved = True
    while improved:
        improved = False
        n = len(tour)
        # 2-opt
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                cand = tour[:i] + tour[i:j + 1][::-1] + tour[j + 1:]
                c = tour_cost(D, cand)
                if c < best - 1e-9:
                    tour, best, improved = cand, c, True
        # Or-opt
        for seg in (1, 2, 3):
            i = 1
            while i + seg <= len(tour) - 1:
                segment = tour[i:i + seg]
                rest = tour[:i] + tour[i + seg:]
                for pos in range(1, len(rest)):
                    if pos == i:
                        continue
                    cand = rest[:pos] + segment + rest[pos:]
                    c = tour_cost(D, cand)
                    if c < best - 1e-9:
                        tour, best, improved = cand, c, True
                        break
                i += 1
    return tour, best


def heuristic_tsp(D, time_budget=6.0, seed=42):
    """Nearest neighbour + local search with random restarts (iterated)."""
    rng = random.Random(seed)
    t0 = time.perf_counter()
    best_t, best_c = local_search(D, nearest_neighbor(D))
    while time.perf_counter() - t0 < time_budget:
        # perturbation: random double-bridge-ish shuffle of the best tour
        inner = best_t[1:-1]
        if len(inner) < 4:
            break
        a, b, c = sorted(rng.sample(range(1, len(inner)), 3))
        inner = inner[:a] + inner[b:c] + inner[a:b] + inner[c:]
        t, cst = local_search(D, [0] + inner + [0])
        if cst < best_c - 1e-9:
            best_t, best_c = t, cst
    return best_t


def solve_tsp(D):
    if len(D) - 1 <= EXACT_LIMIT:
        return held_karp(D), "Held-Karp (exact)"
    return heuristic_tsp(D), "Nearest Neighbour + 2-opt/Or-opt (iterated)"


# ----------------------------------------------------------------------------
# 4. ROUTE RECONSTRUCTION ON THE REAL ROAD NETWORK
# ----------------------------------------------------------------------------
def leg_geometry(G, path):
    """Coordinates (lat, lon) along a node path, using OSM edge geometry if present."""
    coords, dist, secs = [], 0.0, 0.0
    for u, v in zip(path[:-1], path[1:]):
        e = G[u][v]
        dist += e["length"]
        secs += e.get("travel_time", e["length"] / (30 / 3.6))
        geom = e.get("geometry")
        if geom is not None:
            pts = [(y, x) for x, y in geom.coords]
        else:
            pts = [(G.nodes[u]["y"], G.nodes[u]["x"]), (G.nodes[v]["y"], G.nodes[v]["x"])]
        coords.extend(pts)
    return coords, dist, secs


def build_route(G, nodes, tour):
    full_coords, legs = [], []
    total_d = total_t = 0.0
    for a, b in zip(tour[:-1], tour[1:]):
        if nodes[a] == nodes[b]:
            legs.append((0.0, 0.0))
            continue
        path = nx.shortest_path(G, nodes[a], nodes[b], weight="length")
        coords, d, s = leg_geometry(G, path)
        full_coords.extend(coords)
        legs.append((d, s))
        total_d += d
        total_t += s
    return full_coords, total_d, total_t, legs


# ----------------------------------------------------------------------------
# 5. STREAMLIT UI
# ----------------------------------------------------------------------------
st.set_page_config(page_title="TSP SPPG Simulator", layout="wide")
st.title("🍱 TSP SPPG Simulator — MBG Delivery, Surabaya")

G = load_graph()
schools = load_schools()

if "sppg" not in st.session_state:
    st.session_state.sppg = None
if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.header("Settings")
    radius = st.slider("Delivery radius x (km)", 0.5, 15.0, 3.0, 0.5)
    st.caption("Click the map to place the SPPG. Schools inside the radius "
               "(straight-line distance) are visited. Only state (negeri) schools are used.")
    run = st.button("🚚 Find TSP route", type="primary", use_container_width=True)
    if st.button("Reset", use_container_width=True):
        st.session_state.sppg = None
        st.session_state.result = None
    st.markdown(f"**State schools loaded:** {len(schools)}  \n**Graph:** {G.number_of_nodes():,} nodes, "
                f"{G.number_of_edges():,} directed edges")

# Schools inside radius
in_radius = pd.DataFrame()
if st.session_state.sppg:
    sl, sn = st.session_state.sppg
    d = schools.apply(lambda r: haversine_km(sl, sn, r.lat, r.lon), axis=1)
    in_radius = schools[d <= radius].copy()

# Solve
if run:
    if not st.session_state.sppg:
        st.warning("Click on the map first to choose the SPPG location.")
    elif in_radius.empty:
        st.warning("No schools within this radius. Increase the radius.")
    else:
        with st.spinner(f"Computing shortest paths and TSP for {len(in_radius)} schools..."):
            sl, sn = st.session_state.sppg
            nodes = [ox.distance.nearest_nodes(G, X=sn, Y=sl)]
            nodes += list(ox.distance.nearest_nodes(G, X=in_radius.lon.values, Y=in_radius.lat.values))
            Dm = build_distance_matrix(G, nodes)
            t0 = time.perf_counter()
            tour, algo = solve_tsp(Dm)
            solve_time = time.perf_counter() - t0
            coords, td, tt, legs = build_route(G, nodes, tour)
            st.session_state.result = dict(
                tour=tour, algo=algo, solve_time=solve_time, coords=coords,
                dist=td, secs=tt, legs=legs, schools=in_radius.reset_index(drop=True),
                sppg=st.session_state.sppg, radius=radius)

res = st.session_state.result

# Map
m = folium.Map(location=st.session_state.sppg or CENTER, zoom_start=13 if not st.session_state.sppg else 14,
               tiles="OpenStreetMap")
if st.session_state.sppg:
    folium.Marker(st.session_state.sppg, tooltip="SPPG",
                  icon=folium.Icon(color="red", icon="home")).add_to(m)
    folium.Circle(st.session_state.sppg, radius=radius * 1000, color="red", fill=True,
                  fill_opacity=0.05).add_to(m)
for _, r in in_radius.iterrows():
    folium.CircleMarker((r.lat, r.lon), radius=5, color="blue", fill=True,
                        tooltip=r["name"]).add_to(m)
if res:
    folium.PolyLine(res["coords"], color="green", weight=5, opacity=0.8).add_to(m)
    for order, idx in enumerate(res["tour"][1:-1], start=1):
        r = res["schools"].iloc[idx - 1]
        folium.Marker(
            (r.lat, r.lon), tooltip=f"{order}. {r['name']}",
            icon=folium.DivIcon(html=f"""<div style="background:#1565c0;color:white;border-radius:50%;
            width:22px;height:22px;text-align:center;line-height:22px;font-size:11px;
            font-weight:bold;border:2px solid white">{order}</div>""")).add_to(m)

out = st_folium(m, height=560, width=None, returned_objects=["last_clicked"])
if out and out.get("last_clicked"):
    new = (out["last_clicked"]["lat"], out["last_clicked"]["lng"])
    if new != st.session_state.sppg:
        st.session_state.sppg = new
        st.session_state.result = None
        st.rerun()

if st.session_state.sppg:
    st.info(f"SPPG at ({st.session_state.sppg[0]:.5f}, {st.session_state.sppg[1]:.5f}) — "
            f"{len(in_radius)} school(s) within {radius} km")
else:
    st.info("👆 Click anywhere on the map to place the SPPG.")

# Results
if res:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total distance", f"{res['dist'] / 1000:.2f} km")
    h, mnt = divmod(res["secs"] / 60, 60)
    c2.metric("Estimated travel time", f"{int(h)} h {mnt:.0f} min" if h else f"{mnt:.0f} min")
    c3.metric("Schools visited", len(res["schools"]))
    c4.metric("Solver time", f"{res['solve_time'] * 1000:.1f} ms")
    st.caption(f"Algorithm: **{res['algo']}** · travel time from OSM speed limits "
               f"(no live traffic) · excludes unloading time at schools.")

    rows = [{"Order": 0, "Stop": "SPPG (start)", "Leg distance (km)": None, "Leg time (min)": None}]
    for k, idx in enumerate(res["tour"][1:-1], start=1):
        d_, s_ = res["legs"][k - 1]
        rows.append({"Order": k, "Stop": res["schools"].iloc[idx - 1]["name"],
                     "Leg distance (km)": round(d_ / 1000, 2), "Leg time (min)": round(s_ / 60, 1)})
    d_, s_ = res["legs"][-1]
    rows.append({"Order": len(res["tour"]) - 1, "Stop": "SPPG (return)",
                 "Leg distance (km)": round(d_ / 1000, 2), "Leg time (min)": round(s_ / 60, 1)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
