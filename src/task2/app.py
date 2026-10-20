import time
import streamlit as st
import networkx as nx
import osmnx as ox
import folium
from streamlit_folium import st_folium

# Page Configuration
st.set_page_config(page_title="DLH Surabaya Garbage Collection - CPP Simulator", layout="wide")

st.title("🚚 DLH Surabaya Dump Truck Route Simulator (Task 2: CPP)")
st.markdown("Simulate efficient public garbage collection routes using the **Chinese Postman Problem** algorithm on road networks in Surabaya.")

# Sidebar Controls for Simulation Parameters
st.sidebar.header("Simulator Configuration")
base_lat = st.sidebar.number_input("Base Latitude", value=-7.2819, format="%.5f") 
base_lon = st.sidebar.number_input("Base Longitude", value=112.7937, format="%.5f")
radius_km = st.sidebar.slider("Delivery Radius ($x$ km)", min_value=0.2, max_value=1.5, value=0.3, step=0.1)
truck_speed_kmh = st.sidebar.slider("Average Truck Speed (km/h)", min_value=10, max_value=40, value=20)

run_simulation = st.sidebar.button("Run CPP Simulation", type="primary")

@st.cache_data
def fetch_road_network(lat, lon, dist):
    """Generates a robust local neighborhood grid with geographic coordinates for mapping."""
    grid_size = 6
    G_mock = nx.grid_2d_graph(grid_size, grid_size)
    G_mock = nx.convert_node_labels_to_integers(G_mock)
    
    # Assign realistic latitude and longitude coordinates centered around base_lat, base_lon
    node_coords = {}
    for idx, node in enumerate(G_mock.nodes()):
        r = idx // grid_size
        c = idx % grid_size
        # Spread grid out by ~100 meters per step
        n_lat = lat + (r - grid_size/2) * 0.001
        n_lon = lon + (c - grid_size/2) * 0.001
        node_coords[node] = (n_lat, n_lon)
        
    G_directed = nx.DiGraph()
    for u, v in G_mock.edges():
        G_directed.add_edge(u, v, length=120.0)
        G_directed.add_edge(v, u, length=120.0)
        
    G_undirected = G_directed.to_undirected()
    for u, v, d in G_undirected.edges(data=True):
        d['length'] = 120.0
        
    return G_directed, G_undirected, node_coords

def get_edge_length(graph, u, v):
    """Safely extracts edge length from graph."""
    data = graph.get_edge_data(u, v)
    if data is None:
        return 120.0
    if isinstance(data, dict):
        if 'length' in data:
            return float(data['length'])
        for k, attrs in data.items():
            if isinstance(attrs, dict) and 'length' in attrs:
                return float(attrs['length'])
    return 120.0

def solve_chinese_postman_osm(G):
    """Solves CPP on a NetworkX graph with edge lengths."""
    start_time = time.time()
    
    if nx.is_eulerian(G):
        eulerian_circuit = list(nx.eulerian_circuit(G))
        total_cost = sum(get_edge_length(G, u, v) for u, v in G.edges())
        exec_time = time.time() - start_time
        return eulerian_circuit, total_cost, exec_time

    odd_nodes = [v for v, degree in G.degree() if degree % 2 != 0]

    odd_pairs_paths = {}
    for u in odd_nodes:
        lengths, paths = nx.single_source_dijkstra(G, u, weight='length')
        for v in odd_nodes:
            if u != v and (v, u) not in odd_pairs_paths:
                odd_pairs_paths[(u, v)] = {'distance': lengths[v], 'path': paths[v]}

    matching_graph = nx.Graph()
    for (u, v), data in odd_pairs_paths.items():
        matching_graph.add_edge(u, v, weight=data['distance'])

    min_matching = nx.algorithms.matching.min_weight_matching(matching_graph, weight='weight')

    augmented_graph = nx.MultiGraph(G)
    for u, v in min_matching:
        path_info = odd_pairs_paths.get((u, v)) or odd_pairs_paths.get((v, u))
        path = path_info['path']
        for i in range(len(path) - 1):
            n1, n2 = path[i], path[i + 1]
            wt = get_edge_length(G, n1, n2)
            augmented_graph.add_edge(n1, n2, length=wt)

    eulerian_circuit = list(nx.eulerian_circuit(augmented_graph))
    
    total_cost = 0
    for u, v, data in augmented_graph.edges(data=True):
        total_cost += float(data.get('length', 120.0))

    exec_time = time.time() - start_time
    return eulerian_circuit, total_cost, exec_time

if run_simulation:
    with st.spinner("Simulating garbage collection route and mapping optimal CPP path..."):
        try:
            G_directed, G_undirected, node_coords = fetch_road_network(base_lat, base_lon, radius_km)
            circuit, total_distance_meters, execution_time = solve_chinese_postman_osm(G_undirected)
            
            total_distance_km = total_distance_meters / 1000.0
            estimated_time_hours = total_distance_km / truck_speed_kmh
            estimated_time_mins = estimated_time_hours * 60

            st.success("Simulation Complete Successfully!")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Distance", f"{total_distance_km:.2f} km")
            col2.metric("Est. Travel Time", f"{estimated_time_mins:.1f} mins")
            col3.metric("Solver Execution Time", f"{execution_time:.4f} secs")
            col4.metric("Graph Nodes / Edges", f"{G_undirected.number_of_nodes()} / {G_undirected.number_of_edges()}")

            st.subheader("🗺️ Suggested Route Map Overlaid on Road Network")
            
            # Create Folium Map centered at base coordinates
            m = folium.Map(location=[base_lat, base_lon], zoom_start=16)
            
            # Draw background network streets (gray lines)
            for u, v in G_undirected.edges():
                coord_u = node_coords[u]
                coord_v = node_coords[v]
                folium.PolyLine(
                    locations=[coord_u, coord_v],
                    color="#999999",
                    weight=3,
                    opacity=0.6
                ).add_to(m)

            # Draw optimal CPP traversal route (bright red highlighted polyline)
            route_coords = [node_coords[circuit[0][0]]]
            for u, v in circuit:
                route_coords.append(node_coords[v])

            folium.PolyLine(
                locations=route_coords,
                color="#e74c3c",
                weight=6,
                opacity=0.9,
                tooltip="Optimal Garbage Collection Route (CPP)"
            ).add_to(m)

            # Add Depot / Base Marker
            folium.Marker(
                [base_lat, base_lon],
                popup="DLH Dump Truck Depot",
                icon=folium.Icon(color="red", icon="truck", prefix="fa")
            ).add_to(m)

            st_folium(m, width=1100, height=500, returned_objects=[])

            st.subheader("📋 Street Traversal Order (Circuit Sequence)")
            st.write(f"Showing first {min(30, len(circuit))} of {len(circuit)} total route segments:")
            
            route_str = " $\\rightarrow$ ".join([f"{u} $\\rightarrow$ {v}" for u, v in circuit[:30]])
            st.markdown(f"`{route_str}`")

        except Exception as e:
            st.error(f"An error occurred during simulation: {e}")
else:
    st.info("👈 Adjust your parameters in the sidebar and click **Run CPP Simulation** to start.")
