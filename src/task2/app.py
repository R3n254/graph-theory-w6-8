"""
Task 2 - Dump Truck Route Simulator (Chinese Postman Problem) on Surabaya.

Run:  streamlit run app.py

How to use:
  1. Click anywhere on the map to place the dump truck base (or type lat/lon in the sidebar).
  2. Set the radius (km) in the sidebar.
  3. Press "Find CPP route".
"""

import time

import folium
import networkx as nx
import osmnx as ox
import streamlit as st
from streamlit_folium import st_folium

from cpp_solver import (
    estimated_minutes,
    prepare_graph,
    solve_directed_cpp,
)

# Surabaya city center (Tugu Pahlawan area) as the default base.
DEFAULT_LAT, DEFAULT_LON = -7.2459, 112.7378
MAX_RADIUS_KM = 6.0

st.set_page_config(page_title="Dump Truck CPP - Surabaya", layout="wide")
st.title("Dump Truck Route Simulator (Chinese Postman Problem)")


# --------------------------------------------------------------------------
# Data loading (cached so it only downloads once)
# --------------------------------------------------------------------------

@st.cache_resource(show_spinner="Downloading road network around the base (first time only)...")
def load_roads(lat, lon, dist_m):
    """Directed drive network around (lat, lon). Cached by rounded coordinates."""
    ox.settings.use_cache = True
    ox.settings.log_console = False
    # Only the road classes we need keeps the download small and fast.
    cf = '["highway"~"trunk|primary|secondary|tertiary|trunk_link|primary_link|secondary_link|tertiary_link"]'
    return ox.graph_from_point((lat, lon), dist=dist_m, custom_filter=cf,
                               network_type="drive", simplify=True, retain_all=True)


# --------------------------------------------------------------------------
# Sidebar controls
# --------------------------------------------------------------------------

if "base" not in st.session_state:
    st.session_state.base = (DEFAULT_LAT, DEFAULT_LON)
if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.header("Settings")
    radius_km = st.slider("Delivery radius x (km)", 0.5, MAX_RADIUS_KM, 1.5, 0.5)
    speed = st.number_input("Assumed truck speed (km/h)", 5.0, 80.0, 30.0, 1.0,
                            help="Used only for the estimated travel time.")
    st.caption("Base location (click the map to change it):")
    lat_in = st.number_input("Latitude", value=float(st.session_state.base[0]), format="%.6f")
    lon_in = st.number_input("Longitude", value=float(st.session_state.base[1]), format="%.6f")
    if (lat_in, lon_in) != tuple(st.session_state.base):
        st.session_state.base = (lat_in, lon_in)
        st.session_state.result = None
    run = st.button("Find CPP route", type="primary", use_container_width=True)

base_lat, base_lon = st.session_state.base

# --------------------------------------------------------------------------
# Solve
# --------------------------------------------------------------------------

if run:
    try:
        with st.spinner("Loading roads..."):
            # Round the center so nearby clicks reuse the same download; add 1 km margin.
            G = load_roads(round(base_lat, 3), round(base_lon, 3), int(MAX_RADIUS_KM * 1000 + 1000))
            H, base_node = prepare_graph(G, base_lat, base_lon, radius_km)
        with st.spinner("Solving the Chinese Postman Problem..."):
            res = solve_directed_cpp(H, base_node)
        res["H"] = H
        res["base_node"] = base_node
        res["radius_km"] = radius_km
        res["speed"] = speed
        st.session_state.result = res
    except Exception as e:  # show a readable message instead of a stack trace
        st.session_state.result = None
        st.error(f"Could not compute a route: {e}")

res = st.session_state.result

# --------------------------------------------------------------------------
# Map
# --------------------------------------------------------------------------

m = folium.Map(location=[base_lat, base_lon], zoom_start=14, tiles="OpenStreetMap")
folium.Circle([base_lat, base_lon], radius=radius_km * 1000, color="#1f77b4",
              fill=True, fill_opacity=0.05, weight=2).add_to(m)

if res:
    H = res["H"]
    # Roads that must be covered (grey), then the route drawn in order in a colour gradient.
    for u, v, d in H.edges(data=True):
        geom = d.get("geometry")
        if geom is not None:
            pts = [(lat, lon) for lon, lat in geom.coords]
        else:
            pts = [(H.nodes[u]["y"], H.nodes[u]["x"]), (H.nodes[v]["y"], H.nodes[v]["x"])]
        folium.PolyLine(pts, color="#999999", weight=3, opacity=0.6).add_to(m)

    steps = res["route"]
    n = len(steps)
    for i, s in enumerate(steps):
        geom = s["geometry"]
        if geom is not None:
            pts = [(lat, lon) for lon, lat in geom.coords]
        else:
            pts = [(H.nodes[s["from"]]["y"], H.nodes[s["from"]]["x"]),
                   (H.nodes[s["to"]]["y"], H.nodes[s["to"]]["x"])]
        # Colour goes from blue (start) to red (end); repeated roads are dashed.
        frac = i / max(n - 1, 1)
        color = "#%02x%02x%02x" % (int(255 * frac), 60, int(255 * (1 - frac)))
        folium.PolyLine(
            pts, color=color, weight=5, opacity=0.9,
            dash_array="8" if s["repeated"] else None,
            tooltip=f"#{i + 1}: {s['name']} ({s['length_m']:.0f} m)",
        ).add_to(m)

folium.Marker([base_lat, base_lon], tooltip="Dump truck base",
              icon=folium.Icon(color="red", icon="truck", prefix="fa")).add_to(m)

out = st_folium(m, height=520, use_container_width=True, returned_objects=["last_clicked"])
if out and out.get("last_clicked"):
    new = (round(out["last_clicked"]["lat"], 6), round(out["last_clicked"]["lng"], 6))
    if new != tuple(st.session_state.base):
        st.session_state.base = new
        st.session_state.result = None
        st.rerun()

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------

if res:
    total_km = res["total_m"] / 1000
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total distance", f"{total_km:.2f} km")
    c2.metric("Estimated travel time", f"{estimated_minutes(res['total_m'], res['speed']):.0f} min")
    c3.metric("CPP solver time", f"{res['solver_seconds'] * 1000:.1f} ms")
    c4.metric("Repeated roads", f"{res['repeated_m'] / 1000:.2f} km")
    st.caption(
        f"{res['n_edges']} road segments to cover, {res['required_m'] / 1000:.2f} km of roads, "
        f"travel time assumes a constant {res['speed']:.0f} km/h. "
        "Blue to red = order of travel; dashed = a road driven again."
    )

    st.subheader("Street traversal order")
    rows = []
    for i, s in enumerate(res["route"], start=1):
        rows.append({
            "Step": i,
            "Street": s["name"],
            "Distance (m)": round(s["length_m"]),
            "Revisit": "yes" if s["repeated"] else "",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("Click the map to place the base, choose a radius, then press **Find CPP route**.")
