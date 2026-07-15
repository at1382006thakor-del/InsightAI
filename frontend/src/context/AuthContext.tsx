"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";
import { useRouter, usePathname } from "next/navigation";

interface User {
  id: number;
  name: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<any>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isAnalyst: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Load local auth cache on hydration
    const cachedToken = localStorage.getItem("insightai_token");
    const cachedUser = localStorage.getItem("insightai_user");
    
    if (cachedToken && cachedUser) {
      setToken(cachedToken);
      setUser(JSON.parse(cachedUser));
    }
    
    setLoading(false);
  }, []);

  // Monitor paths and check permissions
  useEffect(() => {
    if (loading) return;

    const publicPaths = ["/login", "/register", "/forgot-password", "/reset-password"];
    const isPublicPath = publicPaths.some(path => pathname.startsWith(path));
    
    if (!token && !isPublicPath) {
      router.replace("/login");
    } else if (token && isPublicPath) {
      router.replace("/");
    }

    // Role-based path checks
    if (token && user) {
      const adminOnlyPaths = ["/datasets/upload", "/datasets/history", "/admin"];
      const analystPaths = ["/forecast", "/reports"];
      
      const isAdminPath = adminOnlyPaths.some(path => pathname.startsWith(path));
      const isAnalystPath = analystPaths.some(path => pathname.startsWith(path));
      
      if (isAdminPath && user.role !== "admin") {
        router.replace("/");
      } else if (isAnalystPath && user.role === "viewer") {
        router.replace("/");
      }
    }
  }, [pathname, token, user, loading, router]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const data = await api.auth.login(email, password);
      setToken(data.access_token);
      setUser(data.user);
      router.push("/");
      return data;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    api.auth.logout();
    setToken(null);
    setUser(null);
    router.replace("/login");
  };

  const isAuthenticated = !!token;
  const isAdmin = user?.role === "admin";
  const isAnalyst = user?.role === "admin" || user?.role === "analyst";

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated,
        isAdmin,
        isAnalyst,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return context;
};
