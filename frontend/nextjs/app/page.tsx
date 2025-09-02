"use client";

import { useState, useEffect } from "react";
import {
  Play,
  BarChart3,
  Brain,
  Users,
  Settings,
  TrendingUp,
  Activity,
  Target,
} from "lucide-react";

interface SimulationResult {
  id: string;
  task_id: string;
  duration: number;
  termination_reason: string;
  agent_cost: number;
  user_cost: number;
  reward: number;
  action_checks: Array<{
    name: string;
    reward: number;
  }>;
}

interface LearningSummary {
  total_simulations: number;
  overall_success_rate: number;
  recent_success_rate: number;
  total_learning_records: number;
  improvement_suggestions: string[];
}

export default function Dashboard() {
  const [simulations, setSimulations] = useState<SimulationResult[]>([]);
  const [learningSummary, setLearningSummary] =
    useState<LearningSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch recent simulations
      const simResponse = await fetch("/api/simulations/recent");
      if (simResponse.ok) {
        const simData = await simResponse.json();
        setSimulations(simData.simulations || []);
      }

      // Fetch learning summary
      const learningResponse = await fetch("/api/learning/summary");
      if (learningResponse.ok) {
        const learningData = await learningResponse.json();
        setLearningSummary(learningData);
      }
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const runSimulation = async () => {
    try {
      const response = await fetch("/api/simulations/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          domain: "patient_intake",
          agent: "llm_agent",
          user: "user_simulator",
          num_tasks: 1,
          max_steps: 50,
          max_errors: 10,
          agent_llm: "gpt-4.1",
          user_llm: "gpt-4.1",
          num_trials: 1,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Simulation started:", result);
        // In a real app, you'd poll for status updates
        await fetchDashboardData(); // Refresh data
      }
    } catch (error) {
      console.error("Error running simulation:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-primary-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">
                SIVA Dashboard
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={runSimulation}
                className="btn-primary flex items-center"
              >
                <Play className="h-4 w-4 mr-2" />
                Run Simulation
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: "overview", label: "Overview", icon: BarChart3 },
              { id: "simulations", label: "Simulations", icon: Activity },
              { id: "learning", label: "Learning", icon: Brain },
              { id: "agents", label: "Agents", icon: Users },
              { id: "settings", label: "Settings", icon: Settings },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <tab.icon className="h-4 w-4 mr-2" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Activity className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">
                      Total Simulations
                    </p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {learningSummary?.total_simulations || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Target className="h-8 w-8 text-success-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">
                      Success Rate
                    </p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {learningSummary
                        ? `${(
                            learningSummary.overall_success_rate * 100
                          ).toFixed(1)}%`
                        : "0%"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <TrendingUp className="h-8 w-8 text-warning-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">
                      Recent Success
                    </p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {learningSummary
                        ? `${(
                            learningSummary.recent_success_rate * 100
                          ).toFixed(1)}%`
                        : "0%"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Brain className="h-8 w-8 text-primary-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">
                      Learning Records
                    </p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {learningSummary?.total_learning_records || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Simulations */}
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Recent Simulations
              </h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Task ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Duration
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Reward
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cost
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {simulations.slice(0, 5).map((sim) => (
                      <tr key={sim.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {sim.task_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {sim.duration.toFixed(1)}s
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {sim.reward.toFixed(3)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ${(sim.agent_cost + sim.user_cost).toFixed(4)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              sim.reward >= 0.8
                                ? "bg-success-100 text-success-800"
                                : sim.reward >= 0.5
                                ? "bg-warning-100 text-warning-800"
                                : "bg-error-100 text-error-800"
                            }`}
                          >
                            {sim.reward >= 0.8
                              ? "Excellent"
                              : sim.reward >= 0.5
                              ? "Good"
                              : "Needs Improvement"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Improvement Suggestions */}
            {learningSummary?.improvement_suggestions &&
              learningSummary.improvement_suggestions.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Improvement Suggestions
                  </h3>
                  <div className="space-y-3">
                    {learningSummary.improvement_suggestions.map(
                      (suggestion, index) => (
                        <div key={index} className="flex items-start">
                          <div className="flex-shrink-0">
                            <div className="h-2 w-2 bg-primary-500 rounded-full mt-2"></div>
                          </div>
                          <p className="ml-3 text-sm text-gray-700">
                            {suggestion}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}
          </div>
        )}

        {activeTab === "simulations" && (
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              All Simulations
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Task ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Reward
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {simulations.map((sim) => (
                    <tr key={sim.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {sim.task_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {sim.duration.toFixed(1)}s
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {sim.reward.toFixed(3)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${(sim.agent_cost + sim.user_cost).toFixed(4)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button className="text-primary-600 hover:text-primary-900">
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === "learning" && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Learning System Status
              </h3>
              {learningSummary && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">
                      Performance Metrics
                    </h4>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">
                          Total Simulations:
                        </dt>
                        <dd className="text-sm font-medium text-gray-900">
                          {learningSummary.total_simulations}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">
                          Overall Success Rate:
                        </dt>
                        <dd className="text-sm font-medium text-gray-900">
                          {(learningSummary.overall_success_rate * 100).toFixed(
                            1
                          )}
                          %
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-sm text-gray-500">
                          Recent Success Rate:
                        </dt>
                        <dd className="text-sm font-medium text-gray-900">
                          {(learningSummary.recent_success_rate * 100).toFixed(
                            1
                          )}
                          %
                        </dd>
                      </div>
                    </dl>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">
                      Learning Records
                    </h4>
                    <p className="text-sm text-gray-500">
                      {learningSummary.total_learning_records} records captured
                      for continuous improvement
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "agents" && (
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Agent Management
            </h3>
            <p className="text-gray-500">
              Agent configuration and optimization tools coming soon...
            </p>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              System Settings
            </h3>
            <p className="text-gray-500">
              System configuration and preferences coming soon...
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
