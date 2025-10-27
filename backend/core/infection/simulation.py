from collections import deque
import networkx as nx # <-- Make sure this import is here

def run_bfs_simulation(graph_data, source, target, firewalled_nodes):
    """
    Runs a BFS simulation on the graph, stopping at firewalled nodes.
    Returns the infection order and status of the target.
    """
    
    # --- THIS IS THE FIX ---
    # Recreate graph from JSON data consistently using networkx
    # This correctly handles the graph structure sent from the frontend.
    # G = nx.node_link_graph(graph_data, edges="links")
    # Rebuild the graph manually because the frontend mutates link objects
    G = nx.Graph()
    for node in graph_data['nodes']:
        G.add_node(node['id'])
        
    for link in graph_data['links']:
        # Frontend mutates links to be objects {id: ...}, so we get the id
        src = link['source']['id'] if isinstance(link['source'], dict) else link['source']
        tgt = link['target']['id'] if isinstance(link['target'], dict) else link['target']
        G.add_edge(src, tgt)

    # Now we must manually recreate the adjacency list `adj`
    adj = {node: list(G.neighbors(node)) for node in G.nodes()}
    
    # Get adjacency list directly from the graph object
    adj = G.adj
    # --- END OF FIX ---
        
    queue = deque([source])
    infected = {source}
    infection_order = [source] # Order of infection
    
    target_status = "SAFE"
    
    if source in firewalled_nodes:
        # Source was firewalled, infection doesn't even start
        return {
            "status": "STOPPED_AT_SOURCE",
            "infection_order": [source],
            "infected_nodes": [source],
            "target_status": target_status
        }
    
    while queue:
        current_node = queue.popleft()
        
        if current_node == target:
            target_status = "INFECTED"
            # We don't stop, let the infection spread fully
            
        # This loop now works correctly because 'adj' is a networkx
        # adjacency view, and 'neighbor' will be the node ID (e.g., 3)
        for neighbor in adj[current_node]:
            if neighbor not in infected:
                # Check for firewall
                if neighbor in firewalled_nodes:
                    infected.add(neighbor) # Mark as infected to avoid re-check
                    # Don't add to queue, spread stops here
                else:
                    infected.add(neighbor)
                    infection_order.append(neighbor)
                    queue.append(neighbor)
                    
    return {
        "status": "COMPLETED",
        "infection_order": infection_order,
        "infected_nodes": list(infected),
        "target_status": target_status
    }

