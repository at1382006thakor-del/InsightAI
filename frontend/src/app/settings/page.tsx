"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../../services/api";
import { LayoutFrame } from "../../components/LayoutFrame";
import { Key, Database, CheckCircle, AlertTriangle, ShieldCheck } from "lucide-react";

export default function SettingsPage() {
  const [geminiKey, setGeminiKey] = useState("");
  const [dbType, setDbType] = useState("sqlite");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const user = api.auth.getCurrentUser();
    if (user && user.role === "admin") {
      setIsAdmin(true);
    }
  }, []);

  // Fetch persisted settings (Admin only)
  const { data: settingsData, isLoading: settingsLoading } = useQuery({
    queryKey: ["systemSettings"],
    queryFn: () => api.settings.get(),
    enabled: isAdmin,
  });

  // Hydrate states when settingsData loads
  useEffect(() => {
    if (settingsData) {
      setGeminiKey(settingsData.gemini_api_key || "");
      setDbType(settingsData.database_type || "sqlite");
    }
  }, [settingsData]);

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: (payload: { gemini_api_key?: string; database_type?: string }) =>
      api.settings.update(payload),
    onSuccess: (data) => {
      setSuccessMessage(data.message || "System configurations updated successfully.");
      setErrorMessage("");
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || err.message || "Failed to update configurations.");
      setSuccessMessage("");
    }
  });

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAdmin) return;
    updateSettingsMutation.mutate({
      gemini_api_key: geminiKey,
      database_type: dbType,
    });
  };

  return (
    <LayoutFrame>
      <div className="space-y-6 max-w-2xl">
        {errorMessage && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <AlertTriangle size={16} />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <CheckCircle size={16} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Configurations Form */}
        <div className="glass-panel p-6 rounded-xl border border-zinc-800/80 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-zinc-200">System Parameters Configurations</h4>
            <p className="text-zinc-500 text-xs">Configure LLM integrations and database connections</p>
          </div>

          {!isAdmin ? (
            <div className="bg-zinc-950/40 border border-zinc-850 p-6 rounded-xl text-center space-y-2">
              <ShieldCheck size={24} className="mx-auto text-zinc-600" />
              <h5 className="text-xs font-bold text-zinc-400">Access Restricted</h5>
              <p className="text-[10px] text-zinc-500">Only Administrator users can inspect or edit global parameters settings.</p>
            </div>
          ) : settingsLoading ? (
            <div className="text-center text-zinc-500 py-10 text-xs">Synchronizing persisted parameters...</div>
          ) : (
            <form onSubmit={handleSaveSettings} className="space-y-4 pt-2">
              {/* Gemini API Key */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="text-zinc-400 text-xs font-semibold">Google Gemini API Token Key</label>
                  {settingsData?.has_key && (
                    <span className="text-emerald-400 text-[10px] font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                      Key Persisted
                    </span>
                  )}
                </div>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                    <Key size={14} />
                  </span>
                  <input
                    type="password"
                    placeholder={settingsData?.has_key ? "••••••••••••••••" : "Paste your GEMINI_API_KEY"}
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-brand-500"
                  />
                </div>
                <p className="text-[9px] text-zinc-500 leading-relaxed">
                  Required to generate LLM strategies and answer conversational chat queries. Leaves blank to use fallback rule-based summaries.
                </p>
              </div>

              {/* Database type */}
              <div className="space-y-1.5">
                <label className="text-zinc-400 text-xs font-semibold">Active Database Connection Type</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                    <Database size={14} />
                  </span>
                  <select
                    value={dbType}
                    onChange={(e) => setDbType(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-6 text-xs text-zinc-200 focus:outline-none focus:border-brand-500 appearance-none cursor-pointer"
                  >
                    <option value="sqlite">Local SQLite Connection (Development)</option>
                    <option value="postgresql">Neon Serverless PostgreSQL (Production)</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={updateSettingsMutation.isPending}
                className="bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs py-2.5 px-4 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <span>{updateSettingsMutation.isPending ? "Updating configurations..." : "Save Parameters Configuration"}</span>
              </button>
            </form>
          )}
        </div>
      </div>
    </LayoutFrame>
  );
}
