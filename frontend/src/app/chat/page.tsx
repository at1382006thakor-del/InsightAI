"use client";

import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../services/api";
import { LayoutFrame } from "../../components/LayoutFrame";
import { Sparkles, Send, Plus, Trash2, HelpCircle, Brain, User as UserIcon } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from "recharts";

const CHART_COLORS = ["#8b5cf6", "#ec4899", "#a78bfa", "#c084fc"];

export default function ChatPage() {
  const queryClient = useQueryClient();
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messageText, setMessageText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // 1. Fetch conversations list
  const { data: conversations, isLoading: convsLoading } = useQuery({
    queryKey: ["chatConversations"],
    queryFn: () => api.chat.listConversations(),
  });

  // Automatically select the first conversation if none is selected
  useEffect(() => {
    if (conversations && conversations.length > 0 && !activeConversationId) {
      setActiveConversationId(conversations[0].id);
    }
  }, [conversations, activeConversationId]);

  // 2. Fetch messages in active conversation
  const { data: messages, isLoading: messagesLoading, refetch: refetchMessages } = useQuery({
    queryKey: ["chatMessages", activeConversationId],
    queryFn: () => api.chat.getMessages(activeConversationId!),
    enabled: !!activeConversationId,
  });

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 3. Create conversation mutation
  const createConvMutation = useMutation({
    mutationFn: (title: string) => api.chat.createConversation(title),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["chatConversations"] });
      setActiveConversationId(data.id);
    }
  });

  // 4. Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: ({ conversationId, text }: { conversationId: number; text: string }) =>
      api.chat.sendMessage(conversationId, text),
    onSuccess: () => {
      setMessageText("");
      refetchMessages();
    }
  });

  // 5. Delete conversation mutation
  const deleteConvMutation = useMutation({
    mutationFn: (id: number) => api.chat.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chatConversations"] });
      setActiveConversationId(null);
    }
  });

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageText.trim() || !activeConversationId) return;
    sendMessageMutation.mutate({
      conversationId: activeConversationId,
      text: messageText.trim(),
    });
  };

  const handleCreateNewDiscussion = () => {
    createConvMutation.mutate("New Discussion");
  };

  const handleDeleteConversation = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteConvMutation.mutate(id);
  };

  const handleSuggestionClick = (query: string) => {
    if (!activeConversationId) return;
    sendMessageMutation.mutate({
      conversationId: activeConversationId,
      text: query,
    });
  };

  // Helper to render inline dynamic Recharts graphs inside messages
  const renderMessageChart = (chartMeta: any) => {
    if (!chartMeta || !chartMeta.type || !chartMeta.data || chartMeta.data.length === 0) return null;
    
    const type = chartMeta.type.toLowerCase();
    const xKey = chartMeta.xKey || "name";
    const yKey = chartMeta.yKey || "value";
    const data = chartMeta.data;

    return (
      <div className="w-full h-48 bg-zinc-950/60 p-3 rounded-lg border border-zinc-800/80 mt-3 max-w-lg">
        <ResponsiveContainer width="100%" height="100%">
          {type === "line" ? (
            <LineChart data={data}>
              <CartesianGrid stroke="#27272a" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xKey} stroke="#a1a1aa" fontSize={8} tickLine={false} />
              <YAxis stroke="#a1a1aa" fontSize={8} tickLine={false} />
              <Tooltip />
              <Line type="monotone" dataKey={yKey} stroke="#8b5cf6" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid stroke="#27272a" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={xKey} stroke="#a1a1aa" fontSize={8} tickLine={false} />
              <YAxis stroke="#a1a1aa" fontSize={8} tickLine={false} />
              <Tooltip />
              <Bar dataKey={yKey} fill="#8b5cf6" radius={[2, 2, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <LayoutFrame>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-8.5rem)] max-h-[800px]">
        {/* Left conversations list */}
        <div className="glass-panel rounded-xl border border-zinc-800/80 p-4 flex flex-col justify-between h-full">
          <div className="space-y-4 flex-1 overflow-y-auto">
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400">Discussion Threads</h4>
              <button
                onClick={handleCreateNewDiscussion}
                className="w-7 h-7 rounded-lg bg-brand-600/10 border border-brand-500/20 flex items-center justify-center text-brand-400 hover:bg-brand-600 hover:text-white transition-all cursor-pointer"
              >
                <Plus size={14} />
              </button>
            </div>

            <div className="space-y-1.5 mt-2">
              {convsLoading ? (
                <div className="text-zinc-600 text-xs text-center py-10">Loading discussions...</div>
              ) : conversations?.length === 0 ? (
                <div className="text-zinc-600 text-xs text-center py-10">No discussions yet. Create one.</div>
              ) : (
                conversations?.map((c: any) => (
                  <div
                    key={c.id}
                    onClick={() => setActiveConversationId(c.id)}
                    className={`px-3 py-2.5 rounded-lg text-xs font-medium cursor-pointer flex justify-between items-center transition-all ${
                      activeConversationId === c.id
                        ? "bg-zinc-800 text-zinc-200 border border-zinc-700/80"
                        : "text-zinc-400 hover:bg-zinc-800/30 hover:text-zinc-300 border border-transparent"
                    }`}
                  >
                    <span className="truncate max-w-[120px]">{c.title}</span>
                    <button
                      onClick={(e) => handleDeleteConversation(c.id, e)}
                      className="text-zinc-600 hover:text-red-400 transition-colors p-0.5"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="border-t border-zinc-800/50 pt-4 flex items-center gap-2 text-[10px] text-zinc-500">
            <Brain size={14} />
            <span>Google Gemini-2.5-flash engine</span>
          </div>
        </div>

        {/* Right chat panel */}
        <div className="lg:col-span-3 glass-panel rounded-xl border border-zinc-800/80 flex flex-col h-full overflow-hidden">
          {/* Active Chat Feed */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4 scroll-smooth bg-zinc-950/20">
            {!activeConversationId ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
                <span className="w-12 h-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
                  <Sparkles size={20} />
                </span>
                <div>
                  <h4 className="text-sm font-semibold text-zinc-300">Choose a Conversation</h4>
                  <p className="text-zinc-500 text-xs mt-1">Select a discuss thread from the left or create a new one to explore sales analytics.</p>
                </div>
              </div>
            ) : messagesLoading ? (
              <div className="h-full flex items-center justify-center text-zinc-500 text-xs">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-brand-500 mr-2"></div>
                <span>Syncing message history...</span>
              </div>
            ) : messages?.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-md mx-auto">
                <span className="w-10 h-10 rounded-full bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
                  <Sparkles size={16} />
                </span>
                <div>
                  <h4 className="text-sm font-semibold text-zinc-300">Ask the AI Business Assistant</h4>
                  <p className="text-zinc-500 text-xs mt-1 leading-relaxed">
                    Query your data using natural language. Ask Gemini to analyze margins, detect category changes, list top products, or run custom projections.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2.5 pt-4 w-full">
                  {[
                    "Show top selling products",
                    "Which region generated the highest revenue?",
                    "Compare Q2 profit by category",
                    "List clients with high churn risk"
                  ].map(suggestion => (
                    <button
                      key={suggestion}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700/60 p-2.5 rounded-lg text-[10px] text-zinc-400 text-left hover:text-zinc-200 transition-all cursor-pointer"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4 pr-1">
                {messages?.map((m: any) => {
                  const isUser = m.sender === "user";
                  return (
                    <div
                      key={m.id}
                      className={`flex gap-3 max-w-[85%] ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}
                    >
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border flex-shrink-0 ${
                        isUser 
                          ? "bg-brand-600/10 border-brand-500/20 text-brand-400" 
                          : "bg-zinc-900 border-zinc-800 text-zinc-400"
                      }`}>
                        {isUser ? <UserIcon size={14} /> : <Sparkles size={14} />}
                      </span>

                      <div className={`p-4.5 rounded-2xl text-xs leading-relaxed ${
                        isUser 
                          ? "bg-brand-600 text-white rounded-tr-none" 
                          : "bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-tl-none shadow-md shadow-black/5"
                      }`}>
                        <p className="whitespace-pre-wrap">{m.message}</p>
                        {!isUser && m.chart_metadata && renderMessageChart(m.chart_metadata)}
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Form input line */}
          {activeConversationId && (
            <form onSubmit={handleSendMessage} className="p-4 border-t border-zinc-800/80 bg-zinc-900/40 backdrop-blur flex gap-3 items-center">
              <input
                type="text"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                placeholder="Ask about sales margin, top products, outliers..."
                disabled={sendMessageMutation.isPending}
                className="flex-1 bg-zinc-950 border border-zinc-800 hover:border-zinc-700/60 rounded-lg text-xs py-3 px-4 text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                disabled={!messageText.trim() || sendMessageMutation.isPending}
                className="w-10 h-10 rounded-lg bg-brand-600 hover:bg-brand-500 text-white flex items-center justify-center transition-all shadow-md shadow-brand-500/10 cursor-pointer disabled:opacity-50"
              >
                <Send size={14} className={sendMessageMutation.isPending ? "animate-pulse" : ""} />
              </button>
            </form>
          )}
        </div>
      </div>
    </LayoutFrame>
  );
}
