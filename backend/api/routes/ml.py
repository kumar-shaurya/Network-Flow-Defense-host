import joblib
import json
import os
import pandas as pd
import networkx as nx
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from ml.features.extraction import extract_features

router = APIRouter()

# --- Model Loading ---
MODEL = None
FEATURE_COLS = None

def load_model():
    """Load model and features on startup (works on Render and locally)."""
    global MODEL, FEATURE_COLS
    try:
        # Dynamically resolve the model path regardless of working directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "../../ml/models/rf_model.pkl")
        feature_path = os.path.join(base_dir, "../../ml/models/feature_columns.json")

        # Normalize paths
        model_path = os.path.normpath(model_path)
        feature_path = os.path.normpath(feature_path)

        MODEL = joblib.load(model_path)
        with open(feature_path, 'r') as f:
            FEATURE_COLS = json.load(f)

        print(f"✅ ML model loaded from: {model_path}")
        print(f"✅ Feature columns loaded from: {feature_path}")

    except FileNotFoundError as e:
        print(f"⚠️ Model loading failed: {e}")
        MODEL = None
        FEATURE_COLS = None


class MLRequest(BaseModel):
    graph: Dict[str, Any]
    source: int
    target: int
    k: int = 5  # Number of nodes to return


def get_ml_prediction_internal(graph_data, source, target, k=5):
    """Internal function for other modules to call."""
    if MODEL is None or FEATURE_COLS is None:
        return {"error": "Model not loaded", "top_k_nodes": []}

    # Rebuild the graph manually
    G = nx.Graph()
    for node in graph_data['nodes']:
        G.add_node(node['id'])

    for link in graph_data['links']:
        src = link['source']['id'] if isinstance(link['source'], dict) else link['source']
        tgt = link['target']['id'] if isinstance(link['target'], dict) else link['target']
        G.add_edge(src, tgt)

    # 1. Extract features
    try:
        features_df = extract_features(G, source, target)
    except nx.NetworkXNoPath:
        return {"error": "No path between source and target", "top_k_nodes": []}

    # Ensure columns order
    features_df = features_df[FEATURE_COLS]

    # 2. Predict probabilities (prob of class '1')
    pred_probs = MODEL.predict_proba(features_df)[:, 1]
    prob_series = pd.Series(pred_probs, index=features_df.index)

    # 3. Drop source and target
    prob_series = prob_series.drop([source, target], errors='ignore')

    # 4. Threshold and ranking
    if prob_series.empty:
        return {
            "top_k_nodes": [],
            "all_node_scores": {int(k): float(v) for k, v in prob_series.to_dict().items()}
        }

    top_score = prob_series.max()
    relative_threshold = top_score * 0.30
    final_nodes_series = prob_series[prob_series >= relative_threshold]
    final_nodes = final_nodes_series.index.tolist()
    final_nodes.sort(key=lambda node: prob_series.get(node, 0), reverse=True)

    # 5. Convert to JSON-friendly types
    top_k_nodes = [int(node) for node in final_nodes[:k]]
    all_node_scores = {int(k): float(v) for k, v in prob_series.to_dict().items()}

    return {
        "top_k_nodes": top_k_nodes,
        "all_node_scores": all_node_scores
    }


@router.post("/predict")
def predict_critical_nodes(request: MLRequest):
    """Predicts the Top-K most critical nodes to block."""
    return get_ml_prediction_internal(
        request.graph,
        request.source,
        request.target,
        request.k
    )
