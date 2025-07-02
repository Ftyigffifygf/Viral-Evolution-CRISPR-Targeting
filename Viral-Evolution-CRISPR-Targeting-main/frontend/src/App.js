import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("upload");
  const [sequence, setSequence] = useState("");
  const [sequenceName, setSequenceName] = useState("");
  const [virusType, setVirusType] = useState("HIV-1");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [samples, setSamples] = useState({});
  const [sequenceId, setSequenceId] = useState(null);
  const [mutationSim, setMutationSim] = useState({
    mutation_rate: 0.001,
    generations: 100
  });
  const [simulationResult, setSimulationResult] = useState(null);

  useEffect(() => {
    loadSamples();
  }, []);

  const loadSamples = async () => {
    try {
      const response = await axios.get(`${API}/samples`);
      setSamples(response.data);
    } catch (error) {
      console.error("Error loading samples:", error);
    }
  };

  const loadSampleSequence = async (virusType) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/samples/load/${virusType}`);
      const sampleData = response.data;
      setSequence(sampleData.sequence);
      setSequenceName(sampleData.name);
      setVirusType(sampleData.virus_type);
      setSequenceId(sampleData.id);
      setLoading(false);
    } catch (error) {
      console.error("Error loading sample:", error);
      setLoading(false);
    }
  };

  const uploadSequence = async () => {
    if (!sequence || !sequenceName) {
      alert("Please provide sequence name and sequence data");
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API}/sequence/upload`, {
        name: sequenceName,
        sequence: sequence,
        virus_type: virusType
      });
      setSequenceId(response.data.id);
      setLoading(false);
      alert("Sequence uploaded successfully!");
    } catch (error) {
      console.error("Error uploading sequence:", error);
      setLoading(false);
      alert("Error uploading sequence");
    }
  };

  const analyzeSequence = async () => {
    if (!sequenceId) {
      alert("Please upload a sequence first");
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API}/sequence/analyze/${sequenceId}`);
      setAnalysisResult(response.data);
      setLoading(false);
      setActiveTab("results");
    } catch (error) {
      console.error("Error analyzing sequence:", error);
      setLoading(false);
      alert("Error analyzing sequence");
    }
  };

  const simulateMutations = async () => {
    if (!sequence) {
      alert("Please provide a sequence first");
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API}/simulate/mutation`, {
        original_sequence: sequence,
        mutation_rate: parseFloat(mutationSim.mutation_rate),
        generations: parseInt(mutationSim.generations)
      });
      setSimulationResult(response.data);
      setLoading(false);
      setActiveTab("simulation");
    } catch (error) {
      console.error("Error simulating mutations:", error);
      setLoading(false);
      alert("Error simulating mutations");
    }
  };

  const getEscapeRiskColor = (probability) => {
    if (probability < 0.3) return "text-green-600 bg-green-100";
    if (probability < 0.6) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getConservationColor = (score) => {
    if (score > 0.8) return "text-green-600 bg-green-100";
    if (score > 0.6) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🧬 Viral Evolution CRISPR Targeting
          </h1>
          <p className="text-lg text-gray-600">
            Predict escape-resistant CRISPR targets in highly mutable viruses
          </p>
        </div>

        {/* Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg shadow-md p-1">
            {["upload", "results", "simulation"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-2 rounded-md font-medium transition-colors ${
                  activeTab === tab
                    ? "bg-blue-500 text-white"
                    : "text-gray-600 hover:text-blue-500"
                }`}
              >
                {tab === "upload" && "📤 Upload & Analyze"}
                {tab === "results" && "📊 Results"}
                {tab === "simulation" && "🧪 Mutation Simulation"}
              </button>
            ))}
          </div>
        </div>

        {/* Upload Tab */}
        {activeTab === "upload" && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">Sample Sequences</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {Object.keys(samples).map((virusType) => (
                  <button
                    key={virusType}
                    onClick={() => loadSampleSequence(virusType)}
                    className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 transition-colors"
                    disabled={loading}
                  >
                    <div className="text-left">
                      <h3 className="font-semibold text-lg">{virusType}</h3>
                      <p className="text-gray-600 text-sm">
                        Load sample sequence for analysis
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold mb-4">Upload Viral Sequence</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sequence Name
                  </label>
                  <input
                    type="text"
                    value={sequenceName}
                    onChange={(e) => setSequenceName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter sequence name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Virus Type
                  </label>
                  <select
                    value={virusType}
                    onChange={(e) => setVirusType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="HIV-1">HIV-1</option>
                    <option value="SARS-CoV-2">SARS-CoV-2</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Viral Sequence (FASTA format)
                </label>
                <textarea
                  value={sequence}
                  onChange={(e) => setSequence(e.target.value.toUpperCase())}
                  className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder="Paste your viral sequence here (ATCG format)"
                />
              </div>

              <div className="flex gap-4">
                <button
                  onClick={uploadSequence}
                  disabled={loading || !sequence || !sequenceName}
                  className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {loading ? "Uploading..." : "Upload Sequence"}
                </button>
                
                <button
                  onClick={analyzeSequence}
                  disabled={loading || !sequenceId}
                  className="px-6 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {loading ? "Analyzing..." : "Analyze CRISPR Targets"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === "results" && (
          <div className="max-w-6xl mx-auto">
            {analysisResult ? (
              <div className="space-y-6">
                {/* Analysis Summary */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-2xl font-bold mb-4">Analysis Summary</h2>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-3xl font-bold text-blue-600">
                        {analysisResult.analysis.total_targets}
                      </div>
                      <div className="text-sm text-gray-600">Total Targets</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-3xl font-bold text-green-600">
                        {analysisResult.analysis.high_confidence_targets}
                      </div>
                      <div className="text-sm text-gray-600">High Confidence</div>
                    </div>
                    <div className="text-center p-4 bg-yellow-50 rounded-lg">
                      <div className="text-3xl font-bold text-yellow-600">
                        {(analysisResult.analysis.conservation_data.avg_conservation * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Avg Conservation</div>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-3xl font-bold text-red-600">
                        {(analysisResult.analysis.escape_analysis.avg_escape_prob * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Avg Escape Risk</div>
                    </div>
                  </div>
                  
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-2">Recommendations</h3>
                    <ul className="space-y-2">
                      {analysisResult.analysis.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-green-500 mr-2">✓</span>
                          <span className="text-gray-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* CRISPR Targets */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-2xl font-bold mb-4">CRISPR Targets</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full table-auto">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 text-left">Target Sequence</th>
                          <th className="px-4 py-2 text-left">Position</th>
                          <th className="px-4 py-2 text-left">GC%</th>
                          <th className="px-4 py-2 text-left">Conservation</th>
                          <th className="px-4 py-2 text-left">Escape Risk</th>
                          <th className="px-4 py-2 text-left">Binding</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysisResult.targets
                          .sort((a, b) => a.escape_probability - b.escape_probability)
                          .slice(0, 10)
                          .map((target, index) => (
                          <tr key={index} className="border-t">
                            <td className="px-4 py-2 font-mono text-sm">
                              {target.target_sequence}
                            </td>
                            <td className="px-4 py-2">{target.position}</td>
                            <td className="px-4 py-2">{target.gc_content.toFixed(1)}%</td>
                            <td className="px-4 py-2">
                              <span className={`px-2 py-1 rounded text-xs ${getConservationColor(target.conservation_score)}`}>
                                {(target.conservation_score * 100).toFixed(1)}%
                              </span>
                            </td>
                            <td className="px-4 py-2">
                              <span className={`px-2 py-1 rounded text-xs ${getEscapeRiskColor(target.escape_probability)}`}>
                                {(target.escape_probability * 100).toFixed(1)}%
                              </span>
                            </td>
                            <td className="px-4 py-2">{(target.binding_strength * 100).toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md p-6 text-center">
                <p className="text-gray-600">No analysis results available. Please upload and analyze a sequence first.</p>
              </div>
            )}
          </div>
        )}

        {/* Simulation Tab */}
        {activeTab === "simulation" && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">Mutation Simulation</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mutation Rate
                  </label>
                  <input
                    type="number"
                    step="0.001"
                    value={mutationSim.mutation_rate}
                    onChange={(e) => setMutationSim({...mutationSim, mutation_rate: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Generations
                  </label>
                  <input
                    type="number"
                    value={mutationSim.generations}
                    onChange={(e) => setMutationSim({...mutationSim, generations: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <button
                onClick={simulateMutations}
                disabled={loading || !sequence}
                className="px-6 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {loading ? "Simulating..." : "Simulate Mutations"}
              </button>
            </div>

            {simulationResult && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold mb-4">Simulation Results</h3>
                
                <div className="mb-6">
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-3xl font-bold text-purple-600">
                      {simulationResult.mutation_count}
                    </div>
                    <div className="text-sm text-gray-600">Mutations Generated</div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">Recent Mutations:</h4>
                    <div className="max-h-40 overflow-y-auto">
                      {simulationResult.mutations.slice(-10).map((mut, index) => (
                        <div key={index} className="text-sm p-2 bg-gray-50 rounded mb-1">
                          Gen {mut.generation}: Position {mut.position} ({mut.from} → {mut.to})
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;