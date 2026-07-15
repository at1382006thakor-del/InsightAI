"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../services/api";
import { LayoutFrame } from "../../../components/LayoutFrame";
import { Upload, Check, AlertTriangle, Database, Trash2, CheckCircle } from "lucide-react";

const REQUIRED_COLUMNS = [
  "order_date", "customer", "segment", "city", "state", 
  "product", "category", "quantity", "price", "discount", 
  "revenue", "profit", "region"
];

export default function DatasetUploadPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [cleanLoading, setCleanLoading] = useState(false);
  const [uploadedMeta, setUploadedMeta] = useState<any>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [fillMissing, setFillMissing] = useState(true);
  const [removeDuplicates, setRemoveDuplicates] = useState(true);
  
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Fetch dataset history list
  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ["datasetsList"],
    queryFn: () => api.datasets.list(),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setUploadedMeta(null);
      setErrorMessage("");
      setSuccessMessage("");
    }
  };

  const handleUploadFile = async () => {
    if (!file) return;
    setUploadLoading(true);
    setErrorMessage("");
    try {
      const data = await api.datasets.upload(file);
      setUploadedMeta(data);
      
      // Auto-suggest column mappings
      const initialMapping: Record<string, string> = {};
      REQUIRED_COLUMNS.forEach(col => {
        const matched = Object.entries(data.mapped_columns).find(([_, val]) => val === col);
        initialMapping[col] = matched ? matched[0] : "";
      });
      setColumnMapping(initialMapping);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || "Failed to analyze raw spreadsheet file.");
    } finally {
      setUploadLoading(false);
    }
  };

  const handleImportClean = async () => {
    if (!uploadedMeta) return;
    setCleanLoading(true);
    setErrorMessage("");
    setSuccessMessage("");

    // Verify all variables are mapped
    const missingMaps = REQUIRED_COLUMNS.filter(col => !columnMapping[col]);
    if (missingMaps.length > 0) {
      setErrorMessage(`All database variables must be mapped. Missing: ${missingMaps.join(", ")}`);
      setCleanLoading(false);
      return;
    }

    try {
      // Re-map from database variable key back to raw file column
      const apiMapping: Record<string, string> = {};
      Object.entries(columnMapping).forEach(([reqKey, srcVal]) => {
        apiMapping[srcVal] = reqKey;
      });

      const res = await api.datasets.clean({
        file_path: uploadedMeta.file_path,
        mapping_json: apiMapping,
        fill_missing: fillMissing,
        remove_duplicates: removeDuplicates
      });

      setSuccessMessage(res.message || "New dataset loaded successfully.");
      setUploadedMeta(null);
      setFile(null);
      queryClient.invalidateQueries({ queryKey: ["datasetsList"] });
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || err.message || "Spreadsheet cleaning and bulk loading failed.");
    } finally {
      setCleanLoading(false);
    }
  };

  const handleToggleActive = async (id: string) => {
    try {
      await api.datasets.toggleActive(id);
      queryClient.invalidateQueries({ queryKey: ["datasetsList"] });
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleDeleteDataset = async (id: string) => {
    try {
      await api.datasets.delete(id);
      queryClient.invalidateQueries({ queryKey: ["datasetsList"] });
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleMapChange = (reqCol: string, srcCol: string) => {
    setColumnMapping({ ...columnMapping, [reqCol]: srcCol });
  };

  return (
    <LayoutFrame>
      <div className="space-y-6">
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

        {/* Upload Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* File selector zone */}
          <div className="glass-panel p-6 rounded-xl border border-zinc-800/80 space-y-4 lg:col-span-1">
            <div>
              <h4 className="text-sm font-bold text-zinc-200">Spreadsheet Importer</h4>
              <p className="text-zinc-500 text-xs">Drag and drop file to check structures</p>
            </div>

            <div className="border border-dashed border-zinc-800 hover:border-zinc-700/80 rounded-xl p-8 flex flex-col items-center justify-center text-center space-y-3 bg-zinc-950/20 relative">
              <input
                type="file"
                accept=".csv, .xls, .xlsx"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="text-zinc-600 animate-pulse-subtle" size={28} />
              <div className="space-y-1">
                <p className="text-xs text-zinc-300 font-semibold truncate max-w-[200px]">
                  {file ? file.name : "Select CSV / Excel File"}
                </p>
                <p className="text-[10px] text-zinc-500">Max size 100MB</p>
              </div>
            </div>

            {file && !uploadedMeta && (
              <button
                onClick={handleUploadFile}
                disabled={uploadLoading}
                className="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <span>{uploadLoading ? "Uploading..." : "Analyze Spreadsheet"}</span>
              </button>
            )}
          </div>

          {/* Column mappings */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-zinc-800/80 space-y-4">
            <div>
              <h4 className="text-sm font-bold text-zinc-200">Database Schema Variable Mapping</h4>
              <p className="text-zinc-500 text-xs">Map spreadsheet columns to database fields</p>
            </div>

            {!uploadedMeta ? (
              <div className="h-60 flex flex-col items-center justify-center text-zinc-600 text-xs border border-zinc-800/30 rounded-xl bg-zinc-950/10">
                <Database size={24} className="mb-2 text-zinc-700" />
                <span>Upload a spreadsheet to configure schema mapping.</span>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 max-h-56 overflow-y-auto pr-1">
                  {REQUIRED_COLUMNS.map(reqCol => (
                    <div key={reqCol} className="flex justify-between items-center bg-zinc-950/40 p-2.5 rounded-lg border border-zinc-850">
                      <span className="text-xs text-zinc-400 font-medium capitalize">
                        {reqCol.replace("_", " ")}
                      </span>
                      <select
                        value={columnMapping[reqCol] || ""}
                        onChange={(e) => handleMapChange(reqCol, e.target.value)}
                        className="bg-zinc-900 border border-zinc-800 rounded text-[10px] py-1 px-2 text-zinc-300 focus:outline-none focus:border-brand-500 cursor-pointer"
                      >
                        <option value="">-- Select Column --</option>
                        {uploadedMeta.columns.map((c: string) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-4 text-xs text-zinc-400 items-center pt-2">
                  <label className="flex items-center gap-1.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={fillMissing}
                      onChange={(e) => setFillMissing(e.target.checked)}
                      className="accent-brand-500"
                    />
                    <span>Auto-fill missing cells</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={removeDuplicates}
                      onChange={(e) => setRemoveDuplicates(e.target.checked)}
                      className="accent-brand-500"
                    />
                    <span>Remove row duplicates</span>
                  </label>
                  
                  <button
                    onClick={handleImportClean}
                    disabled={cleanLoading}
                    className="ml-auto bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs py-2 px-4 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    <Check size={14} className={cleanLoading ? "animate-pulse" : ""} />
                    <span>{cleanLoading ? "Ingesting..." : "Clean and Load Dataset"}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* History log list */}
        <div className="glass-panel p-6 rounded-xl border border-zinc-800/80">
          <div>
            <h4 className="text-sm font-bold text-zinc-200">Dataset History & Active Status</h4>
            <p className="text-zinc-500 text-xs">Switch active dataset or delete entries</p>
          </div>

          <div className="overflow-x-auto mt-4">
            {datasetsLoading ? (
              <div className="text-center text-zinc-500 py-10 text-xs">Loading logs...</div>
            ) : datasets?.length === 0 ? (
              <div className="text-center text-zinc-600 py-10 text-xs">No datasets uploaded yet.</div>
            ) : (
              <table className="w-full text-left text-xs text-zinc-400">
                <thead className="text-[10px] text-zinc-500 uppercase tracking-wider border-b border-zinc-800/80">
                  <tr>
                    <th className="pb-3 font-semibold">Spreadsheet Filename</th>
                    <th className="pb-3 font-semibold text-center">Quality Score</th>
                    <th className="pb-3 font-semibold">Upload Date</th>
                    <th className="pb-3 font-semibold text-center">Active Status</th>
                    <th className="pb-3 font-semibold text-right">Delete</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {datasets?.map((d: any) => {
                    const uploadDate = d.upload_date ? new Date(d.upload_date).toLocaleDateString() : new Date().toLocaleDateString();
                    return (
                      <tr key={d.id} className="hover:bg-zinc-800/10">
                        <td className="py-3.5 font-semibold text-zinc-200 flex items-center gap-2">
                          <Database size={14} className={d.is_active ? "text-brand-400" : "text-zinc-500"} />
                          <span>{d.filename}</span>
                        </td>
                        <td className="py-3.5 text-center font-bold text-brand-400">{d.quality_score.toFixed(1)}%</td>
                        <td className="py-3.5">{uploadDate}</td>
                        <td className="py-3.5 text-center">
                          <button
                            onClick={() => handleToggleActive(d.id)}
                            className={`px-3 py-1 rounded text-[10px] font-bold border transition-all cursor-pointer ${
                              d.is_active
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-zinc-950 text-zinc-500 border-zinc-850 hover:text-zinc-300"
                            }`}
                          >
                            {d.is_active ? "Active" : "Activate"}
                          </button>
                        </td>
                        <td className="py-3.5 text-right">
                          <button
                            onClick={() => handleDeleteDataset(d.id)}
                            className="text-zinc-600 hover:text-red-400 p-1 rounded hover:bg-red-500/10 cursor-pointer"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </LayoutFrame>
  );
}
