import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Attach Authorization header if token exists
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("insightai_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle unauthorized responses dynamically
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("insightai_token");
        localStorage.removeItem("insightai_user");
        if (!window.location.pathname.includes("/login")) {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // 1. Authentication
  auth: {
    login: async (email: string, password: string) => {
      const { data } = await apiClient.post("/auth/login", { email, password });
      localStorage.setItem("insightai_token", data.access_token);
      localStorage.setItem("insightai_user", JSON.stringify(data.user));
      return data;
    },
    register: async (name: string, email: string, password: string, role = "viewer") => {
      const { data } = await apiClient.post("/auth/register", { name, email, password, role });
      return data;
    },
    forgotPassword: async (email: string) => {
      const { data } = await apiClient.post("/auth/forgot-password", { email });
      return data;
    },
    resetPassword: async (payload: { token: string; new_password: string }) => {
      const { data } = await apiClient.post("/auth/reset-password", payload);
      return data;
    },
    logout: () => {
      localStorage.removeItem("insightai_token");
      localStorage.removeItem("insightai_user");
      window.location.href = "/login";
    },
    getMe: async () => {
      const { data } = await apiClient.get("/auth/me");
      return data;
    },
    getCurrentUser: () => {
      if (typeof window === "undefined") return null;
      const userStr = localStorage.getItem("insightai_user");
      return userStr ? JSON.parse(userStr) : null;
    }
  },

  // 2. Dataset Management
  datasets: {
    list: async () => {
      const { data } = await apiClient.get("/datasets");
      return data;
    },
    upload: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post("/datasets/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return data;
    },
    clean: async (payload: {
      file_path: string;
      mapping_json: Record<string, string>;
      fill_missing?: boolean;
      remove_duplicates?: boolean;
    }) => {
      const formData = new FormData();
      formData.append("file_path", payload.file_path);
      formData.append("mapping_json", JSON.stringify(payload.mapping_json));
      formData.append("fill_missing", String(payload.fill_missing ?? true));
      formData.append("remove_duplicates", String(payload.remove_duplicates ?? true));
      
      const { data } = await apiClient.post("/data/clean", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return data;
    },
    toggleActive: async (id: string) => {
      const { data } = await apiClient.patch(`/datasets/${id}/active`);
      return data;
    },
    delete: async (id: string) => {
      const { data } = await apiClient.delete(`/datasets/${id}`);
      return data;
    }
  },

  // 3. Dashboard Metrics & Charts
  dashboard: {
    getSummary: async (filters: { startDate?: string; endDate?: string; region?: string } = {}) => {
      const params = new URLSearchParams();
      if (filters.startDate) params.append("start_date", filters.startDate);
      if (filters.endDate) params.append("end_date", filters.endDate);
      if (filters.region) params.append("region", filters.region);
      
      const { data } = await apiClient.get(`/dashboard/summary?${params.toString()}`);
      return data;
    },
    getTimeseries: async (filters: { startDate?: string; endDate?: string; region?: string } = {}) => {
      const params = new URLSearchParams();
      if (filters.startDate) params.append("start_date", filters.startDate);
      if (filters.endDate) params.append("end_date", filters.endDate);
      if (filters.region) params.append("region", filters.region);

      const { data } = await apiClient.get(`/dashboard/charts/timeseries?${params.toString()}`);
      return data;
    },
    getCategorySales: async (filters: { startDate?: string; endDate?: string; region?: string } = {}) => {
      const params = new URLSearchParams();
      if (filters.startDate) params.append("start_date", filters.startDate);
      if (filters.endDate) params.append("end_date", filters.endDate);
      if (filters.region) params.append("region", filters.region);

      const { data } = await apiClient.get(`/dashboard/charts/category?${params.toString()}`);
      return data;
    },
    getRegionalSales: async (filters: { startDate?: string; endDate?: string } = {}) => {
      const params = new URLSearchParams();
      if (filters.startDate) params.append("start_date", filters.startDate);
      if (filters.endDate) params.append("end_date", filters.endDate);

      const { data } = await apiClient.get(`/dashboard/charts/regional?${params.toString()}`);
      return data;
    },
    getNotifications: async () => {
      const { data } = await apiClient.get("/dashboard/notifications");
      return data;
    },
    markNotificationRead: async (id: number) => {
      const { data } = await apiClient.post(`/dashboard/notifications/read/${id}`);
      return data;
    }
  },

  // 4. Analytics Deep Dive
  analytics: {
    getProducts: async (filters: { limit?: number; sortBy?: string; category?: string } = {}) => {
      const params = new URLSearchParams();
      if (filters.limit) params.append("limit", String(filters.limit));
      if (filters.sortBy) params.append("sort_by", filters.sortBy);
      if (filters.category) params.append("category", filters.category);

      const { data } = await apiClient.get(`/dashboard/products/performance?${params.toString()}`);
      return data;
    },
    getCustomers: async (filters: { limit?: number; segment?: string } = {}) => {
      const params = new URLSearchParams();
      if (filters.limit) params.append("limit", String(filters.limit));
      if (filters.segment) params.append("segment", filters.segment);

      const { data } = await apiClient.get(`/dashboard/customers/performance?${params.toString()}`);
      return data;
    }
  },

  // 5. ML Sales Forecasting & Client analytics
  predict: {
    train: async (modelType: string) => {
      const { data } = await apiClient.post("/predict/train", { model_type: modelType });
      return data;
    },
    run: async (payload: { monthsAhead?: number; modelType?: string; region?: string; category?: string }) => {
      const { data } = await apiClient.post("/predict/run", {
        months_ahead: payload.monthsAhead || 6,
        model_type: payload.modelType || "xgboost",
        region: payload.region || null,
        category: payload.category || null,
      });
      return data;
    }
  },

  // 6. AI Conversational Assistant
  chat: {
    sendMessage: async (conversationId: number, message: string) => {
      const { data } = await apiClient.post("/chat", {
        conversation_id: conversationId,
        message
      });
      return data;
    },
    listConversations: async () => {
      const { data } = await apiClient.get("/chat/conversations");
      return data;
    },
    createConversation: async (title = "New Discussion") => {
      const { data } = await apiClient.post("/chat/conversations", { title });
      return data;
    },
    getMessages: async (conversationId: number) => {
      const { data } = await apiClient.get(`/chat/conversations/${conversationId}/messages`);
      return data;
    },
    deleteConversation: async (conversationId: number) => {
      const { data } = await apiClient.delete(`/chat/conversations/${conversationId}`);
      return data;
    }
  },

  // 7. Strategy Reports
  reports: {
    list: async () => {
      const { data } = await apiClient.get("/reports/list");
      return data;
    },
    generate: async (reportType: string, fileFormat: "pdf" | "pptx" = "pdf") => {
      const { data } = await apiClient.post("/reports/generate", {
        report_type: reportType,
        file_format: fileFormat
      });
      return data;
    },
    getDownloadUrl: (reportId: string) => {
      return `${API_BASE_URL}/reports/download/${reportId}`;
    }
  },

  // 8. Admin Users Management
  admin: {
    listUsers: async () => {
      const { data } = await apiClient.get("/users");
      return data;
    },
    updateRole: async (userId: number, role: string) => {
      const { data } = await apiClient.patch(`/users/${userId}/role`, { role });
      return data;
    },
    deleteUser: async (userId: number) => {
      const { data } = await apiClient.delete(`/users/${userId}`);
      return data;
    }
  },

  // 9. System Configurations Settings
  settings: {
    get: async () => {
      const { data } = await apiClient.get("/settings");
      return data;
    },
    update: async (payload: { gemini_api_key?: string; database_type?: string }) => {
      const { data } = await apiClient.post("/settings", payload);
      return data;
    }
  }
};
