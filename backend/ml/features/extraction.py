import networkx as nx
import pandas as pd

def extract_features(G, source, target):
    """
    Extracts features for each node in the graph.
    """
    features = {}
    
    # 1. Global centrality measures
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    
    # 2. Get all nodes on *any* simple path between source and target
    # This feature is CRITICAL to match the 'minimum_node_cut' label,
    # which also considers all paths.
    nodes_on_paths = set()
    if nx.has_path(G, source, target):
        try:
            # Set a cutoff to prevent searching billions of paths on dense graphs
            # A cutoff of 10-12 on a 20-node graph is reasonable.
            cutoff = (G.number_of_nodes() // 2) + 2 
            for path in nx.all_simple_paths(G, source, target, cutoff=cutoff):
                 nodes_on_paths.update(path)
        except (nx.NetworkXNoPath, nx.NetworkXError):
            pass # No paths found or other error
            
    nodes_on_paths.discard(source)
    nodes_on_paths.discard(target)

    for node in G.nodes():
        has_path_to_target = nx.has_path(G, node, target)
        has_path_from_source = nx.has_path(G, source, node)

        features[node] = {
            "degree_centrality": degree_centrality.get(node, 0),
            "betweenness_centrality": betweenness_centrality.get(node, 0),
            "closeness_centrality": closeness_centrality.get(node, 0),
            
            # New S-T Specific Features:
            "is_on_any_path": 1 if node in nodes_on_paths else 0,
            
            "distance_from_source": nx.shortest_path_length(G, source, node) 
                                    if has_path_from_source else -1,
                                    
            "distance_to_target": nx.shortest_path_length(G, node, target) 
                                  if has_path_to_target else -1 
        }
        
    return pd.DataFrame.from_dict(features, orient='index')

def get_labels(G, source, target):
    """
    Generates labels. A node is 'critical' (1) if it's in the
    minimum node cut separating source and target.
    """
    # Min-cut is a good proxy for "critical"
    try:
        cut_set = nx.minimum_node_cut(G, source, target)
    except nx.NetworkXError:
        cut_set = set()
        
    labels = {node: (1 if node in cut_set else 0) for node in G.nodes()}
    return pd.Series(labels, name="is_critical")