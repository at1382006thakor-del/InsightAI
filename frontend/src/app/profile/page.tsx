"use client";

import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { LayoutFrame } from "../../components/LayoutFrame";
import { User as UserIcon, Shield, Mail, Key, CheckCircle, AlertTriangle } from "lucide-react";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess("");
    setError("");

    if (newPassword !== confirmPassword) {
      setError("New password and confirm password do not match.");
      return;
    }

    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters long.");
      return;
    }

    // Mock successful password change
    setSuccess("Password updated successfully.");
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  return (
    <LayoutFrame>
      <div className="space-y-6 max-w-2xl">
        {success && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <CheckCircle size={16} />
            <span>{success}</span>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* User Profile Card */}
        <div className="glass-panel p-6 rounded-xl border border-zinc-800/80 space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-brand-600/10 border border-brand-500/30 flex items-center justify-center text-2xl font-bold text-brand-400">
              {user?.name.charAt(0)}
            </div>
            <div>
              <h3 className="text-lg font-bold text-zinc-100">{user?.name}</h3>
              <p className="text-zinc-500 text-xs mt-0.5 capitalize">{user?.role} Account</p>
            </div>
          </div>

          <div className="border-t border-zinc-800/50 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 bg-zinc-950/40 p-3 rounded-lg border border-zinc-900">
              <Mail size={16} className="text-zinc-500" />
              <div>
                <p className="text-[10px] text-zinc-500 uppercase font-bold">Email Address</p>
                <p className="text-xs text-zinc-300 font-semibold">{user?.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 bg-zinc-950/40 p-3 rounded-lg border border-zinc-900">
              <Shield size={16} className="text-zinc-500" />
              <div>
                <p className="text-[10px] text-zinc-500 uppercase font-bold">Access Scope Privilege</p>
                <p className="text-xs text-zinc-300 font-semibold capitalize">{user?.role}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Password update Form */}
        <div className="glass-panel p-6 rounded-xl border border-zinc-800/80 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-zinc-200">Update Profile Password</h4>
            <p className="text-zinc-500 text-xs">Verify current password to authenticate new credential updates</p>
          </div>

          <form onSubmit={handlePasswordChange} className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <label className="text-zinc-400 text-xs font-semibold">Current Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                  <Key size={14} />
                </span>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-xs text-zinc-200 focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-zinc-400 text-xs font-semibold">New Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                  <Key size={14} />
                </span>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-xs text-zinc-200 focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-zinc-400 text-xs font-semibold">Confirm New Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-zinc-500">
                  <Key size={14} />
                </span>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-xs text-zinc-200 focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs py-2.5 px-4 rounded-lg transition-colors cursor-pointer"
              >
                Change Password
              </button>
              <button
                type="button"
                onClick={logout}
                className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700/60 text-red-400 font-semibold text-xs py-2.5 px-4 rounded-lg transition-colors cursor-pointer"
              >
                Log Out
              </button>
            </div>
          </form>
        </div>
      </div>
    </LayoutFrame>
  );
}
