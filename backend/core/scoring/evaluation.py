def calculate_score(target_status, user_picks, ml_picks):
    """
    Calculates the player's score based on success and resources used.
    """
    if target_status == "INFECTED":
        return {
            "score": 0,
            "message": "Failure: The Critical Patient was infected."
        }
        
    # --- Scoring for successful defense ---
    base_score = 10000
    
    # 1. Penalty for resources used
    resource_penalty = len(user_picks) * 500
    
    # 2. Bonus for efficiency (comparing to ML picks)
    # We use Jaccard Similarity: (Intersection / Union)
    set_user = set(user_picks)
    set_ml = set(ml_picks)
    
    intersection = len(set_user.intersection(set_ml))
    union = len(set_user.union(set_ml))
    
    similarity_bonus = 0
    if union > 0:
        similarity = intersection / union
        similarity_bonus = int(similarity * 2000) # Max 2000 bonus points
        
    final_score = base_score - resource_penalty + similarity_bonus
    
    return {
        "score": max(0, final_score), # Ensure score doesn't go below 0
        "message": f"Success! Target is safe. Base: {base_score}, Penalty: -{resource_penalty}, ML Bonus: +{similarity_bonus}"
    }