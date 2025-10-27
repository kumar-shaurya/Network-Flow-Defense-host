import joblib
import json
import pandas as pd
import networkx as nx
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List

from ml.features.extraction import extract_features

router = APIRouter()

# --- Model Loading ---
MODEL = None
FEATURE_COLS = None

def load_model():
    """Load model and features on startup."""
    global MODEL, FEATURE_COLS
    try:
        MODEL = joblib.load("backend/ml/models/rf_model.pkl")
        with open("backend/ml/models/feature_columns.json", 'r') as f:
            FEATURE_COLS = json.load(f)
        print("ML model and features loaded successfully.")
    except FileNotFoundError:
        print("WARNING: ML model not found. Run train.py first.")
        MODEL = None
        FEATURE_COLS = None

class MLRequest(BaseModel):
    graph: Dict[str, Any]
    source: int
    target: int
    k: int = 5 # Number of nodes to return

def get_ml_prediction_internal(graph_data, source, target, k=5):
    """
    Internal function for other modules to call.
    """
    if MODEL is None or FEATURE_COLS is None:
        return {"error": "Model not loaded", "top_k_nodes": []}
        
    # # This is the key fix: add edges="links"
    # G = nx.node_link_graph(graph_data, edges="links")
    # # G = nx.node_link_graph(graph_data)

    # Rebuild the graph manually because the frontend mutates link objects
    G = nx.Graph()
    for node in graph_data['nodes']:
        G.add_node(node['id'])
        
    for link in graph_data['links']:
        # Frontend mutates links to be objects {id: ...}, so we get the id
        src = link['source']['id'] if isinstance(link['source'], dict) else link['source']
        tgt = link['target']['id'] if isinstance(link['target'], dict) else link['target']
        G.add_edge(src, tgt)
    
    # 1. Extract features for the new graph
    try:
        features_df = extract_features(G, source, target)
    except nx.NetworkXNoPath:
        return {"error": "No path between source and target", "top_k_nodes": []}
    
    # Ensure columns are in the same order as training
    features_df = features_df[FEATURE_COLS]
    
    # 2. Get prediction probabilities
    # We want prob of class '1' (critical)
    pred_probs = MODEL.predict_proba(features_df)[:, 1]
    
    # 3. Create a series with node index
    prob_series = pd.Series(pred_probs, index=features_df.index)
    
    # 4. Get top-k nodes
    # Exclude source and target from recommendations
    prob_series = prob_series.drop([source, target], errors='ignore')
    
    # --- THIS IS THE NEW, RELATIVE FIX ---

    # 1. Check if we have any predictions at all
    if prob_series.empty:
        return {
            "top_k_nodes": [],
            "all_node_scores": {int(k): float(v) for k, v in prob_series.to_dict().items()}
        }

    # 2. Get the score of the #1 best node
    top_score = prob_series.max()

    # 3. Set a dynamic threshold. We'll include all nodes that
    #    have a score of at least 90% of the top score.
    #    This is the value you can "fine-tune" (0.90)
    relative_threshold = top_score * 0.30

    # 4. Filter the series to get all nodes above this new threshold
    final_nodes_series = prob_series[prob_series >= relative_threshold]
    
    # 5. Get the list of nodes
    final_nodes = final_nodes_series.index.tolist()
    
    # 6. Sort by probability (highest first) and honor the 'k' limit
    final_nodes.sort(key=lambda node: prob_series.get(node, 0), reverse=True)
    
    # --- JSON Conversion FIX ---
    # Convert numpy types to standard python types for JSON serialization
    
    # Convert the final list of node IDs to standard ints
    top_k_nodes = [int(node) for node in final_nodes[:k]]
    
    # Convert the scores dictionary's keys to int and values to float
    all_scores_dict = prob_series.to_dict()
    all_node_scores = {int(k): float(v) for k, v in all_scores_dict.items()}

    return {
        "top_k_nodes": top_k_nodes,
        "all_node_scores": all_node_scores
    }

@router.post("/predict")
def predict_critical_nodes(request: MLRequest):
    """
    Predicts the Top-K most critical nodes to block.
    """
    return get_ml_prediction_internal(
        request.graph, 
        request.source, 
        request.target, 
        request.k
    )