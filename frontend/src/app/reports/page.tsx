"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, apiClient } from "../../services/api";
import { LayoutFrame } from "../../components/LayoutFrame";
import { FileText, Download, Play, CheckCircle, Clock, Trash2, ShieldAlert } from "lucide-react";

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [reportType, setReportType] = useState("monthly");
  const [fileFormat, setFileFormat] = useState<"pdf" | "pptx">("pdf");

  // Fetch strategy reports list
  const { data: reports, isLoading: reportsLoading, error: reportsError } = useQuery({
    queryKey: ["strategyReports"],
    queryFn: () => api.reports.list(),
  });

  // Report generation mutation
  const generateMutation = useMutation({
    mutationFn: ({ type, format }: { type: string; format: "pdf" | "pptx" }) =>
      api.reports.generate(type, format),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategyReports"] });
    }
  });

  const handleGenerateReport = () => {
    generateMutation.mutate({ type: reportType, format: fileFormat });
  };

  const handleDownload = async (id: string, format: string) => {
    try {
      const response = await apiClient.get(`/reports/download/${id}`, {
        responseType: "blob",
      });
      const contentType = response.headers["content-type"];
      const blob = new Blob([response.data], {
        type: typeof contentType === "string" ? contentType : undefined,
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `InsightAI_Report_${id.slice(0, 5)}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
      alert("Failed to download the report.");
    }
  };

  return (
    <LayoutFrame>
      <div className="space-y-6">
        {/* Reports triggers */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-zinc-900/40 p-4 border border-zinc-800/80 rounded-xl">
          <div>
            <h2 className="text-sm font-semibold text-zinc-300">Generate Business Report</h2>
            <p className="text-zinc-500 text-xs">Run asynchronous PDF or PowerPoint strategical slide compile jobs</p>
          </div>
          <div className="flex flex-wrap gap-3 items-center w-full sm:w-auto">
            <div className="flex items-center gap-1.5">
              <label className="text-zinc-500 text-[10px] uppercase font-bold">Scope:</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 rounded-lg text-xs py-2 px-3 text-zinc-300 focus:outline-none focus:border-brand-500 cursor-pointer"
              >
                <option value="monthly">Monthly Performance</option>
                <option value="quarterly">Quarterly Strategy</option>
                <option value="annual">Annual Executive</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <label className="text-zinc-500 text-[10px] uppercase font-bold">Format:</label>
              <select
                value={fileFormat}
                onChange={(e) => setFileFormat(e.target.value as "pdf" | "pptx")}
                className="bg-zinc-950 border border-zinc-800 rounded-lg text-xs py-2 px-3 text-zinc-300 focus:outline-none focus:border-brand-500 cursor-pointer"
              >
                <option value="pdf">Adobe PDF Format</option>
                <option value="pptx">PowerPoint slides (.pptx)</option>
              </select>
            </div>

            <button
              onClick={handleGenerateReport}
              disabled={generateMutation.isPending}
              className="bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs py-2.5 px-4 rounded-lg transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <Play size={12} className={generateMutation.isPending ? "animate-spin" : ""} />
              <span>{generateMutation.isPending ? "Compiling..." : "Generate Strategy Report"}</span>
            </button>
          </div>
        </div>

        {generateMutation.isSuccess && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <CheckCircle size={16} />
            <span>Strategy report generated successfully. Ready for download.</span>
          </div>
        )}

        {reportsError && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs">
            Failed to load reports catalog from database.
          </div>
        )}

        {/* History Log table */}
        <div className="glass-panel p-6 rounded-xl border border-zinc-800/80">
          <div>
            <h4 className="text-sm font-bold text-zinc-200">Reports Generation History Log</h4>
            <p className="text-zinc-500 text-xs">Audited strategy documents generated on-demand</p>
          </div>

          <div className="overflow-x-auto mt-4">
            {reportsLoading ? (
              <div className="text-center text-zinc-500 py-10 text-xs">Synchronizing document list...</div>
            ) : reports?.length === 0 ? (
              <div className="text-center text-zinc-600 py-10 text-xs">No reports compiled yet. Adjust controls above.</div>
            ) : (
              <table className="w-full text-left text-xs text-zinc-400">
                <thead className="text-[10px] text-zinc-500 uppercase tracking-wider border-b border-zinc-800/80">
                  <tr>
                    <th className="pb-3 font-semibold">Document Name</th>
                    <th className="pb-3 font-semibold">Report Format</th>
                    <th className="pb-3 font-semibold">Generation Date</th>
                    <th className="pb-3 font-semibold text-center">Status</th>
                    <th className="pb-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {reports?.map((r: any) => {
                    const isPdf = r.file_format === "pdf";
                    const isNewFormatReport = r.pdf_path || r.file_path; // compatible check
                    const dateStr = r.generated_at ? new Date(r.generated_at).toLocaleDateString() : new Date().toLocaleDateString();
                    
                    return (
                      <tr key={r.report_id} className="hover:bg-zinc-800/10">
                        <td className="py-3.5 font-semibold text-zinc-200 flex items-center gap-2">
                          <span className={`w-6 h-6 rounded bg-zinc-800 border flex items-center justify-center font-bold text-[10px] ${
                            isPdf ? "text-red-400 border-red-500/20" : "text-amber-400 border-amber-500/20"
                          }`}>
                            <FileText size={12} />
                          </span>
                          <span>
                            InsightAI_{r.type.toUpperCase()}_Report_{r.report_id.slice(0, 5)}.{r.file_format || "pdf"}
                          </span>
                        </td>
                        <td className="py-3.5 capitalize font-semibold">{r.file_format || "PDF"}</td>
                        <td className="py-3.5">{dateStr}</td>
                        <td className="py-3.5 text-center">
                          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 inline-flex items-center gap-1">
                            <CheckCircle size={10} />
                            Completed
                          </span>
                        </td>
                        <td className="py-3.5 text-right">
                          <button
                            onClick={() => handleDownload(r.report_id, r.file_format)}
                            className="px-3 py-1.5 rounded bg-brand-600/10 hover:bg-brand-600 border border-brand-500/20 text-brand-400 hover:text-white transition-all text-[10px] inline-flex items-center gap-1 font-bold cursor-pointer"
                          >
                            <Download size={10} />
                            Download
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
