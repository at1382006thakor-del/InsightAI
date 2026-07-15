"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import {
  LayoutDashboard,
  TrendingUp,
  Sparkles,
  FileText,
  Settings as SettingsIcon,
  LogOut,
  Bell,
  Menu,
  CheckCircle,
  AlertTriangle,
  Info,
  ChevronLeft,
  ChevronRight,
  Database,
  Users as UsersIcon,
  ShieldCheck
} from "lucide-react";

interface LayoutFrameProps {
  children: React.ReactNode;
}

export const LayoutFrame: React.FC<LayoutFrameProps> = ({ children }) => {
  const { user, logout, isAdmin, isAnalyst } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [notifDropdownOpen, setNotifDropdownOpen] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, [pathname]);

  const fetchNotifications = async () => {
    try {
      const data = await api.dashboard.getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error("Failed to load notifications", err);
    }
  };

  const handleMarkAsRead = async (id: number) => {
    try {
      await api.dashboard.markNotificationRead(id);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error(err);
    }
  };

  const menuItems = [
    { name: "Overview", path: "/", icon: LayoutDashboard, role: "viewer" },
    { name: "Sales Analytics", path: "/analytics", icon: TrendingUp, role: "viewer" },
    { name: "AI Assistant", path: "/chat", icon: Sparkles, role: "viewer" },
    { name: "ML Forecasting", path: "/forecast", icon: Sparkles, role: "analyst" },
    { name: "Strategy Reports", path: "/reports", icon: FileText, role: "analyst" },
    { name: "Dataset Ingestion", path: "/datasets/upload", icon: Database, role: "admin" },
    { name: "Admin Dashboard", path: "/admin", icon: ShieldCheck, role: "admin" },
    { name: "System Settings", path: "/settings", icon: SettingsIcon, role: "viewer" }
  ];

  const getPageTitle = () => {
    const matched = menuItems.find(item => item.path === pathname);
    return matched ? matched.name : "InsightAI Console";
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="min-h-screen bg-zinc-950 flex font-sans">
      {/* Sidebar Navigation Panel */}
      <aside 
        className={`${
          sidebarOpen ? "w-64" : "w-20"
        } bg-zinc-900 border-r border-zinc-800 transition-all duration-300 flex flex-col z-20 fixed md:static h-full min-h-screen`}
      >
        {/* Logo and collapse switch */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-zinc-800/80">
          <Link href="/" className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center font-bold text-white text-base shadow-lg shadow-violet-500/20">
              I
            </span>
            {sidebarOpen && (
              <span className="font-extrabold text-white tracking-wide bg-gradient-to-r from-zinc-50 to-zinc-200 bg-clip-text text-transparent text-sm">
                Insight<span className="text-brand-400">AI</span>
              </span>
            )}
          </Link>
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-zinc-400 hover:text-white md:block hidden p-1 hover:bg-zinc-800 rounded-lg"
          >
            {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
          </button>
        </div>

        {/* Dynamic Nav list */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {menuItems.map((item) => {
            // Role gates checks
            if (item.role === "admin" && !isAdmin) return null;
            if (item.role === "analyst" && !isAnalyst) return null;

            const isActive = pathname === item.path;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                href={item.path}
                className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive 
                    ? "bg-brand-600/10 text-brand-400 border border-brand-500/25 shadow-md shadow-brand-500/5" 
                    : "text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-200 border border-transparent"
                }`}
              >
                <Icon size={18} className={isActive ? "text-brand-400" : "text-zinc-400"} />
                {sidebarOpen && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User context footer */}
        <div className="p-4 border-t border-zinc-800/80 flex flex-col gap-2">
          {user && sidebarOpen && (
            <div className="flex items-center gap-3 px-2 py-1 mb-2 bg-zinc-950/30 border border-zinc-800/50 rounded-lg">
              <div className="w-8 h-8 rounded-full bg-brand-800/60 border border-brand-500/30 flex items-center justify-center text-xs font-bold text-brand-300">
                {user.name.charAt(0)}
              </div>
              <div className="truncate flex-1">
                <p className="text-zinc-200 text-xs font-semibold">{user.name}</p>
                <p className="text-zinc-500 text-[10px] capitalize">{user.role}</p>
              </div>
            </div>
          )}
          
          <button
            onClick={logout}
            className="flex items-center gap-4 px-4 py-3 rounded-lg text-sm text-zinc-400 hover:bg-red-950/10 hover:text-red-400 hover:border-red-500/20 border border-transparent transition-all duration-200 w-full"
          >
            <LogOut size={18} />
            {sidebarOpen && <span>Log Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Panel Viewport */}
      <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        {/* Top Navbar Header */}
        <header className="h-16 border-b border-zinc-800/80 bg-zinc-900/40 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-bold text-zinc-100">{getPageTitle()}</h1>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Notification bell dropdown list */}
            <div className="relative">
              <button
                onClick={() => setNotifDropdownOpen(!notifDropdownOpen)}
                className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700/80 flex items-center justify-center text-zinc-400 hover:text-white relative transition-all duration-200"
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-500 ring-2 ring-zinc-900 animate-pulse"></span>
                )}
              </button>
              
              {notifDropdownOpen && (
                <div className="absolute right-0 mt-2 w-80 rounded-xl bg-zinc-900 border border-zinc-800 shadow-2xl p-2 z-50">
                  <div className="flex justify-between items-center px-3 py-2 border-b border-zinc-800/50 mb-1">
                    <span className="text-xs font-semibold text-zinc-400">System Notifications</span>
                    {unreadCount > 0 && (
                      <span className="bg-brand-500/20 text-brand-400 px-2 py-0.5 rounded-full text-[10px] font-bold">
                        {unreadCount} unread
                      </span>
                    )}
                  </div>
                  
                  <div className="max-h-72 overflow-y-auto space-y-1">
                    {notifications.length === 0 ? (
                      <div className="text-center text-zinc-500 py-6 text-xs">
                        No recent notifications.
                      </div>
                    ) : (
                      notifications.map(n => {
                        const NotifIcon = n.type === "success" ? CheckCircle : n.type === "warning" ? AlertTriangle : Info;
                        const iconColor = n.type === "success" ? "text-emerald-400" : n.type === "warning" ? "text-amber-400" : "text-sky-400";
                        const bgOverlay = n.is_read ? "opacity-60" : "bg-zinc-800/30";

                        return (
                          <div 
                            key={n.id} 
                            onClick={() => handleMarkAsRead(n.id)}
                            className={`p-2.5 rounded-lg border border-transparent hover:border-zinc-800 hover:bg-zinc-800/20 cursor-pointer flex gap-3 items-start transition-all ${bgOverlay}`}
                          >
                            <NotifIcon size={14} className={`${iconColor} mt-0.5 flex-shrink-0`} />
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-zinc-300 leading-tight">{n.title}</p>
                              <p className="text-[10px] text-zinc-500 leading-snug mt-0.5">{n.message}</p>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <div className="w-[1px] h-6 bg-zinc-800"></div>
            
            {user && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center text-xs font-extrabold text-white">
                  {user.name.charAt(0)}
                </div>
                <div className="hidden sm:block">
                  <p className="text-xs font-semibold text-zinc-200">{user.name}</p>
                  <p className="text-[9px] text-zinc-500 capitalize">{user.role} Account</p>
                </div>
              </div>
            )}
          </div>
        </header>
        
        {/* Main Panel Viewport */}
        <main className="flex-1 p-8 overflow-y-auto max-w-[1400px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
