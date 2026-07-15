"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { Sparkles, Lock, Mail, AlertCircle, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email.trim().toLowerCase(), password);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        "Invalid email or password. Please verify and try again."
      );
      setLoading(false);
    }
  };

  const handleQuickLogin = (role: "admin" | "analyst") => {
    if (role === "admin") {
      setEmail("admin@insightai.com");
      setPassword("admin123");
    } else {
      setEmail("user@insightai.com"); // standard user / analyst
      setPassword("user123");
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center items-center px-4 relative overflow-hidden">
      {/* Glow Orbs background decor */}
      <div className="absolute w-[400px] h-[400px] rounded-full bg-violet-600/10 blur-[120px] -top-20 -left-20 pointer-events-none"></div>
      <div className="absolute w-[400px] h-[400px] rounded-full bg-indigo-600/10 blur-[120px] -bottom-20 -right-20 pointer-events-none"></div>

      <div className="w-full max-w-md z-10">
        {/* Logo Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-xl shadow-violet-500/20 mb-3 animate-pulse-subtle">
            <Sparkles size={24} />
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Insight<span className="text-brand-500">AI</span> Console
          </h1>
          <p className="text-zinc-500 text-xs mt-1">AI-Powered Sales Analytics & Strategy Assistant</p>
        </div>

        {/* Form container */}
        <div className="bg-zinc-900/60 backdrop-blur-md border border-zinc-800 rounded-2xl p-8 shadow-2xl shadow-black/20">
          <h2 className="text-lg font-bold text-zinc-100 mb-6">Sign In to Platform</h2>
          
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3.5 rounded-lg text-xs flex items-start gap-2.5 mb-5">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-zinc-400 text-xs font-semibold mb-1.5">Business Email</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                  <Mail size={16} />
                </span>
                <input
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-zinc-400 text-xs font-semibold">Password</label>
                <Link href="/forgot-password" className="text-brand-400 hover:text-brand-300 text-[10px]">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || authLoading}
              className="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-6 shadow-lg shadow-brand-500/20 disabled:opacity-55 cursor-pointer"
            >
              {loading ? (
                <span>Verifying credentials...</span>
              ) : (
                <>
                  <span>Log In</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* User Sign-up link */}
          <div className="mt-4 text-center">
            <span className="text-zinc-500 text-xs">Don&apos;t have an account? </span>
            <Link href="/register" className="text-brand-400 hover:text-brand-300 text-xs font-semibold">
              Create Account
            </Link>
          </div>

          {/* Quick login panel */}
          <div className="mt-8 border-t border-zinc-800/80 pt-6">
            <p className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider text-center mb-3">
              Quick Demo Access
            </p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handleQuickLogin("admin")}
                className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700/80 text-zinc-300 text-xs py-2 rounded-lg transition-all cursor-pointer"
              >
                Admin (Full Access)
              </button>
              <button
                onClick={() => handleQuickLogin("analyst")}
                className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700/80 text-zinc-300 text-xs py-2 rounded-lg transition-all cursor-pointer"
              >
                Sales Analyst
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
