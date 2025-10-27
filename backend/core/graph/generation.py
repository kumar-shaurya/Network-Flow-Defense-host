import networkx as nx
import random

def generate_graph(min_nodes=15, max_nodes=20):
    """
    Generates a random connected graph, assigns source and target.
    """
    num_nodes = random.randint(min_nodes, max_nodes)
    
    # Create a random graph, ensuring it's connected
    G = None
    while G is None or not nx.is_connected(G):
        G = nx.erdos_renyi_graph(num_nodes, p=0.10) # 10% density
        
    # Select source (Patient Zero) and target (Critical Patient)
    # Ensure they are not the same node and are reasonably far apart
    nodes = list(G.nodes())
    source = random.choice(nodes)
    target = random.choice(nodes)
    
    path_len = 0
    # Keep picking target until it's not the source and at least 2 hops away
    while target == source or path_len < 2:
        target = random.choice(nodes)
        if nx.has_path(G, source, target):
            path_len = nx.shortest_path_length(G, source, target)
        else:
            # This shouldn't happen in a connected graph, but as a fallback
            path_len = 0 
            
    # Prepare graph data for JSON output (React-friendly)
    # This is the key fix: add edges="links"
    # graph_data = nx.node_link_data(G, edges="links")
    graph_data = nx.node_link_data(G)
    
    return {
        "graph": graph_data,
        "source": source,
        "target": target
    }