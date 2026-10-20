import networkx as nx

def create_sample_graph():
    """
    Creates the exact sample weighted graph shown in Task 2 illustration (Image 1).
    Nodes: A, B, C, D, E
    Edges and Weights:
      C-A: 6, A-D: 2, D-B: 7, B-C: 12, B-E: 17, D-E: 18
    """
    G = nx.Graph()
    edges = [
        ('C', 'A', 6),
        ('A', 'D', 2),
        ('D', 'B', 7),
        ('B', 'C', 12),
        ('B', 'E', 17),
        ('D', 'E', 18)
    ]
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    return G

def solve_chinese_postman(G):
    """
    Solves the Chinese Postman Problem for an undirected connected graph G.
    """
    # 1. Check if graph is already Eulerian
    if nx.is_eulerian(G):
        print("Graph is Eulerian! Finding direct Eulerian circuit.")
        total_cost = sum(d['weight'] for u, v, d in G.edges(data=True))
        return list(nx.eulerian_circuit(G)), total_cost

    # 2. Identify odd degree vertices
    odd_nodes = [v for v, degree in G.degree() if degree % 2 != 0]
    print(f"Vertices with odd degrees ({len(odd_nodes)}): {odd_nodes}")

    # 3. Find shortest paths between all pairs of odd nodes
    odd_pairs_paths = {}
    for u in odd_nodes:
        lengths, paths = nx.single_source_dijkstra(G, u, weight='weight')
        for v in odd_nodes:
            if u != v and (v, u) not in odd_pairs_paths:
                odd_pairs_paths[(u, v)] = {'distance': lengths[v], 'path': paths[v]}

    # 4. Construct complete matching graph for odd nodes and find min weight matching
    matching_graph = nx.Graph()
    for (u, v), data in odd_pairs_paths.items():
        matching_graph.add_edge(u, v, weight=data['distance'])

    min_matching = nx.algorithms.matching.min_weight_matching(matching_graph, weight='weight')
    print(f"Optimal pairings of odd nodes to duplicate: {list(min_matching)}")

    # 5. Create augmented MultiGraph by duplicating edges along shortest matching paths
    augmented_graph = nx.MultiGraph(G)
    for u, v in min_matching:
        path_info = odd_pairs_paths.get((u, v)) or odd_pairs_paths.get((v, u))
        path = path_info['path']
        for i in range(len(path) - 1):
            n1, n2 = path[i], path[i + 1]
            wt = G[n1][n2]['weight']
            augmented_graph.add_edge(n1, n2, weight=wt)

    # 6. Find Eulerian circuit and calculate total cost safely
    eulerian_circuit = list(nx.eulerian_circuit(augmented_graph))
    
    total_cost = 0
    for u, v in augmented_graph.edges():
        edge_data = augmented_graph[u][v]
        for key in edge_data:
            total_cost += edge_data[key].get('weight', 0)

    return eulerian_circuit, total_cost

if __name__ == "__main__":
    graph = create_sample_graph()
    print(f"Original Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    circuit, total_distance = solve_chinese_postman(graph)
    
    print("\n--- Chinese Postman Optimal Circuit ---")
    route_str = " -> ".join([edge[0] for edge in circuit] + [circuit[-1][1]])
    print(f"Route: {route_str}")
    print(f"Total Optimal Cost/Distance: {total_distance}")
