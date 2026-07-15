"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { LayoutFrame } from "../../components/LayoutFrame";
import { Brain, Sparkles, AlertTriangle, ShieldCheck, Check, Play, Settings as SettingsIcon } from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";

const GRID_COLOR = "#27272a"; 
const TEXT_COLOR = "#a1a1aa"; 

export default function ForecastPage() {
  const queryClient = useQueryClient();
  const [monthsAhead, setMonthsAhead] = useState(6);
  const [modelType, setModelType] = useState("xgboost");
  const [regionFilter, setRegionFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const user = api.auth.getCurrentUser();
    if (user && user.role === "admin") {
      setIsAdmin(true);
    }
  }, []);

  const forecastFilters = {
    monthsAhead,
    modelType,
    region: regionFilter || undefined,
    category: categoryFilter || undefined,
  };

  // Run forecast query
  const { data: forecastData, isLoading: forecastLoading, error: forecastError, refetch: runForecast } = useQuery({
    queryKey: ["forecastPredictions", forecastFilters],
    queryFn: () => api.predict.run(forecastFilters),
    enabled: false, // triggered manually via user click
  });

  // Automatically load initial forecast on mount
  useEffect(() => {
    runForecast();
  }, []);

  // Retrain model mutation (Admins only)
  const retrainMutation = useMutation({
    mutationFn: (model: string) => api.predict.train(model),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["forecastPredictions"] });
      runForecast();
    }
  });

  const handleRunForecast = () => {
    runForecast();
  };

  const handleRetrain = () => {
    retrainMutation.mutate(modelType);
  };

  // Format chart predictions data
  const chartData = forecastData?.predictions || [];

  return (
    <LayoutFrame>
      <div className="space-y-6">
        {/* Info Box */}
        <div className="bg-gradient-to-r from-violet-900/20 to-indigo-900/10 border border-violet-800/20 p-5 rounded-xl flex items-start gap-4">
          <span className="w-10 h-10 rounded-lg bg-violet-600/10 border border-violet-500/20 flex items-center justify-center text-brand-400 mt-0.5 flex-shrink-0 animate-pulse-subtle">
            <Brain size={20} />
          </span>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-zinc-200">AI Predictive Forecast Console</h3>
            <p className="text-zinc-400 text-xs leading-relaxed">
              InsightAI uses recursive time-series forecasting algorithms (XGBoost, Random Forest, or Ridge Linear Regression) built on historical transaction lags. Shaded margins represent the 95% forecast confidence interval boundary.
            </p>
          </div>
        </div>

        {forecastError && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs">
            Could not compile predictions. Ensure that active dataset contains at least 13 months of historical records.
          </div>
        )}

        {retrainMutation.isError && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs">
            Model training failed. Verify you have administrator rights to execute training jobs.
          </div>
        )}

        {retrainMutation.isSuccess && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <Check size={16} />
            <span>Model trained successfully. MAPE: {retrainMutation.data.mape.toFixed(2)}%, R2: {retrainMutation.data.r2_score.toFixed(2)}</span>
          </div>
        )}

        {/* Main Grid Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Settings Console */}
          <div className="glass-panel p-6 rounded-xl space-y-5 border border-zinc-800/80">
            <div>
              <h4 className="text-sm font-bold text-zinc-200">Parameters Console</h4>
              <p className="text-zinc-500 text-xs">Adjust models configuration inputs</p>
            </div>

            <div className="space-y-4">
              {/* Target algorithm */}
              <div className="space-y-1.5">
                <label className="text-zinc-400 text-xs font-semibold">Algorithm Engine</label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg text-xs py-2 px-3 text-zinc-300 focus:outline-none focus:border-brand-500 cursor-pointer"
                >
                  <option value="xgboost">XGBoost Regressor</option>
                  <option value="random_forest">Random Forest Forest</option>
                  <option value="linear">Ridge Linear Regression</option>
                </select>
              </div>

              {/* Range scale slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <label className="text-zinc-400">Months Ahead</label>
                  <span className="text-brand-400">{monthsAhead} months</span>
                </div>
                <input
                  type="range"
                  min="3"
                  max="12"
                  step="1"
                  value={monthsAhead}
                  onChange={(e) => setMonthsAhead(Number(e.target.value))}
                  className="w-full h-1 bg-zinc-850 rounded-lg appearance-none cursor-pointer accent-brand-500"
                />
              </div>

              {/* Territory split selector */}
              <div className="space-y-1.5">
                <label className="text-zinc-400 text-xs font-semibold">Target Territory Filter</label>
                <select
                  value={regionFilter}
                  onChange={(e) => setRegionFilter(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg text-xs py-2 px-3 text-zinc-300 focus:outline-none focus:border-brand-500 cursor-pointer"
                >
                  <option value="">Full Workspace (Overall)</option>
                  <option value="West">West Region</option>
                  <option value="East">East Region</option>
                  <option value="South">South Region</option>
                  <option value="Central">Central Region</option>
                </select>
              </div>

              {/* Category filter */}
              <div className="space-y-1.5">
                <label className="text-zinc-400 text-xs font-semibold">Product Category Filter</label>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg text-xs py-2 px-3 text-zinc-300 focus:outline-none focus:border-brand-500 cursor-pointer"
                >
                  <option value="">All Categories</option>
                  <option value="Technology">Technology</option>
                  <option value="Office Supplies">Office Supplies</option>
                  <option value="Furniture">Furniture</option>
                  <option value="Apparel">Apparel</option>
                </select>
              </div>

              <div className="pt-4 space-y-2">
                <button
                  onClick={handleRunForecast}
                  disabled={forecastLoading}
                  className="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  <Play size={14} />
                  <span>Execute Sales Forecast</span>
                </button>

                {isAdmin && (
                  <button
                    onClick={handleRetrain}
                    disabled={retrainMutation.isPending}
                    className="w-full bg-zinc-950 border border-zinc-800 hover:border-zinc-700/60 text-zinc-300 font-semibold text-xs py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    <SettingsIcon size={14} className={retrainMutation.isPending ? "animate-spin" : ""} />
                    <span>{retrainMutation.isPending ? "Training Model..." : "Retrain Engine"}</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Chart Display Panel */}
          <div className="glass-panel p-6 rounded-xl lg:col-span-2 space-y-4 border border-zinc-800/80 flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-bold text-zinc-200">Revenue Forecast Trajectory Chart</h4>
              <p className="text-zinc-500 text-xs">Projection path showing 95% Confidence Interval margins</p>
            </div>

            <div className="w-full h-80 flex-1 mt-4">
              {forecastLoading ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-zinc-500 text-xs">
                  <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-brand-500 mb-2"></div>
                  <span>Running ML predictions...</span>
                </div>
              ) : chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
                    <XAxis dataKey="month" stroke={TEXT_COLOR} fontSize={10} tickLine={false} />
                    <YAxis stroke={TEXT_COLOR} fontSize={10} tickLine={false} tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + "k" : v}`} />
                    <Tooltip
                      content={({ active, payload, label }: any) => {
                        if (active && payload && payload.length) {
                          const info = payload[0].payload;
                          return (
                            <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-lg shadow-xl text-zinc-200 text-xs">
                              <p className="font-semibold text-zinc-400 mb-1">{label}</p>
                              <p className="text-brand-400 font-bold my-0.5">Forecasted Sales: ${info.predicted_sales.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                              <p className="text-zinc-500 text-[10px] my-0.5">Confidence Limit: ${info.confidence_lower.toLocaleString(undefined, { maximumFractionDigits: 0 })} - ${info.confidence_upper.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: "11px", color: TEXT_COLOR }} />
                    
                    {/* Confidence Intervals shading */}
                    <Area
                      name="95% Confidence Band"
                      type="monotone"
                      dataKey="confidence_upper"
                      stroke="none"
                      fill="#8b5cf6"
                      fillOpacity={0.12}
                    />
                    <Area
                      name="Confidence Lower"
                      type="monotone"
                      dataKey="confidence_lower"
                      stroke="none"
                      fill="#09090b"
                      fillOpacity={1}
                    />
                    
                    {/* Prediction line */}
                    <Line
                      name="Forecasted Revenue"
                      type="monotone"
                      dataKey="predicted_sales"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      dot={{ r: 3, stroke: "#8b5cf6", strokeWidth: 1, fill: "#09090b" }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-600 text-xs">
                  No prediction paths available. Run execution console.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </LayoutFrame>
  );
}
