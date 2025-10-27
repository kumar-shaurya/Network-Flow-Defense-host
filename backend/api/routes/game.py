from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from core.graph.generation import generate_graph
from core.infection.simulation import run_bfs_simulation
from core.scoring.evaluation import calculate_score

# We'll import the ML prediction function later
from .ml import get_ml_prediction_internal

router = APIRouter()

class SimulationRequest(BaseModel):
    graph: Dict[str, Any]
    source: int
    target: int
    firewalled_nodes: List[int]

@router.post("/new_game")
def get_new_game():
    """
    Generates a new graph, source, and target.
    """
    game_data = generate_graph()
    return game_data


@router.post("/simulate")
def simulate_infection(request: SimulationRequest):
    """
    Runs the simulation and returns the result and score.
    """
    # 1. Run the user's simulation
    sim_result = run_bfs_simulation(
        request.graph,
        request.source,
        request.target,
        request.firewalled_nodes
    )
    
    # 2. Get the ML's optimal picks for scoring
    # (This calls the ML model internally)
    ml_picks_data = get_ml_prediction_internal(
        request.graph, 
        request.source, 
        request.target, 
        k=5 # Get top 5 ML picks for comparison
    )
    ml_picks = ml_picks_data.get("top_k_nodes", [])
    
    # 3. Calculate the score
    score_data = calculate_score(
        sim_result["target_status"],
        request.firewalled_nodes,
        ml_picks
    )
    
    return {
        "simulation": sim_result,
        "scoring": score_data
    }