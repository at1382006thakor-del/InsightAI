"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { LayoutFrame } from "../../components/LayoutFrame";
import { ShieldCheck, Users as UsersIcon, Trash2, CheckCircle, AlertTriangle } from "lucide-react";

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [isAdmin, setIsAdmin] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const user = api.auth.getCurrentUser();
    if (user && user.role === "admin") {
      setIsAdmin(true);
    }
  }, []);

  // Fetch all users list (Admin only)
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ["adminUsersList"],
    queryFn: () => api.admin.listUsers(),
    enabled: isAdmin,
  });

  // Role update mutation
  const updateRoleMutation = useMutation({
    mutationFn: ({ id, role }: { id: number; role: string }) =>
      api.admin.updateRole(id, role),
    onSuccess: (data) => {
      setSuccessMessage("User role updated successfully.");
      queryClient.invalidateQueries({ queryKey: ["adminUsersList"] });
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || err.message || "Failed to update user role.");
    }
  });

  // User delete mutation
  const deleteUserMutation = useMutation({
    mutationFn: (id: number) => api.admin.deleteUser(id),
    onSuccess: () => {
      setSuccessMessage("User account permanently deleted.");
      queryClient.invalidateQueries({ queryKey: ["adminUsersList"] });
    },
    onError: (err: any) => {
      setErrorMessage(err.response?.data?.detail || err.message || "Failed to delete user account.");
    }
  });

  const handleRoleChange = (id: number, role: string) => {
    updateRoleMutation.mutate({ id, role });
  };

  const handleDeleteUser = (id: number) => {
    if (confirm("Are you sure you want to permanently delete this user account? This action cannot be undone.")) {
      deleteUserMutation.mutate(id);
    }
  };

  return (
    <LayoutFrame>
      <div className="space-y-6">
        {successMessage && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <CheckCircle size={16} />
            <span>{successMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <AlertTriangle size={16} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Configurations Form */}
        <div className="glass-panel p-6 rounded-xl border border-zinc-800/80 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-zinc-200">Administrative Controls Panel</h4>
            <p className="text-zinc-500 text-xs">Manage workspace accounts and coordinate roles privileges</p>
          </div>

          {!isAdmin ? (
            <div className="bg-zinc-950/40 border border-zinc-850 p-6 rounded-xl text-center space-y-2 max-w-md mx-auto my-10">
              <ShieldCheck size={24} className="mx-auto text-zinc-600" />
              <h5 className="text-xs font-bold text-zinc-400">Access Restricted</h5>
              <p className="text-[10px] text-zinc-500">Only Administrator users can inspect or edit accounts privileges.</p>
            </div>
          ) : usersLoading ? (
            <div className="text-center text-zinc-500 py-10 text-xs">Loading user list...</div>
          ) : (
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-left text-xs text-zinc-400">
                <thead className="text-[10px] text-zinc-500 uppercase tracking-wider border-b border-zinc-800/80">
                  <tr>
                    <th className="pb-3 font-semibold">User Details</th>
                    <th className="pb-3 font-semibold">Business Email</th>
                    <th className="pb-3 font-semibold text-center">Current Role</th>
                    <th className="pb-3 font-semibold text-center">Modify Privileges</th>
                    <th className="pb-3 font-semibold text-right">Delete Account</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {users?.map((u: any) => (
                    <tr key={u.id} className="hover:bg-zinc-800/10">
                      <td className="py-3.5 font-semibold text-zinc-200 flex items-center gap-2">
                        <span className="w-7 h-7 rounded-full bg-brand-600/10 text-brand-400 flex items-center justify-center font-bold text-[10px]">
                          {u.name.charAt(0)}
                        </span>
                        <span>{u.name}</span>
                      </td>
                      <td className="py-3.5">{u.email}</td>
                      <td className="py-3.5 text-center capitalize font-semibold text-brand-400">{u.role}</td>
                      <td className="py-3.5 text-center">
                        <select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          className="bg-zinc-950 border border-zinc-800 rounded text-[10px] py-1 px-2 text-zinc-300 focus:outline-none focus:border-brand-500 cursor-pointer"
                        >
                          <option value="viewer">Viewer (Read-Only)</option>
                          <option value="analyst">Analyst (View & Export)</option>
                          <option value="admin">Admin (Full Access)</option>
                        </select>
                      </td>
                      <td className="py-3.5 text-right">
                        <button
                          onClick={() => handleDeleteUser(u.id)}
                          className="text-zinc-600 hover:text-red-400 p-1.5 rounded hover:bg-red-500/10 cursor-pointer transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </LayoutFrame>
  );
}
