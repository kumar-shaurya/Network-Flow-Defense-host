import pandas as pd
import networkx as nx
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import sys
import os

# # Import from our other modules
script_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.append(backend_dir)

from core.graph.generation import generate_graph
from ml.features.extraction import extract_features, get_labels

def generate_training_data(num_graphs=200):
    """
    Generates a large dataset by creating many graphs.
    """
    all_features = []
    all_labels = []
    
    print(f"Generating {num_graphs} graphs for training data...")
    for i in range(num_graphs):
        if (i+1) % 20 == 0:
            print(f"  ...graph {i+1}/{num_graphs}")
            
        game_data = generate_graph()
        G = nx.node_link_graph(game_data['graph'], edges="links")
        source = game_data['source']
        target = game_data['target']
        
        # Check if path exists before proceeding
        if not nx.has_path(G, source, target):
            continue
            
        features = extract_features(G, source, target)
        labels = get_labels(G, source, target)
        
        all_features.append(features)
        all_labels.append(labels)
        
    print("Data generation complete.")
    
    # Combine all data
    X = pd.concat(all_features)
    y = pd.concat(all_labels)
    
    return X, y

def train_model():
    """
    Trains a Random Forest model and saves it.
    """
    X, y = generate_training_data(num_graphs=500) # Use 500 graphs
    
    # Define feature columns (important for prediction)
    feature_cols = list(X.columns)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    
    print("Model training complete.")
    
    # Test model
    y_pred = model.predict(X_test)
    print("\nModel Performance Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model and feature columns
    model_path = "ml/models/rf_model.pkl"
    features_path = "ml/models/feature_columns.json"
    
    joblib.dump(model, model_path)
    import json
    with open(features_path, 'w') as f:
        json.dump(feature_cols, f)
        
    print(f"Model saved to {model_path}")
    print(f"Features saved to {features_path}")

if __name__ == "__main__":
    # Create models directory if it doesn't exist
    import os
    os.makedirs("ml/models", exist_ok=True)
    
    train_model()