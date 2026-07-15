"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";
import { Sparkles, User as UserIcon, Lock, Mail, AlertCircle, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("viewer");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.auth.register(name.trim(), email.trim().toLowerCase(), password, role);
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        "Account creation failed. Please check your credentials and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center items-center px-4 relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute w-[400px] h-[400px] rounded-full bg-violet-600/10 blur-[120px] -top-20 -left-20 pointer-events-none"></div>
      <div className="absolute w-[400px] h-[400px] rounded-full bg-indigo-600/10 blur-[120px] -bottom-20 -right-20 pointer-events-none"></div>

      <div className="w-full max-w-md z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-xl shadow-violet-500/20 mb-3 animate-pulse-subtle">
            <Sparkles size={24} />
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Insight<span className="text-brand-500">AI</span> Console
          </h1>
          <p className="text-zinc-500 text-xs mt-1">Join the next generation AI business analyst platform</p>
        </div>

        <div className="bg-zinc-900/60 backdrop-blur-md border border-zinc-800 rounded-2xl p-8 shadow-2xl shadow-black/20">
          <h2 className="text-lg font-bold text-zinc-100 mb-6">Create account</h2>
          
          {success && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-lg text-xs font-semibold mb-5 text-center">
              Registration successful! Redirecting to Login...
            </div>
          )}

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3.5 rounded-lg text-xs flex items-start gap-2.5 mb-5">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-zinc-400 text-xs font-semibold mb-1.5">Full Name</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                  <UserIcon size={16} />
                </span>
                <input
                  type="text"
                  required
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>
            </div>

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
              <label className="block text-zinc-400 text-xs font-semibold mb-1.5">Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  required
                  placeholder="•••••••• (min 8 chars)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-zinc-400 text-xs font-semibold mb-1.5">Account Role</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: "viewer", label: "Viewer" },
                  { id: "analyst", label: "Analyst" },
                  { id: "admin", label: "Admin" }
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setRole(item.id)}
                    className={`py-2 text-xs font-medium border rounded-lg transition-all cursor-pointer ${
                      role === item.id 
                        ? "bg-brand-600 border-brand-500 text-white" 
                        : "bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-700/60"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || success}
              className="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-6 shadow-lg shadow-brand-500/20 disabled:opacity-55 cursor-pointer"
            >
              {loading ? (
                <span>Creating account...</span>
              ) : (
                <>
                  <span>Sign Up</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <div className="mt-4 text-center">
            <span className="text-zinc-500 text-xs">Already have an account? </span>
            <Link href="/login" className="text-brand-400 hover:text-brand-300 text-xs font-semibold">
              Log In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
