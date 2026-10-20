import networkx as nx

def create_sample_graph():
    """
    Creates a sample weighted, connected, undirected graph for testing CPP.
    """
    G = nx.Graph()
    # Add weighted edges (u, v, weight)
    edges = [
        ('A', 'B', 4),
        ('A', 'C', 2),
        ('B', 'C', 1),
        ('B', 'D', 5),
        ('C', 'D', 8),
        ('C', 'E', 10),
        ('D', 'E', 2)
    ]
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    return G

def solve_chinese_postman(G):
    """
    Solves the Chinese Postman Problem for an undirected connected graph G.
    Returns:
        eulerian_circuit: List of tuples representing the optimal edge traversal route.
        total_cost: Total weight/distance of the complete tour.
    """
    # Step 1: Check if graph is already Eulerian (all nodes have even degrees)
    if nx.is_eulerian(G):
        print("Graph is Eulerian! Finding direct Eulerian circuit.")
        total_cost = sum(d['weight'] for u, v, d in G.edges(data=True))
        return list(nx.eulerian_circuit(G)), total_cost

    # Step 2: Identify all nodes with odd degree
    odd_nodes = [v for v, degree in G.degree() if degree % 2 != 0]
    print(f"Nodes with odd degree ({len(odd_nodes)}): {odd_nodes}")

    # Step 3: Find shortest path distances between all pairs of odd nodes
    odd_pairs_paths = {}
    for u in odd_nodes:
        lengths, paths = nx.single_source_dijkstra(G, u, weight='weight')
        for v in odd_nodes:
            if u != v and (v, u) not in odd_pairs_paths:
                odd_pairs_paths[(u, v)] = {'distance': lengths[v], 'path': paths[v]}

    # Step 4: Create complete graph of odd nodes to find minimum weight matching
    matching_graph = nx.Graph()
    for (u, v), data in odd_pairs_paths.items():
        matching_graph.add_edge(u, v, weight=data['distance'])

    min_matching = nx.algorithms.matching.min_weight_matching(matching_graph, weight='weight')
    print(f"Optimal pairings to duplicate: {list(min_matching)}")

    # Step 5: Construct augmented MultiGraph by duplicating edges along shortest paths
    augmented_graph = nx.MultiGraph(G)
    for u, v in min_matching:
        path_info = odd_pairs_paths.get((u, v)) or odd_pairs_paths.get((v, u))
        path = path_info['path']
        
        # Add duplicate edges along the shortest path
        for i in range(len(path) - 1):
            n1, n2 = path[i], path[i + 1]
            wt = G[n1][n2]['weight']
            augmented_graph.add_edge(n1, n2, weight=wt)

    # Step 6: Find Eulerian circuit in the augmented MultiGraph
    eulerian_circuit = list(nx.eulerian_circuit(augmented_graph))
    
    # Calculate total weight (original edges + duplicated edges)
    total_cost = sum(d['weight'] for u, v, d in augmented_graph.edges(data=True))

    return eulerian_circuit, total_cost

if __name__ == "__main__":
    # Load test graph
    graph = create_sample_graph()
    print(f"Initial Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Run Chinese Postman Algorithm
    circuit, total_distance = solve_chinese_postman(graph)
    
    print("\n--- Chinese Postman Optimal Circuit ---")
    route_str = " -> ".join([edge[0] for edge in circuit] + [circuit[-1][1]])
    print(f"Route: {route_str}")
    print(f"Total Optimal Cost/Distance: {total_distance}")
