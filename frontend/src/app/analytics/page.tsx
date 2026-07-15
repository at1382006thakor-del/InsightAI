"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../services/api";
import { LayoutFrame } from "../../components/LayoutFrame";
import { CategoryPerformanceChart } from "../../charts/DashboardCharts";
import { 
  Users as UsersIcon, 
  MapPin, 
  ShoppingBag, 
  TrendingUp,
  Award,
  Search,
  Filter
} from "lucide-react";

export default function AnalyticsPage() {
  const [segmentFilter, setSegmentFilter] = useState("");
  const [productLimit, setProductLimit] = useState(10);
  const [sortBy, setSortBy] = useState("revenue");

  // React Query fetch for top customers ranked by revenue
  const { data: topCustomers, isLoading: custLoading } = useQuery({
    queryKey: ["analyticsCustomers", segmentFilter],
    queryFn: () => api.analytics.getCustomers({ limit: 10, segment: segmentFilter || undefined }),
  });

  // React Query fetch for top product performance
  const { data: topProducts, isLoading: prodLoading } = useQuery({
    queryKey: ["analyticsProducts", productLimit, sortBy],
    queryFn: () => api.analytics.getProducts({ limit: productLimit, sortBy }),
  });

  // Fetch category performance values for the bar chart
  const { data: categoryStats, isLoading: chartLoading } = useQuery({
    queryKey: ["analyticsCategoryChart"],
    queryFn: () => api.dashboard.getCategorySales(), // pulls default global category sales
  });

  const isPageLoading = custLoading || prodLoading || chartLoading;

  return (
    <LayoutFrame>
      <div className="space-y-6">
        {/* Subnavigation filter controls */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-zinc-900/40 p-4 border border-zinc-800/80 rounded-xl">
          <div>
            <h2 className="text-sm font-semibold text-zinc-300">Client Portfolio Segment Filters</h2>
            <p className="text-zinc-500 text-xs">Isolate metrics by specific corporate/consumer customer segments</p>
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            {["", "Consumer", "Corporate", "Home Office"].map((seg) => (
              <button
                key={seg}
                onClick={() => setSegmentFilter(seg)}
                className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                  segmentFilter === seg
                    ? "bg-brand-600 text-white border-brand-500 shadow-md shadow-brand-500/10"
                    : "bg-zinc-950 text-zinc-400 border-zinc-800 hover:border-zinc-700/60"
                }`}
              >
                {seg === "" ? "All Segments" : seg}
              </button>
            ))}
          </div>
        </div>

        {isPageLoading && (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-brand-500"></div>
            <span className="text-zinc-400 text-sm ml-3">Analyzing product metrics...</span>
          </div>
        )}

        {!isPageLoading && (
          <>
            {/* Top Row: Category Performance chart & Top Products List */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Category Bar chart */}
              <div className="glass-panel p-6 rounded-xl lg:col-span-2 space-y-4 border border-zinc-800/80">
                <div>
                  <h4 className="text-sm font-bold text-zinc-200">Category Profit Yield Comparison</h4>
                  <p className="text-zinc-500 text-xs">Analysis of category performance values</p>
                </div>
                {categoryStats && categoryStats.length > 0 ? (
                  <CategoryPerformanceChart data={categoryStats} />
                ) : (
                  <div className="h-60 flex items-center justify-center text-zinc-600 text-xs">
                    No category data available.
                  </div>
                )}
              </div>

              {/* Top Products sidebar */}
              <div className="glass-panel p-6 rounded-xl space-y-4 border border-zinc-800/80 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="text-sm font-bold text-zinc-200">Top Revenue Drivers</h4>
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="bg-zinc-950 border border-zinc-800 rounded-lg text-[10px] py-1 px-2 text-zinc-400 focus:outline-none focus:border-brand-500 appearance-none cursor-pointer"
                    >
                      <option value="revenue">Sales Value</option>
                      <option value="profit">Net Profit</option>
                      <option value="quantity">Units Count</option>
                    </select>
                  </div>
                  <p className="text-zinc-500 text-xs">Key product items ranked by metrics</p>
                </div>

                <div className="space-y-3.5 flex-1 overflow-y-auto mt-4 pr-1 max-h-72">
                  {topProducts?.map((p: any, index: number) => (
                    <div key={p.product_id} className="flex justify-between items-center bg-zinc-950/30 p-2.5 rounded-lg border border-zinc-800/30">
                      <div className="flex items-center gap-3">
                        <span className="w-5 h-5 rounded bg-zinc-800 border border-zinc-700/80 flex items-center justify-center text-[10px] text-zinc-400 font-bold">
                          {index + 1}
                        </span>
                        <div className="truncate max-w-[130px]">
                          <p className="text-xs font-semibold text-zinc-200 truncate">{p.name}</p>
                          <p className="text-zinc-500 text-[9px] uppercase tracking-wider">{p.category}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-bold text-white">
                          ${p.revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </p>
                        <p className="text-[9px] text-zinc-500">Stock: {p.stock} pcs</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom Row: Customer Portfolio lists */}
            <div className="glass-panel p-6 rounded-xl border border-zinc-800/80">
              <div className="mb-4">
                <h4 className="text-sm font-bold text-zinc-200">High-Value Client Portfolio List</h4>
                <p className="text-zinc-500 text-xs">Ranking accounts by cumulative transaction revenues</p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-zinc-400">
                  <thead className="text-[10px] text-zinc-500 uppercase tracking-wider border-b border-zinc-800/85">
                    <tr>
                      <th className="pb-3 font-semibold">Account Name</th>
                      <th className="pb-3 font-semibold">Market Segment</th>
                      <th className="pb-3 font-semibold">Location</th>
                      <th className="pb-3 font-semibold text-center">Orders Count</th>
                      <th className="pb-3 font-semibold text-right">Revenue Contribution</th>
                      <th className="pb-3 font-semibold text-right">Partnership Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50">
                    {topCustomers?.map((c: any) => (
                      <tr key={c.customer_id} className="hover:bg-zinc-800/10">
                        <td className="py-3.5 font-semibold text-zinc-200 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-brand-600/10 text-brand-400 flex items-center justify-center font-bold text-[10px]">
                            {c.name.charAt(0)}
                          </span>
                          <span>{c.name}</span>
                        </td>
                        <td className="py-3.5">{c.segment}</td>
                        <td className="py-3.5">{c.city}, {c.state}</td>
                        <td className="py-3.5 text-center font-semibold text-zinc-300">{c.orders} transactions</td>
                        <td className="py-3.5 text-right font-bold text-white">
                          ${c.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-3.5 text-right">
                          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 inline-flex items-center gap-1">
                            <Award size={10} />
                            Partner Tier
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </LayoutFrame>
  );
}
