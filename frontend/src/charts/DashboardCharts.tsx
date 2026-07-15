"use client";

import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Legend,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
  FunnelChart,
  Funnel,
  LabelList
} from "recharts";

const CHART_COLORS = ["#8b5cf6", "#a78bfa", "#c084fc", "#ddd6fe", "#ec4899", "#f43f5e"];
const GRID_COLOR = "#27272a"; 
const TEXT_COLOR = "#a1a1aa"; 

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-lg shadow-xl text-zinc-200 text-xs">
        <p className="font-semibold text-zinc-400 mb-1">{label}</p>
        {payload.map((pld: any, index: number) => (
          <p key={index} style={{ color: pld.fill || pld.color || "#a78bfa" }} className="my-0.5">
            {pld.name}: {typeof pld.value === "number" ? `$${pld.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : pld.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

interface TimeseriesProps {
  data: Array<{ date: string; revenue: number; profit: number; orders?: number }>;
}

export const SalesTrendChart: React.FC<TimeseriesProps> = ({ data }) => {
  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorProf" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ec4899" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
          <XAxis dataKey="date" stroke={TEXT_COLOR} fontSize={10} tickLine={false} />
          <YAxis stroke={TEXT_COLOR} fontSize={10} tickLine={false} tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + "k" : v}`} />
          <Tooltip content={<CustomTooltip />} />
          <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: "11px", color: TEXT_COLOR }} />
          <Area name="Revenue" type="monotone" dataKey="revenue" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
          <Area name="Net Profit" type="monotone" dataKey="profit" stroke="#ec4899" strokeWidth={2} fillOpacity={1} fill="url(#colorProf)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

interface CategoryProps {
  data: Array<{ category: string; revenue: number; profit: number }>;
}

export const CategoryPerformanceChart: React.FC<CategoryProps> = ({ data }) => {
  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
          <XAxis dataKey="category" stroke={TEXT_COLOR} fontSize={10} tickLine={false} />
          <YAxis stroke={TEXT_COLOR} fontSize={10} tickLine={false} tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + "k" : v}`} />
          <Tooltip content={<CustomTooltip />} />
          <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: "11px", color: TEXT_COLOR }} />
          <Bar name="Revenue" dataKey="revenue" fill="#8b5cf6" radius={[4, 4, 0, 0]} maxBarSize={40} />
          <Bar name="Net Profit" dataKey="profit" fill="#a78bfa" radius={[4, 4, 0, 0]} maxBarSize={40} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

interface DonutProps {
  data: Array<{ name: string; value: number }>;
}

export const ShareDonutChart: React.FC<DonutProps> = ({ data }) => {
  const total = data.reduce((acc, curr) => acc + curr.value, 0);

  return (
    <div className="w-full h-80 flex flex-col justify-center items-center">
      <ResponsiveContainer width="100%" height="80%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={85}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} stroke="#09090b" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip formatter={(value: any) => [`$${Number(value || 0).toLocaleString()}`, "Revenue"]} />
        </PieChart>
      </ResponsiveContainer>
      
      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs text-zinc-400 mt-2">
        {data.map((item, index) => {
          const percent = total > 0 ? ((item.value / total) * 100).toFixed(1) : "0";
          return (
            <div key={item.name} className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}></span>
              <span className="truncate max-w-[90px]">{item.name}</span>
              <span className="text-zinc-500 font-semibold">{percent}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

interface ScatterProps {
  data: Array<{ name: string; revenue: number; discount: number; quantity: number }>;
}

export const SalesScatterPlot: React.FC<ScatterProps> = ({ data }) => {
  const formattedData = data.map(item => ({
    ...item,
    discountPercent: Math.round(item.discount * 100)
  }));

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: -10 }}>
          <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3" />
          <XAxis 
            type="number" 
            dataKey="discountPercent" 
            name="Discount" 
            unit="%" 
            stroke={TEXT_COLOR} 
            fontSize={10}
            domain={[0, 100]}
          />
          <YAxis 
            type="number" 
            dataKey="revenue" 
            name="Revenue" 
            unit="$" 
            stroke={TEXT_COLOR} 
            fontSize={10} 
            tickFormatter={(v) => `$${v}`}
          />
          <ZAxis type="number" dataKey="quantity" range={[40, 400]} name="Quantity Sold" />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }} 
            content={({ active, payload }: any) => {
              if (active && payload && payload.length) {
                const info = payload[0].payload;
                return (
                  <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-lg shadow-xl text-zinc-200 text-xs">
                    <p className="font-semibold text-zinc-400 mb-1">{info.name}</p>
                    <p className="my-0.5">Discount: {info.discountPercent}%</p>
                    <p className="my-0.5 text-brand-400">Revenue: ${info.revenue.toFixed(2)}</p>
                    <p className="my-0.5 text-pink-400">Quantity: {info.quantity} units</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter name="Deals Efficacy" data={formattedData} fill="#8b5cf6" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};
