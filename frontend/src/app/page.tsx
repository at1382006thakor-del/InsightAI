"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import { LayoutFrame } from "../components/LayoutFrame";
import { SalesTrendChart, ShareDonutChart } from "../charts/DashboardCharts";
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  ShoppingCart, 
  Users as UsersIcon, 
  Percent,
  Calendar,
  MapPin
} from "lucide-react";

export default function DashboardPage() {
  const [regionFilter, setRegionFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const filters = {
    region: regionFilter || undefined,
    startDate: startDate || undefined,
    endDate: endDate || undefined,
  };

  // Fetch summary stats using React Query
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ["dashboardSummary", filters],
    queryFn: () => api.dashboard.getSummary(filters),
  });

  // Fetch sales trend timeseries data
  const { data: timeseries, isLoading: trendLoading } = useQuery({
    queryKey: ["dashboardTimeseries", filters],
    queryFn: () => api.dashboard.getTimeseries(filters),
  });

  // Fetch category sales pie slices
  const { data: categoryData, isLoading: catLoading } = useQuery({
    queryKey: ["dashboardCategory", filters],
    queryFn: () => api.dashboard.getCategorySales(filters),
  });

  const isPageLoading = summaryLoading || trendLoading || catLoading;

  // Format category data for Donut Chart
  const pieData = categoryData
    ? categoryData.map((item: any) => ({
        name: item.category,
        value: item.revenue,
      }))
    : [];

  return (
    <LayoutFrame>
      <div className="space-y-6">
        {/* Dynamic Filters Area */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-zinc-900/40 p-4 border border-zinc-800/80 rounded-xl">
          <div>
            <h2 className="text-sm font-semibold text-zinc-300">Global Dashboard Filters</h2>
            <p className="text-zinc-500 text-xs">Filter metrics dynamically by date ranges and territories</p>
          </div>
          <div className="flex flex-wrap gap-3 items-center w-full sm:w-auto">
            <div className="relative flex items-center">
              <Calendar size={14} className="absolute left-3 text-zinc-500" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700/60 rounded-lg text-xs py-2 pl-9 pr-3 text-zinc-300 focus:outline-none focus:border-brand-500"
              />
            </div>
            <span className="text-zinc-600 text-xs">to</span>
            <div className="relative flex items-center">
              <Calendar size={14} className="absolute left-3 text-zinc-500" />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700/60 rounded-lg text-xs py-2 pl-9 pr-3 text-zinc-300 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div className="relative flex items-center">
              <MapPin size={14} className="absolute left-3 text-zinc-500" />
              <select
                value={regionFilter}
                onChange={(e) => setRegionFilter(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700/60 rounded-lg text-xs py-2 pl-9 pr-6 text-zinc-300 focus:outline-none focus:border-brand-500 appearance-none cursor-pointer"
              >
                <option value="">All Regions</option>
                <option value="West">West</option>
                <option value="East">East</option>
                <option value="South">South</option>
                <option value="Central">Central</option>
              </select>
            </div>
          </div>
        </div>

        {summaryError && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs">
            Failed to aggregate sales metrics. Ensure you have clean active datasets loaded.
          </div>
        )}

        {/* Loading Spinner */}
        {isPageLoading && (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-brand-500"></div>
            <span className="text-zinc-400 text-sm ml-3">Aggregating transaction records...</span>
          </div>
        )}

        {!isPageLoading && summary && (
          <>
            {/* Stat Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
              {/* Revenue */}
              <div className="glass-panel p-6 rounded-xl flex items-center justify-between border border-zinc-800/80 hover:border-zinc-700/50 transition-all duration-300">
                <div className="space-y-1.5">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Total Sales Revenue</span>
                  <h3 className="text-2xl font-extrabold text-white">
                    ${summary.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </h3>
                  <div className="flex items-center gap-1.5 text-[10px]">
                    {summary.growth_percent >= 0 ? (
                      <span className="text-emerald-400 font-bold flex items-center gap-0.5">
                        <TrendingUp size={10} /> +{summary.growth_percent.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-red-400 font-bold flex items-center gap-0.5">
                        <TrendingDown size={10} /> {summary.growth_percent.toFixed(2)}%
                      </span>
                    )}
                    <span className="text-zinc-500">vs last 30 days</span>
                  </div>
                </div>
                <span className="w-10 h-10 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
                  <DollarSign size={18} />
                </span>
              </div>

              {/* Net Profit */}
              <div className="glass-panel p-6 rounded-xl flex items-center justify-between border border-zinc-800/80 hover:border-zinc-700/50 transition-all duration-300">
                <div className="space-y-1.5">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Net Profit</span>
                  <h3 className="text-2xl font-extrabold text-white">
                    ${summary.total_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </h3>
                  <span className="text-[10px] text-zinc-500 font-semibold block">
                    Margin: {summary.return_rate.toFixed(1)}% yield
                  </span>
                </div>
                <span className="w-10 h-10 rounded-lg bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400">
                  <DollarSign size={18} />
                </span>
              </div>

              {/* Closed Orders */}
              <div className="glass-panel p-6 rounded-xl flex items-center justify-between border border-zinc-800/80 hover:border-zinc-700/50 transition-all duration-300">
                <div className="space-y-1.5">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Orders Count</span>
                  <h3 className="text-2xl font-extrabold text-white">
                    {summary.total_orders.toLocaleString()}
                  </h3>
                  <span className="text-[10px] text-zinc-500 font-semibold block">
                    AOV: ${summary.average_order_value.toFixed(2)} average
                  </span>
                </div>
                <span className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <ShoppingCart size={18} />
                </span>
              </div>

              {/* Active Clients */}
              <div className="glass-panel p-6 rounded-xl flex items-center justify-between border border-zinc-800/80 hover:border-zinc-700/50 transition-all duration-300">
                <div className="space-y-1.5">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Active Customers</span>
                  <h3 className="text-2xl font-extrabold text-white">
                    {summary.total_customers.toLocaleString()}
                  </h3>
                  <span className="text-[10px] text-zinc-500 font-semibold block">
                    Unique account portfolio
                  </span>
                </div>
                <span className="w-10 h-10 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                  <UsersIcon size={18} />
                </span>
              </div>
            </div>

            {/* Charts Row Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Sales trend */}
              <div className="glass-panel p-6 rounded-xl lg:col-span-2 space-y-4 border border-zinc-800/80">
                <div>
                  <h4 className="text-sm font-bold text-zinc-200">Historical Sales Revenue Pathway</h4>
                  <p className="text-zinc-500 text-xs">Total sales volume vs net margins trend</p>
                </div>
                {timeseries && timeseries.length > 0 ? (
                  <SalesTrendChart data={timeseries} />
                ) : (
                  <div className="h-60 flex items-center justify-center text-zinc-600 text-xs">
                    No trend history available. Please run standard data seeding.
                  </div>
                )}
              </div>

              {/* Share Donut */}
              <div className="glass-panel p-6 rounded-xl space-y-4 border border-zinc-800/80">
                <div>
                  <h4 className="text-sm font-bold text-zinc-200">Revenue Value Share</h4>
                  <p className="text-zinc-500 text-xs">Segment allocation by category contribution</p>
                </div>
                {pieData.length > 0 ? (
                  <ShareDonutChart data={pieData} />
                ) : (
                  <div className="h-60 flex items-center justify-center text-zinc-600 text-xs">
                    No category records available.
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </LayoutFrame>
  );
}
