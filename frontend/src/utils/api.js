import axios from "axios";

// ✅ Use environment variable for backend URL (Render or local)
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

// Set up axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
});

// ✅ Example API functions
export const getNewGame = () => {
  return api.post("/game/new_game");
};

export const runSimulation = (graph, source, target, firewalled_nodes) => {
  return api.post("/game/simulate", {
    graph,
    source,
    target,
    firewalled_nodes,
  });
};

export const getMlSuggestion = (graph, source, target, k = 5) => {
  return api.post("/ml/predict", {
    graph,
    source,
    target,
    k,
  });
};

// ✅ Optional: helper for backend health check
export const pingServer = async () => {
  try {
    const res = await api.get("/");
    return res.data;
  } catch (err) {
    console.error("Backend unreachable:", err.message);
    return null;
  }
};
