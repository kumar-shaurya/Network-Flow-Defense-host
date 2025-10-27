import React, { useState, useCallback, useRef } from 'react'; // useEffect removed
import ForceGraph2D from 'react-force-graph-2d';
import { getNewGame, runSimulation, getMlSuggestion } from './utils/api';
import './App.css';

// --- Color Constants ---
const COLORS = {
  default: '#aaa',
  source: '#ff4136', // Red
  target: '#0074d9', // Blue
  firewall: '#ff851b', // Orange
  ml_suggestion: '#2ecc40', // Green
  infected: '#b10dc9', // Purple
};

// --- Home Screen Component ---
function HomeScreen({ onStartGame }) {
  return (
    <div className="home-screen">
      <div className="home-content">
        <img src="/my-logo.png" alt="Logo" className="home-logo" />
        <h1>Network Flow Defence</h1>
        <p>A "Patient Zero" (red) is trying to infect a "Critical Patient" (blue).</p>
        <p>Your job is to build firewalls on nodes to stop the infection before it reaches the target.</p>
        <button className="btn btn-primary btn-large" onClick={onStartGame}>
          Start Game
        </button>
      </div>
    </div>
  );
}

// --- Modal Component ---
function Modal({
  isOpen,
  title,
  message,
  score,
  success,
  onNextLevel,
  onRetry,
  onClose,
}) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>{title}</h2>
        {score !== null && <h3>Score: {score}</h3>}
        <p>{message}</p>
        <div className="modal-buttons">
          {success ? (
            <button className="btn btn-success" onClick={onNextLevel}>
              Next Level
            </button>
          ) : (
            <>
              <button className="btn btn-warning" onClick={onRetry}>
                Retry Level
              </button>
              <button className="btn btn-secondary" onClick={onClose}>
                Main Menu
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Main App Component ---
function App() {
  const [gameState, setGameState] = useState('HOME'); // 'HOME' | 'PLAYING'
  const [level, setLevel] = useState(1);
  const [totalScore, setTotalScore] = useState(0);

  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [sourceNode, setSourceNode] = useState(null);
  const [targetNode, setTargetNode] = useState(null);
  const [selectedNodes, setSelectedNodes] = useState(new Set());
  const [mlSuggestions, setMlSuggestions] = useState(new Set());
  
  // --- Unused variables removed ---
  const [gameMessage, setGameMessage] = useState('Loading...');
  // const [simulationResult, setSimulationResult] = useState(null); // Removed
  // const [scoringResult, setScoringResult] = useState(null); // Removed
  
  const [isSimulating, setIsSimulating] = useState(false);
  const [infectedNodes, setInfectedNodes] = useState(new Set());

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState({
    title: '',
    message: '',
    score: null,
    success: false,
  });

  const fgRef = useRef();

  // Load a new game (a new level)
  const newGame = useCallback(() => {
    setIsSimulating(false);
    // setSimulationResult(null); // No longer needed
    // setScoringResult(null); // No longer needed
    setSelectedNodes(new Set());
    setMlSuggestions(new Set());
    setInfectedNodes(new Set());
    setGameMessage('Loading new level...');

    getNewGame()
      .then((response) => {
        const { graph, source, target } = response.data;
        graph.nodes.forEach((node) => {
          node.val = 8; // node size
        });
        setGraphData(graph);
        setSourceNode(source);
        setTargetNode(target);
        setGameMessage('Level loaded. Place your firewalls.');
      })
      .catch((err) => {
        console.error(err);
        setGameMessage('Error loading game. Please try again.');
      });
  }, []);

  // Start a brand new game from the home screen
  const startGame = () => {
    setLevel(1);
    setTotalScore(0);
    setGameState('PLAYING');
    newGame();
  };

  // Return to the home screen
  const goHome = () => {
    setGameState('HOME');
  };

  // Handle clicking on a node
  const handleNodeClick = useCallback(
    (node) => {
      if (isSimulating || node.id === sourceNode || node.id === targetNode) {
        return;
      }
      const newSelectedNodes = new Set(selectedNodes);
      if (newSelectedNodes.has(node.id)) {
        newSelectedNodes.delete(node.id);
      } else {
        newSelectedNodes.add(node.id);
      }
      setSelectedNodes(newSelectedNodes);
    },
    [selectedNodes, sourceNode, targetNode, isSimulating]
  );

  // Get ML Suggestions
  const fetchMlSuggestions = () => {
    setGameMessage('Calculating ML suggestions...');
    getMlSuggestion(graphData, sourceNode, targetNode, 5)
      .then((response) => {
        setMlSuggestions(new Set(response.data.top_k_nodes));
        setGameMessage('ML suggestions loaded.');
      })
      .catch((err) => {
        console.error(err);
        setGameMessage('Error getting ML suggestions.');
      });
  };

  // Run the Simulation
  const handleRunSimulation = () => {
    setIsSimulating(true);
    setGameMessage('Simulation running...');
    setInfectedNodes(new Set([sourceNode]));
    setMlSuggestions(new Set());
    // setSimulationResult(null); // No longer needed
    // setScoringResult(null); // No longer needed

    runSimulation(
      graphData,
      sourceNode,
      targetNode,
      Array.from(selectedNodes)
    )
      .then((response) => {
        const { simulation, scoring } = response.data;
        // setSimulationResult(simulation); // No longer needed
        // setScoringResult(scoring); // No longer needed

        // --- Animate the result ---
        const { infection_order } = simulation;
        if (infection_order.length <= 1) {
          handleSimulationEnd(scoring);
          return;
        }

        infection_order.forEach((nodeId, index) => {
          setTimeout(() => {
            setInfectedNodes((prev) => new Set(prev).add(nodeId));
            if (index === infection_order.length - 1) {
              handleSimulationEnd(scoring);
            }
          }, index * 200); // 200ms delay per step
        });
      })
      .catch((err) => {
        console.error(err);
        setIsSimulating(false);
        setGameMessage('Error running simulation.');
      });
  };

  // Handle the end of a simulation
  const handleSimulationEnd = (scoring) => {
    if (scoring.score > 0) {
      setModalContent({
        title: 'Yayy! Level Complete!',
        message: scoring.message,
        score: scoring.score,
        success: true,
      });
    } else {
      setModalContent({
        title: 'Oh no! Target Infected!',
        message: scoring.message,
        score: scoring.score,
        success: false,
      });
    }
    setIsModalOpen(true); // Open the modal
  };

  // --- Modal Button Handlers ---
  const handleNextLevel = () => {
    setTotalScore((prevScore) => prevScore + modalContent.score);
    setLevel((prevLevel) => prevLevel + 1);
    setIsModalOpen(false);
    newGame();
  };

  const handleRetry = () => {
    setIsModalOpen(false);
    setIsSimulating(false);
    // setSimulationResult(null); // No longer needed
    // setScoringResult(null); // No longer needed
    setSelectedNodes(new Set());
    setInfectedNodes(new Set());
    setGameMessage('Try again! Place your firewalls.');
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    goHome();
  };

  // --- Node Coloring Logic ---
  const getNodeColor = useCallback(
    (node) => {
      if (infectedNodes.has(node.id)) {
        return COLORS.infected;
      }
      if (node.id === sourceNode) {
        return COLORS.source;
      }
      if (node.id === targetNode) {
        return COLORS.target;
      }
      if (selectedNodes.has(node.id)) {
        return COLORS.firewall;
      }
      if (mlSuggestions.has(node.id)) {
        return COLORS.ml_suggestion;
      }
      return COLORS.default;
    },
    [infectedNodes, sourceNode, targetNode, selectedNodes, mlSuggestions]
  );

  // --- Main Render ---

  if (gameState === 'HOME') {
    return <HomeScreen onStartGame={startGame} />;
  }

  return (
    <div className="App">
      <Modal
        isOpen={isModalOpen}
        {...modalContent}
        onNextLevel={handleNextLevel}
        onRetry={handleRetry}
        onClose={handleModalClose}
      />

      <header>
        <div className="header-left">
          <img src="/my-logo.png" alt="Logo" style={{ height: '50px' }} />
          <button className="btn btn-secondary" onClick={goHome}>
            Main Menu
          </button>
        </div>
        <div className="score-display">
          <div>Level: <strong>{level}</strong></div>
          <div>Total Score: <strong>{totalScore}</strong></div>
        </div>
      </header>

      <div className="game-container">
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          nodeColor={getNodeColor}
          linkColor={() => '#555'}
          linkWidth={2}
          onNodeClick={handleNodeClick}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.id;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const color = getNodeColor(node);
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
            ctx.fill();
            ctx.fillStyle = '#fff';
            ctx.fillText(label, node.x, node.y);
          }}
          nodeCanvasObjectMode={() => 'after'}
          autoPauseRedraw={false}
        />

        <div className="floating-controls">
          <h2>Controls</h2>
          <p><strong>Status:</strong> {gameMessage}</p>
          <button
            className="btn btn-primary"
            onClick={handleRunSimulation}
            disabled={isSimulating}
          >
            {isSimulating ? 'Simulating...' : 'Run Simulation'}
          </button>
          <button
            className="btn btn-warning"
            onClick={fetchMlSuggestions}
            disabled={isSimulating}
          >
            Get ML Suggestion
          </button>
          <hr />
          <h2>Legend</h2>
          <ul className="legend">
            <li><div className="legend-color" style={{backgroundColor: COLORS.source}}></div> Patient Zero (Source)</li>
            <li><div className="legend-color" style={{backgroundColor: COLORS.target}}></div> Critical Patient (Target)</li>
            <li><div className="legend-color" style={{backgroundColor: COLORS.firewall}}></div> Your Firewall</li>
            <li><div className="legend-color" style={{backgroundColor: COLORS.ml_suggestion}}></div> ML Suggestion</li>
            <li><div className="legend-color" style={{backgroundColor: COLORS.infected}}></div> Infected Node</li>
            <li><div className="legend-color" style={{backgroundColor: COLORS.default}}></div> Safe Node</li>
          </ul>
        </div>

      </div>
    </div>
  );
}

export default App;