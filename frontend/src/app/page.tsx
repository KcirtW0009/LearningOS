"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import SkillTree from "@/components/SkillTree";
import { PROFICIENCY_COLORS } from "@/components/SkillTree";
import Onboarding from "@/components/Onboarding";
import LearningRecord from "@/components/LearningRecord";
import { hasSeenOnboarding, markOnboardingSeen, cacheGraphData, getCachedGraphNodes, getCachedGraphEdges } from "@/lib/cache";
import { t, getLang, setLang, onLangChange, clearAllLocalData, type LangCode } from "@/lib/i18n";

/* ═══════════════════════════════════════════════════════════════════
   CONSTANTS
   ═══════════════════════════════════════════════════════════════════ */
const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    return (window as any).__API_URL__ || DEFAULT_API_URL;
  }
  return DEFAULT_API_URL;
};

const getApiUrlAsync = async () => {
  if (typeof window !== 'undefined' && (window as any).electronAPI?.getApiUrl) {
    try {
      const url = await (window as any).electronAPI.getApiUrl();
      (window as any).__API_URL__ = url;
      return url;
    } catch (e) {
      console.warn('Failed to get API URL from Electron:', e);
    }
  }
  return getApiUrl();
};

/* ── Fallback graph packages (used when API unreachable) ── */
const GRAPH_PACKAGES_FALLBACK = [
  { id: "ai-adventurer", name: "AI Adventurer Skill Tree", path: "graphs/ai-adventurer/" },
  { id: "git-fundamentals", name: "Git 基础与实战", path: "graphs/git-fundamentals/" },
  { id: "learn-powershell", name: "Learn PowerShell", path: "graphs/learn-powershell/" },
];

/* ── Difficulty metadata ── */
const DIFF_META: Record<
  string,
  { label: string; color: string; icon: string; ring: string }
> = {
  beginner: {
    label: "入门",
    color: "bg-emerald-100 text-emerald-700",
    icon: "○",
    ring: "ring-emerald-200",
  },
  intermediate: {
    label: "进阶",
    color: "bg-amber-100 text-amber-700",
    icon: "◐",
    ring: "ring-amber-200",
  },
  advanced: {
    label: "高级",
    color: "bg-rose-100 text-rose-700",
    icon: "●",
    ring: "ring-rose-200",
  },
};

/* ── Default score presets (synced with backend DEFAULT_SCORE_PRESETS) ── */
const SCORE_PRESETS = [
  { label: "了解一下", score: 1 },
  { label: "认真学了", score: 5 },
  { label: "动手实践", score: 10 },
  { label: "举一反三", score: 20 },
  { label: "项目实战", score: 50 },
  { label: "传授他人", score: 80 },
];

/* ── Node type metadata ── */
const TYPE_META: Record<string, string> = {
  concept: "📖 概念",
  skill: "🔧 技能",
  project: "🚀 项目",
  milestone: "🏁 里程碑",
};

/* ── Status display ── */
const STATUS_META: Record<string, { label: string; cls: string }> = {
  NOT_STARTED: { label: "待解锁", cls: "bg-slate-100 text-slate-400" },
  LOCKED: { label: "🔒 锁定", cls: "bg-slate-100 text-slate-400" },
  AVAILABLE: { label: "可学习", cls: "bg-emerald-100 text-emerald-700" },
  IN_PROGRESS: { label: "⋯ 学习中", cls: "bg-blue-100 text-blue-700" },
  COMPLETED: { label: "✓ 已完成", cls: "bg-emerald-100 text-emerald-700" },
  MASTERED: { label: "★ 已精通", cls: "bg-violet-100 text-violet-700" },
};

/* ═══════════════════════════════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════════════════════════════ */
type NodeDetail = {
  id: string;
  title: string;
  description: string;
  type: string;
  difficulty: string;
  status: string;
  score: number;
  evidence: string;
  resources: { type: string; uri: string; label: string }[];
  custom_dims?: Record<string, number>;
  proficiency?: { label: string; label_en: string; color: string; icon: string };
};

type Achievement = { id: string; name: string; description: string; icon?: string; priority?: number };

type Toast = { id: number; msg: string; type: "success" | "error" | "info" };

/* ═══════════════════════════════════════════════════════════════════
   API HELPERS (with exponential backoff retry)
   ═══════════════════════════════════════════════════════════════════ */
let toastId = 0;

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 500;

async function api(path: string, options?: RequestInit) {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const res = await fetch(`${getApiUrl()}${path}`, options);
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        // Parse structured error: {error: {code, message, suggestion}}
        if (body?.error) {
          throw new Error(`${body.error.message} (${body.error.suggestion})`);
        }
        throw new Error(body?.detail || `HTTP ${res.status}`);
      }
      return res.json();
    } catch (e: any) {
      lastError = e;
      // Don't retry on 4xx errors (client errors)
      if (e.message?.includes("HTTP 4") || e.message?.includes("VALIDATION_ERROR")) {
        throw e;
      }
      if (attempt < MAX_RETRIES) {
        const delay = BASE_DELAY_MS * Math.pow(2, attempt);
        await new Promise((r) => setTimeout(r, delay));
      }
    }
  }
  throw lastError || new Error("Request failed after retries");
}

/* ═══════════════════════════════════════════════════════════════════
   SVG ICONS (inline — no dependency)
   ═══════════════════════════════════════════════════════════════════ */
const Icon = {
  arrowLeft: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
    </svg>
  ),
  arrowRight: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  ),
  check: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  ),
  undo: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a5 5 0 015 5v2M3 10l4-4M3 10l4 4" />
    </svg>
  ),
  trophy: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 9H4.5a2.5 2.5 0 010-5H6M18 9h1.5a2.5 2.5 0 000-5H18M6 9a3 3 0 013-3h6a3 3 0 013 3M6 9v4a6 6 0 0012 0V9M12 15v4m-3 0h6" />
    </svg>
  ),
  star: () => (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
    </svg>
  ),
  sparkle: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
  ),
  lightBulb: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  ),
  link: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
  ),
  target: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 20a8 8 0 100-16 8 8 0 000 16zm0 0v-2m0-6V6m-6 6H4m4.93-4.93L7.5 5.64m9 9l1.41 1.41m0-10.82L16.5 6.57" />
    </svg>
  ),
  code: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M12 3l7.5 4.5v9L12 21l-7.5-4.5v-9L12 3z" />
    </svg>
  ),
  graph: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zm0 9.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zm0 9.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
  ),
};

/* ═══════════════════════════════════════════════════════════════════
   TOAST NOTIFICATION SYSTEM
   ═══════════════════════════════════════════════════════════════════ */

function ToastContainer({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`animate-slide-up pointer-events-auto px-5 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2 ${
            t.type === "success"
              ? "bg-emerald-600 text-white"
              : t.type === "error"
              ? "bg-rose-600 text-white"
              : "bg-slate-800 text-white"
          }`}
        >
          {t.type === "success" && <Icon.check />}
          {t.type === "error" && (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          )}
          {t.type === "info" && <Icon.sparkle />}
          {t.msg}
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   NODE ID TAG — Shows tier/continent color
   ═══════════════════════════════════════════════════════════════════ */
const TIER_COLORS: Record<string, string> = {
  found: "bg-slate-600 text-white",
  vis: "bg-sky-600 text-white",
  lang: "bg-indigo-600 text-white",
  gen: "bg-fuchsia-600 text-white",
  mm: "bg-teal-600 text-white",
  agent: "bg-amber-600 text-white",
  emb: "bg-rose-600 text-white",
  boss: "bg-red-500 text-white",
};

function NodeIdTag({ id }: { id: string }) {
  const prefix = id.split("-")[0] || "";
  const color = TIER_COLORS[prefix] || "bg-slate-400 text-white";
  return (
    <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${color}`}>
      {prefix.slice(0, 3).toUpperCase()}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════════════════════════════ */

export default function Home() {
  const mounted = useRef(false);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [graphInfo, setGraphInfo] = useState<any>(null);
  const [availableNodes, setAvailableNodes] = useState<string[]>([]);
  const [allNodes, setAllNodes] = useState<NodeDetail[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeDetail | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [xp, setXp] = useState<any>(null);
  const [previousLevel, setPreviousLevel] = useState(1);
  const [achievements, setAchievements] = useState<{
    earned: Achievement[];
    locked: Achievement[];
  }>({ earned: [], locked: [] });
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [completing, setCompleting] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [scoreDesc, setScoreDesc] = useState("");
  const [customScore, setCustomScore] = useState<number | "">(5);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [showCompleted, setShowCompleted] = useState(false);
  const [activeGraph, setActiveGraph] = useState<string>("ai-adventurer");
  const [undoStack, setUndoStack] = useState<any>(null);
  const [showUndoPanel, setShowUndoPanel] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [taskTarget, setTaskTarget] = useState<string | null>(null);
  const [taskPath, setTaskPath] = useState<any[]>([]);
  const [viewMode, setViewMode] = useState<"list" | "tree">("list");
  const [edges, setEdges] = useState<any[]>([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [undoConfirm, setUndoConfirm] = useState<any>(null); // undo impact preview data
  const [graphPackages, setGraphPackages] = useState<any[]>(GRAPH_PACKAGES_FALLBACK);
  const [packagesLoading, setPackagesLoading] = useState(true);
  const [lang, setLangState] = useState<LangCode>(getLang());
  const [resetConfirm, setResetConfirm] = useState(false);
  const [graphResetConfirm, setGraphResetConfirm] = useState(false);
  const [showLearningRecord, setShowLearningRecord] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareData, setShareData] = useState<any>(null);

  const addToast = useCallback((msg: string, type: Toast["type"] = "info") => {
    const id = ++toastId;
    setToasts((p) => [...p, { id, msg, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3000);
  }, []);

  /* ── Data loading ── */
  const refreshAll = useCallback(async () => {
    try {
      const [allNodesData, info, st, xpData, ach, recs] = await Promise.all([
        api("/nodes/all"),
        api("/graph/info"),
        api("/status"),
        api("/xp"),
        api("/achievements"),
        api("/recommendations?strategy=next_available"),
      ]);
      setAllNodes(allNodesData);
      // Compute available nodes from the status field
      setAvailableNodes(
        allNodesData
          .filter((n: NodeDetail) => n.status === "AVAILABLE" || n.status === "NOT_STARTED")
          .filter((n: NodeDetail) => n.status !== "LOCKED")
          .map((n: NodeDetail) => n.id)
      );
      // Also sync with the /nodes endpoint which returns available IDs
      const availIds = await api("/nodes");
      setAvailableNodes(availIds);
      setGraphInfo(info);
      setStatus(st);
      setXp(xpData);
      const newLevel = xpData.global_level ?? xpData.level ?? 1;
      if (newLevel > previousLevel) {
        addToast(`🎉 恭喜升级！当前等级: Lv.${newLevel}`, "success");
      }
      setPreviousLevel(newLevel);
      setAchievements(ach);
      setRecommendations(recs.recommendations || []);
      // Fetch undo stack and edges
      try {
        const us = await api("/undo/stack");
        setUndoStack(us);
      } catch { /* ignore */ }
      try {
        const edgeData = await api("/graph/edges");
        setEdges(edgeData);
      } catch { /* ignore */ }
    } catch {
      // not yet loaded
    }
  }, []);

  const loadGraph = useCallback(async (graphId: string) => {
    setLoading(true);
    try {
      const pkg = graphPackages.find((g) => g.id === graphId) || graphPackages[0];
      await api("/graph/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: pkg.path }),
      });
      setLoaded(true);
      setActiveGraph(graphId);
      addToast(`${pkg.name} 加载成功`, "success");
      await refreshAll();
    } catch (e: any) {
      addToast(`加载失败: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  }, [graphPackages, refreshAll, addToast]);

  const viewNode = useCallback(
    async (nodeId: string) => {
      try {
        const detail = await api(`/nodes/${nodeId}`);
        setSelectedNode(detail);
      } catch (e: any) {
        addToast(e.message, "error");
      }
    },
    [addToast]
  );

  const completeNode = useCallback(
    async (nodeId: string, score: number) => {
      setCompleting(true);
      try {
        const r = await api(`/nodes/${nodeId}/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ score }),
        });
        addToast(r.message, "success");
        setSelectedNode(null);
        await refreshAll();
      } catch (e: any) {
        addToast(e.message, "error");
      } finally {
        setCompleting(false);
      }
    },
    [refreshAll, addToast]
  );

  const undoLastAction = useCallback(
    async () => {
      // First, check if there's any impact to warn about
      try {
        const impact = await api("/undo/preview");
        if (impact.has_impact) {
          // Show confirmation dialog
          setUndoConfirm(impact);
          return;
        }
        // No impact — proceed directly
        setResetting(true);
        try {
          const r = await api("/undo", { method: "POST" });
          addToast(r.message, "info");
          setSelectedNode(null);
          await refreshAll();
        } finally {
          setResetting(false);
        }
      } catch (e: any) {
        addToast(e.message, "error");
      }
    },
    [refreshAll, addToast]
  );

  const confirmUndo = useCallback(
    async (cascade: boolean) => {
      setUndoConfirm(null);
      setResetting(true);
      try {
        const params = new URLSearchParams();
        params.set("cascade", String(cascade));
        const r = await api(`/undo/cascade?${params.toString()}`, { method: "POST" });
        const msg = cascade
          ? `已撤回并级联重置 ${1 + (r.cascaded?.length || 0)} 个节点`
          : `已撤回 (${r.primary?.title || "unknown"})`;
        addToast(msg, cascade ? "success" : "info");
        setSelectedNode(null);
        await refreshAll();
      } catch (e: any) {
        addToast(e.message, "error");
      } finally {
        setResetting(false);
      }
    },
    [refreshAll, addToast]
  );

  const cancelUndoConfirm = useCallback(() => {
    setUndoConfirm(null);
  }, []);

  const addScore = useCallback(
    async (nodeId: string, scoreDelta: number, description: string) => {
      setScoring(true);
      try {
        const params = new URLSearchParams();
        params.set("score_delta", String(scoreDelta));
        if (description) params.set("description", description);
        const r = await api(`/nodes/${nodeId}/score?${params.toString()}`, {
          method: "POST",
        });
        addToast(r.message, "success");
        setScoreDesc("");
        await refreshAll();
        // Re-fetch node detail
        const detail = await api(`/nodes/${nodeId}`);
        setSelectedNode(detail);
      } catch (e: any) {
        addToast(e.message, "error");
      } finally {
        setScoring(false);
      }
    },
    [refreshAll, addToast]
  );

  const undoMultiple = useCallback(
    async (count: number) => {
      setResetting(true);
      try {
        const r = await api(`/undo/multi?count=${count}`, { method: "POST" });
        addToast(`已撤回 ${r.undone_count} 步操作`, "info");
        setSelectedNode(null);
        setShowUndoPanel(false);
        await refreshAll();
      } catch (e: any) {
        addToast(e.message, "error");
      } finally {
        setResetting(false);
      }
    },
    [refreshAll, addToast]
  );

  const exportPrompt = useCallback(async () => {
    try {
      const data = await api("/export/prompt");
      // Copy to clipboard
      await navigator.clipboard.writeText(data.prompt);
      addToast("提示词已复制到剪贴板！可直接投喂给外部AI", "success");
    } catch (e: any) {
      addToast(`导出失败: ${e.message}`, "error");
    }
  }, [addToast]);

  const exportProgress = useCallback(async () => {
    try {
      const data = await api("/export/progress");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `learningos-progress-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      addToast("进度已导出为JSON文件", "success");
    } catch (e: any) {
      addToast(`导出失败: ${e.message}`, "error");
    }
  }, [addToast]);

  const loadShareData = useCallback(async () => {
    try {
      const data = await api("/export/share");
      setShareData(data);
      setShowShareModal(true);
    } catch (e: any) {
      addToast(`加载分享数据失败: ${e.message}`, "error");
    }
  }, [addToast]);

  const importProgress = useCallback(async () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        const data = JSON.parse(text);
        const result = await api("/import/progress", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        });
        addToast(result.message, "success");
        await refreshAll();
      } catch (e: any) {
        addToast(`导入失败: ${e.message}`, "error");
      }
    };
    input.click();
  }, [addToast, refreshAll]);

  const doSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    if (query.trim().length < 1) {
      setSearchResults([]);
      setSearchOpen(false);
      return;
    }
    try {
      const data = await api(`/search?q=${encodeURIComponent(query)}`);
      setSearchResults(data.results || []);
      setSearchOpen(true);
    } catch { /* ignore */ }
  }, []);

  const startTaskMode = useCallback(async (nodeId: string) => {
    try {
      const data = await api(`/path/${nodeId}`);
      /* Always set target regardless of reachable (even locked) */
      setTaskTarget(nodeId);
      let effectivePath: any[] = [];
      let statusMsg = "";
      if (data.target_finished === true) {
        /* Scenario 1: target already completed/mastered */
        setTaskPath(data.full_path || data.path || []);
        effectivePath = data.pre_path && data.pre_path.length > 0 ? data.pre_path : (data.full_path || []);
        const label = data.target_status === "MASTERED" ? "精通" : "完成";
        statusMsg = `✅ 该节点已${label}，已设为回顾目标（full_path显示前置回顾链）`;
      } else if (data.reachable) {
        /* Scenario 2: reachable & not finished */
        effectivePath = data.path || data.direct_path || [];
        const stepsMsg = effectivePath.length;
        if (stepsMsg > 0) statusMsg = `🎯 任务模式: ${stepsMsg} 步直达目标`;
        else statusMsg = `🎯 已设为当前目标`;
        setTaskPath(effectivePath);
      } else if (data.pre_path && data.pre_path.length > 0) {
        /* Scenario 3: not reachable but has pre_path prerequisites */
        effectivePath = data.pre_path;
        const stepsMsg = effectivePath.length;
        statusMsg = `🔗 需先学习前置 ${stepsMsg} 个节点（推荐从 #1 开始）`;
        setTaskPath(effectivePath);
      } else {
        /* Scenario 4: not reachable and no pre_path */
        effectivePath = data.path || [];
        setTaskPath(effectivePath);
        if (data.target_status && (data.target_status === "COMPLETED" || data.target_status === "MASTERED")) {
          statusMsg = "✅ 已完成节点设为目标";
        } else {
          statusMsg = data.message || "❌ 当前无可用学习路径，请先完成图谱上的前置节点";
        }
      }
      addToast(statusMsg, "info");
    } catch (e: any) {
      addToast(e.message, "error");
    }
  }, [addToast]);

  const clearTaskMode = useCallback(() => {
    setTaskTarget(null);
    setTaskPath([]);
  }, []);

  /* ── Reset all local data (progress cache + onboarding state) ── */
  const doResetLocalData = useCallback(async () => {
    setResetConfirm(false);
    setResetting(true);
    try {
      await clearAllLocalData();
      addToast(lang === "zh-CN" ? "已重置所有本地数据，页面即将刷新..." : "All local data reset. Page will reload...", "success");
      setTimeout(() => window.location.reload(), 1200);
    } catch (e: any) {
      addToast("重置失败: " + e.message, "error");
    } finally {
      setResetting(false);
    }
  }, [addToast, lang]);

  const triggerOnboarding = useCallback(() => {
    // Re-show onboarding by manually resetting only the flag
    setShowOnboarding(true);
  }, []);

  /* ── Reset current graph progress ── */
  const doResetGraph = useCallback(async () => {
    setGraphResetConfirm(false);
    setResetting(true);
    try {
      await api("/graph/reset", { method: "POST" });
      addToast("当前图谱进度已清空", "success");
      setSelectedNode(null);
      await refreshAll();
    } catch (e: any) {
      addToast("清空失败: " + e.message, "error");
    } finally {
      setResetting(false);
    }
  }, [refreshAll, addToast]);

  /* ── Init: fetch packages + URL param support + onboarding check ── */
  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true;

      const init = async () => {
        let currentPackages: any[] = [...GRAPH_PACKAGES_FALLBACK];

        await getApiUrlAsync();

        try {
          const res = await fetch(`${getApiUrl()}/graphs/packages`);
          const data = await res.json();
          if (data?.packages && Array.isArray(data.packages) && data.packages.length > 0) {
            currentPackages = data.packages;
            setGraphPackages(data.packages);
          }
        } catch (e) {
          console.warn("Failed to fetch packages, using fallback", e);
        } finally {
          setPackagesLoading(false);
        }

        try {
          const params = new URLSearchParams(window.location.search);
          const graphParam = params.get("graph");
          const defaultGraph = currentPackages[0]?.id || "ai-adventurer";
          const toLoad = (graphParam && currentPackages.some((p: any) => p.id === graphParam))
            ? graphParam
            : defaultGraph;
          loadGraph(toLoad);
        } catch {
          loadGraph("ai-adventurer");
        }

        try {
          const seen = await hasSeenOnboarding();
          if (!seen) setShowOnboarding(true);
        } catch { /* ignore */ }
      };

      init();
    }
  }, []);

  useEffect(() => {
    return onLangChange((l) => setLangState(l));
  }, []);

  useEffect(() => {
    if (loaded) {
      refreshAll();
      // Cache graph data for offline use
      if (allNodes.length > 0 && edges.length > 0) {
        cacheGraphData(activeGraph, allNodes, edges).catch(() => {});
      }
    }
  }, [loaded]);

  /* ── Filter nodes ── */
  const filteredNodeIds = (() => {
    let pool: string[];
    if (showCompleted) {
      const baseSet = new Set(availableNodes);
      allNodes.forEach((n) => {
        if (n.status === "COMPLETED" || n.status === "MASTERED") {
          baseSet.add(n.id);
        }
      });
      pool = Array.from(baseSet);
    } else {
      pool = availableNodes;
    }
    if (activeFilter === "all") return pool;
    const detailMap = new Map(allNodes.map((n) => [n.id, n]));
    return pool.filter((id) => {
      const d = detailMap.get(id);
      return d?.difficulty === activeFilter;
    });
  })();

  const completedCount = allNodes.filter(
    (n) => n.status === "COMPLETED" || n.status === "MASTERED"
  ).length;

  // Build a quick lookup map for titles
  const titleMap = new Map(allNodes.map((n) => [n.id, n.title]));
  const detailMap = new Map(allNodes.map((n) => [n.id, n]));

  const earnedCount = achievements.earned.length;
  const totalAch = earnedCount + achievements.locked.length;
  
  const xpPercent = xp
    ? Math.min(100, Math.max(0, Math.round(
        ((xp.global_xp ?? xp.total_xp) - ((xp.global_level ?? xp.level - 1) ** 2) * 50) / 
        xp.xp_to_next_level * 100
      )))
    : 0;

  // Is current node completed or mastered?
  const isCompleted = selectedNode?.status === "COMPLETED" || selectedNode?.status === "MASTERED";
  const isMastered = selectedNode?.status === "MASTERED";

  /* ═══════════════════════════════════════════════════════════════
     LANDING SCREEN
     ═══════════════════════════════════════════════════════════════ */
  if (!loaded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-primary-50/30 to-white flex items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-primary-100 text-primary-600 mb-6">
            <Icon.code />
          </div>
          <h1 className="text-4xl font-extrabold text-slate-900 mb-3 tracking-tight">
            Learning<span className="text-primary-600">OS</span>
          </h1>
          <p className="text-slate-500 text-lg mb-8 max-w-sm">
            基于知识图谱的渐进式学习引擎
          </p>
          <div className="flex flex-col items-center gap-3">
            {packagesLoading ? (
              <div className="w-64 py-3 text-center text-slate-400 text-sm">
                <svg className="animate-spin w-5 h-5 inline-block mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                正在获取图谱列表...
              </div>
            ) : (
              graphPackages.map((pkg) => (
                <button
                  key={pkg.id}
                  onClick={() => loadGraph(pkg.id)}
                  disabled={loading}
                  className={`btn-primary text-base px-8 py-3 flex items-center gap-2 disabled:opacity-60 w-64 justify-center ${
                    pkg.id === (graphPackages[0]?.id || "ai-adventurer") ? "" : "btn-ghost"
                  }`}
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      加载中...
                    </>
                  ) : (
                    <>
                      {pkg.id === (graphPackages[0]?.id || "ai-adventurer") ? <Icon.sparkle /> : <Icon.graph />}
                      <span className="truncate max-w-[180px]">{pkg.name}</span>
                      {typeof pkg.node_count === "number" && (
                        <span className="text-[10px] text-slate-400 ml-auto shrink-0">
                          {pkg.node_count}节点
                        </span>
                      )}
                    </>
                  )}
                </button>
              ))
            )}
            <a
              href="/graph-generator"
              className="btn-ghost text-base px-8 py-3 flex items-center gap-2 w-64 justify-center"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Create New Graph
            </a>
          </div>
        </div>
      </div>
    );
  }

  /* ═══════════════════════════════════════════════════════════════
     MAIN INTERFACE
     ═══════════════════════════════════════════════════════════════ */
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Toasts */}
      <ToastContainer toasts={toasts} />

      {/* Onboarding */}
      {showOnboarding && (
        <Onboarding
          onComplete={() => {
            setShowOnboarding(false);
            markOnboardingSeen().catch(() => {});
          }}
        />
      )}

      {/* Undo Safety Confirmation Dialog */}
      {undoConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface-overlay animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden animate-slide-up">
            {/* Header */}
            <div className="px-6 pt-6 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-800">确认撤回操作</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    撤回 <b className="text-slate-700">{undoConfirm.node_title}</b> 将影响以下节点
                  </p>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="px-6 py-4">
              {/* Impact summary */}
              <div className="flex gap-3 mb-4">
                {undoConfirm.orphaned_count > 0 && (
                  <div className="flex-1 bg-rose-50 border border-rose-100 rounded-xl p-3">
                    <div className="text-lg font-bold text-rose-600">{undoConfirm.orphaned_count}</div>
                    <div className="text-xs text-rose-500">已完成节点将失去前置条件</div>
                  </div>
                )}
                {undoConfirm.blocked_count > 0 && (
                  <div className="flex-1 bg-amber-50 border border-amber-100 rounded-xl p-3">
                    <div className="text-lg font-bold text-amber-600">{undoConfirm.blocked_count}</div>
                    <div className="text-xs text-amber-500">节点将变为锁定状态</div>
                  </div>
                )}
              </div>

              {/* Affected nodes list */}
              <div className="space-y-2 max-h-48 overflow-y-auto scrollbar-thin">
                {undoConfirm.affected.map((item: any) => (
                  <div
                    key={item.node_id}
                    className={`flex items-center gap-3 p-2.5 rounded-lg border ${
                      item.impact === "orphaned"
                        ? "bg-rose-50 border-rose-100"
                        : "bg-amber-50 border-amber-100"
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${
                      item.impact === "orphaned" ? "bg-rose-400" : "bg-amber-400"
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-700 truncate">{item.title}</div>
                      <div className="text-[10px] text-slate-400">{item.node_id}</div>
                    </div>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                      item.impact === "orphaned"
                        ? "bg-rose-100 text-rose-600"
                        : "bg-amber-100 text-amber-600"
                    }`}>
                      {item.impact === "orphaned" ? "⚠ 孤立" : "🔒 将锁定"}
                    </span>
                  </div>
                ))}
              </div>

              {/* Cascade option hint */}
              {undoConfirm.orphaned_count > 0 && (
                <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
                  <div className="flex items-start gap-2">
                    <svg className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 16v-4M12 8h.01" strokeLinecap="round" />
                    </svg>
                    <div className="text-xs text-indigo-700">
                      <b>推荐：</b>使用「级联撤回」将自动重置上述已完成节点，避免数据一致性问题。使用「仅撤回」将保留这些节点但可能导致前置条件不一致。
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="px-6 pb-6 pt-3 flex items-center gap-3">
              <button
                onClick={cancelUndoConfirm}
                className="btn-ghost text-sm px-4 py-2 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={() => confirmUndo(false)}
                disabled={resetting}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium border-2 border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                仅撤回 (不处理依赖)
              </button>
              {undoConfirm.orphaned_count > 0 && (
                <button
                  onClick={() => confirmUndo(true)}
                  disabled={resetting}
                  className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50"
                >
                  级联撤回 (推荐)
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Reset Local Data Confirmation Dialog */}
      {resetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface-overlay animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden animate-slide-up">
            <div className="px-6 pt-6 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-2 14a2 2 0 01-2 2H9a2 2 0 01-2-2L5 6" />
                    <path d="M10 11v6M14 11v6" />
                    <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-800">
                    {lang === "zh-CN" ? "确认重置所有本地数据？" : "Reset all local data?"}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {lang === "zh-CN"
                      ? "清除所有学习进度和缓存，不可撤销"
                      : "Clear all progress & caches — irreversible"}
                  </p>
                </div>
              </div>
            </div>
            <div className="px-6 py-5">
              <div className="space-y-3 mb-2">
                <div className="flex items-start gap-3 p-3 bg-rose-50 border border-rose-100 rounded-xl">
                  <div className="w-2 h-2 mt-1.5 rounded-full bg-rose-400 shrink-0" />
                  <div>
                    <div className="text-sm font-semibold text-rose-700">
                      {lang === "zh-CN" ? "将清除以下内容" : "The following will be erased"}
                    </div>
                    <ul className="mt-1 text-xs text-rose-600/90 space-y-0.5 list-disc list-inside">
                      <li>{lang === "zh-CN" ? "所有图谱的学习进度" : "Learning progress for ALL graphs"}</li>
                      <li>{lang === "zh-CN" ? "新手教程已完成标志（重新打开会触发引导）" : "Onboarding completion flag — tutorial re-triggers on reload"}</li>
                      <li>{lang === "zh-CN" ? "节点/边的本地缓存" : "Cached graph nodes and edges"}</li>
                    </ul>
                  </div>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed pl-1">
                  {lang === "zh-CN"
                    ? "💡 提示：如果只想重新播放新手教程而不清除进度，请关闭此对话框，点击右上角菜单选择「重新播放新手教程」。"
                    : "💡 Tip: To re-play the tutorial without erasing progress, close this and use 「⋯」 menu → Replay Onboarding Tutorial."}
                </p>
              </div>
            </div>
            <div className="px-6 pb-6 pt-2 flex items-center gap-3">
              <button
                onClick={() => setResetConfirm(false)}
                disabled={resetting}
                className="btn-ghost text-sm px-4 py-2 rounded-lg"
              >
                {lang === "zh-CN" ? "取消" : "Cancel"}
              </button>
              <button
                onClick={doResetLocalData}
                disabled={resetting}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50 inline-flex items-center justify-center gap-2"
              >
                {resetting ? (
                  <>
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="2" opacity="0.2"/><path d="M1 8a7 7 0 017-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                    {lang === "zh-CN" ? "正在重置..." : "Resetting..."}
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="2 3 4 3 12 3" /><path d="M11 3l-1 10a1 1 0 01-1 1H5a1 1 0 01-1-1L3 3" /></svg>
                    {lang === "zh-CN" ? "确认重置所有数据" : "Reset Everything"}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Graph Reset Confirmation Dialog */}
      {graphResetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-surface-overlay animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden animate-slide-up">
            <div className="px-6 pt-6 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-800">清空当前图谱进度？</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    将重置 <b className="text-slate-700">{graphInfo?.name || activeGraph}</b> 的所有学习进度，不影响其他图谱
                  </p>
                </div>
              </div>
            </div>
            <div className="px-6 py-4">
              <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
                <div className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-xs text-amber-700">
                    已完成 <b>{completedCount}</b> 个节点的进度将被清空。此操作不可撤销。
                  </div>
                </div>
              </div>
            </div>
            <div className="px-6 pb-6 pt-3 flex items-center gap-3">
              <button
                onClick={() => setGraphResetConfirm(false)}
                className="btn-ghost text-sm px-4 py-2 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={doResetGraph}
                disabled={resetting}
                className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-rose-600 text-white hover:bg-rose-700 transition-colors disabled:opacity-50 inline-flex items-center justify-center gap-2"
              >
                {resetting ? (
                  <>
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="2" opacity="0.2"/><path d="M1 8a7 7 0 017-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                    正在清空...
                  </>
                ) : (
                  "确认清空"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── HEADER ── */}
      <header className="bg-white border-b border-slate-100 px-6 py-3 flex items-center justify-between sticky top-0 z-40 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-lg bg-primary-600 text-white flex items-center justify-center text-sm font-bold">
            L
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900 leading-tight">
              Learning<span className="text-primary-600">OS</span>
            </h1>
            <div className="flex items-center gap-4">
              <select
                value={activeGraph}
                onChange={(e) => loadGraph(e.target.value)}
                className="text-xs text-slate-400 bg-transparent border-none outline-none cursor-pointer hover:text-primary-600 max-w-[200px] truncate"
              >
                {graphPackages.map((pkg) => (
                  <option key={pkg.id} value={pkg.id}>
                    {pkg.name}
                  </option>
                ))}
              </select>
              {status && (
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1.5 font-medium text-slate-700">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    进度 {Math.round(status.percentage)}%
                  </span>
                  <span>已完成 <b className="text-slate-700">{status.completed}</b>/{status.total}</span>
                  <span>可学习 <b className="text-emerald-600">{status.available}</b></span>
                  <span>待解锁 <b className="text-slate-400">{status.locked}</b></span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* User stats */}
        <div className="flex items-center gap-3">
          {/* Language toggle */}
          <button
            onClick={() => {
              const next: LangCode = lang === "zh-CN" ? "en-US" : "zh-CN";
              setLang(next);
            }}
            className="hidden sm:inline-flex text-[10px] px-2 py-1 rounded-md border border-slate-200 text-slate-500 hover:text-primary-600 hover:border-primary-300 transition-colors font-medium"
            title="切换语言 / Switch language"
          >
            {lang === "zh-CN" ? "🌐 EN" : "🌐 中文"}
          </button>

          {/* Menu dropdown for advanced actions */}
          <details className="relative">
            <summary className="list-none cursor-pointer w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center text-slate-400 hover:text-primary-600 hover:border-primary-300 transition-colors">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="7" cy="2.5" r="1" /><circle cx="7" cy="7" r="1" /><circle cx="7" cy="11.5" r="1" />
              </svg>
            </summary>
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-2xl border border-slate-100 z-50 overflow-hidden animate-slide-up">
              <button
                onClick={(e) => { (e.currentTarget.closest("details") as any).open = false; triggerOnboarding(); }}
                className="w-full text-left px-4 py-2.5 text-xs text-slate-600 hover:bg-slate-50 hover:text-primary-600 transition-colors flex items-center gap-2"
              >
                <span>🎓</span>
                {lang === "zh-CN" ? "重新播放新手教程" : "Replay Onboarding Tutorial"}
              </button>
              <div className="border-t border-slate-100" />
              <button
                onClick={(e) => { (e.currentTarget.closest("details") as any).open = false; setResetConfirm(true); }}
                className="w-full text-left px-4 py-2.5 text-xs text-rose-600 hover:bg-rose-50 transition-colors flex items-center gap-2"
              >
                <span>🗑️</span>
                {lang === "zh-CN" ? "重置所有本地数据" : "Reset All Local Data"}
              </button>
            </div>
          </details>

          {xp && (
            <div className="hidden sm:flex items-center gap-2" title="经验值与等级">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200">
                <div className="text-amber-500">
                  <Icon.star />
                </div>
                <span className="text-xs font-bold text-amber-700">
                  全局 Lv.{xp.global_level ?? xp.level}
                </span>
              </div>
              <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-400 rounded-full transition-all duration-500"
                  style={{ width: `${xpPercent}%` }}
                />
              </div>
              <span className="text-xs font-medium text-slate-500 tabular-nums">
                {xp.total_xp} XP
              </span>
              {xp.global_xp !== undefined && (
                <span className="hidden lg:inline text-[10px] text-slate-400" title="跨图谱全局经验">
                  (全局 {xp.global_xp})
                </span>
              )}
            </div>
          )}

          {achievements && (
            <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-400">
              <div className="text-primary-400">
                <Icon.trophy />
              </div>
              <span className="font-medium text-slate-600">{earnedCount}</span>
              <span>/</span>
              <span>{totalAch}</span>
            </div>
          )}
          {/* Proficiency overview — show highest proficiency among completed nodes */}
          {allNodes.length > 0 && (
            <div className="hidden md:flex items-center gap-1.5">
              {(() => {
                const completedNodes = allNodes.filter((n) => n.score > 0 && (n.status === "COMPLETED" || n.status === "MASTERED"));
                if (completedNodes.length === 0) return null;
                const proficiencyCounts: Record<string, number> = {};
                completedNodes.forEach((n) => {
                  const label = n.proficiency?.label_en || "Completed";
                  proficiencyCounts[label] = (proficiencyCounts[label] || 0) + 1;
                });
                return (
                  <div className="flex items-center gap-1" title={Object.entries(proficiencyCounts).map(([k, v]) => `${k}: ${v}`).join(", ")}>
                    {Object.entries(proficiencyCounts).sort((a, b) => b[1] - a[1]).slice(0,3).map(([label, count]) => (
                      <span key={label} className="flex items-center gap-0.5 text-[10px]">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PROFICIENCY_COLORS[label] || "#94a3b8" }} />
                        <span className="text-slate-400">{count}</span>
                      </span>
                    ))}
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      </header>

      {/* ── STATUS BAR ── */}
      {status && (
        <div className="bg-white border-b border-slate-100 px-6 py-2 flex items-center text-xs text-slate-500 overflow-x-auto">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setGraphResetConfirm(true)}
              className="text-xs text-rose-400 hover:text-rose-600 font-medium"
              title="清空当前图谱的所有学习进度"
            >
              ⟳ 清空进度
            </button>
            <button
              onClick={async () => {
                try {
                  const res = await fetch(`${getApiUrl()}/graphs/packages`);
                  const data = await res.json();
                  if (data?.packages?.length) setGraphPackages(data.packages);
                  addToast("图谱列表已刷新", "success");
                } catch (e: any) {
                  addToast("刷新失败: " + e.message, "error");
                }
              }}
              className="text-xs text-slate-400 hover:text-primary-500 font-medium"
              title="重新扫描graphs/目录获取最新图谱"
            >
              ⟳ 刷新图谱
            </button>
            <a href="/graph-generator" className="text-xs text-primary-500 hover:text-primary-700 font-medium">
              + 创建图谱
            </a>
          </div>
          <div className="flex-1 flex justify-center">
            {recommendations.length > 0 && (
              <span className="flex items-center gap-1 text-primary-500">
                <Icon.lightBulb />
                推荐:{" "}
                {recommendations.slice(0, 3).map((id: string, i: number) => (
                  <button
                    key={id}
                    onClick={() => viewNode(id)}
                    className="font-semibold hover:underline"
                  >
                    {titleMap.get(id) || id}
                    {i < Math.min(2, recommendations.length - 1) ? "," : ""}
                  </button>
                ))}
              </span>
            )}
          </div>
          <span className="flex items-center gap-2">
            <button
              onClick={() => {
                if ((window as any).electronAPI?.openDevTools) {
                  (window as any).electronAPI.openDevTools();
                } else {
                  console.log('DevTools: Press F12 or Ctrl+Shift+I to open');
                  addToast('已打开开发者工具（F12）', 'info');
                }
              }}
              className="text-xs text-slate-400 hover:text-slate-600 font-medium"
              title="打开开发者工具"
            >
              🔧 DevTools
            </button>
            <button onClick={exportProgress} className="text-xs text-slate-400 hover:text-slate-600">
              导出进度
            </button>
            <button onClick={importProgress} className="text-xs text-slate-400 hover:text-slate-600">
              导入进度
            </button>
            <button
              onClick={() => setShowLearningRecord(true)}
              className="flex items-center gap-1 text-xs text-primary-500 hover:text-primary-700 font-medium"
              title="查看学习记录热力图和近期活动"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="hidden sm:inline">学习记录</span>
            </button>
            <button onClick={exportPrompt} className="text-xs text-primary-500 hover:text-primary-700 font-medium">
              导出提示词
            </button>
          </span>
        </div>
      )}

      {/* ── MAIN CONTENT ── */}
      <div className="flex-1 flex gap-4 p-4 max-w-7xl w-full mx-auto h-[calc(100vh-100px)]">
        {/* ═══ LEFT: Node List ═══ */}
        <aside className="w-72 flex-shrink-0 flex flex-col gap-3">
          <div className="panel p-4 flex-1 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold text-slate-700 flex items-center gap-2">
                <Icon.target />
                {viewMode === "list" ? (showCompleted ? "节点列表" : "可用节点") : "技能树视图"}
              </h2>
              <div className="flex items-center gap-1">
                {viewMode === "list" && (
                  <button
                    onClick={() => setShowCompleted((v) => !v)}
                    title={showCompleted ? "仅显示可用节点" : "显示已完成节点以便复习"}
                    className={`text-[10px] px-2 py-0.5 rounded-md font-medium mr-1 transition-all
                      ${showCompleted
                        ? "bg-violet-100 text-violet-700"
                        : "text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                      }`}
                  >
                    复习模式 {showCompleted ? `ON (${completedCount})` : "OFF"}
                  </button>
                )}
                <button
                  onClick={() => setViewMode("list")}
                  className={`text-[10px] px-2 py-0.5 rounded-md font-medium ${
                    viewMode === "list"
                      ? "bg-primary-100 text-primary-700"
                      : "text-slate-400 hover:text-slate-600"
                  }`}
                >
                  列表
                </button>
                <button
                  onClick={() => setViewMode("tree")}
                  className={`text-[10px] px-2 py-0.5 rounded-md font-medium ${
                    viewMode === "tree"
                      ? "bg-primary-100 text-primary-700"
                      : "text-slate-400 hover:text-slate-600"
                  }`}
                >
                  技能树
                </button>
              </div>
            </div>

            {/* Search bar */}
            <div className="relative mb-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => doSearch(e.target.value)}
                placeholder="搜索节点..."
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs
                  bg-white text-slate-700 placeholder:text-slate-300
                  focus:outline-none focus:ring-2 focus:ring-primary-200 focus:border-primary-300"
              />
              {searchOpen && searchResults.length > 0 && (
                <div className="absolute top-full mt-1 left-0 right-0 z-50 bg-white border border-slate-200 rounded-xl shadow-lg max-h-64 overflow-auto scrollbar-thin">
                  {searchResults.map((r) => (
                    <div
                      key={r.id}
                      className="border-b border-slate-50 last:border-0 group hover:bg-slate-50"
                    >
                      <div className="flex items-center gap-1 px-3 py-2">
                        <button
                          onClick={() => {
                            viewNode(r.id);
                            setSearchOpen(false);
                            setSearchQuery("");
                          }}
                          className="flex-1 text-left min-w-0"
                        >
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-medium text-slate-700 truncate">{r.title}</span>
                            {r.match !== "title" && (
                              <span className="text-[10px] text-slate-400 shrink-0">描述匹配</span>
                            )}
                            <span className={`ml-auto shrink-0 text-[10px] px-1.5 py-0 rounded font-medium ${STATUS_META[r.status]?.cls || ""}`}>
                              {STATUS_META[r.status]?.label || r.status}
                            </span>
                          </div>
                        </button>
                        <button
                          onClick={() => {
                            startTaskMode(r.id);
                            setSearchOpen(false);
                            setSearchQuery("");
                          }}
                          className={`shrink-0 px-2 py-1 rounded-md text-[10px] font-semibold transition-all inline-flex items-center gap-1
                            ${taskTarget === r.id
                              ? "bg-primary-100 text-primary-700"
                              : "text-primary-500 hover:bg-primary-50 opacity-0 group-hover:opacity-100"
                            }`}
                          title="设定为学习目标，激活任务模式"
                        >
                          {taskTarget === r.id ? (
                            <>✓ 当前目标</>
                          ) : (
                            <>🎯 任务模式</>
                          )}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Task mode banner */}
            {taskTarget && (
              <div className="mb-3 p-3 rounded-xl bg-primary-50 border border-primary-100">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-primary-700">任务模式</span>
                  <button onClick={clearTaskMode} className="text-[10px] text-primary-400 hover:text-primary-600">
                    退出
                  </button>
                </div>
                <p className="text-[10px] text-primary-500 mb-1">
                  目标: {titleMap.get(taskTarget) || taskTarget}
                </p>
                <div className="flex items-center gap-1 flex-wrap">
                  {taskPath.map((n, i) => (
                    <span key={n.id} className="flex items-center gap-0.5">
                      <button
                        onClick={() => viewNode(n.id)}
                        className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium ${
                          n.status === "COMPLETED" || n.status === "MASTERED"
                            ? "bg-emerald-100 text-emerald-600"
                            : n.status === "AVAILABLE"
                            ? "bg-primary-100 text-primary-600"
                            : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {i + 1}. {n.title.length > 8 ? n.title.slice(0, 8) + "..." : n.title}
                      </button>
                      {i < taskPath.length - 1 && (
                        <span className="text-slate-300 text-[10px]">→</span>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Filter tabs */}
            <div className="flex gap-1 mb-3 bg-slate-50 rounded-lg p-1">
              {["all", "beginner", "intermediate", "advanced"].map((f) => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-all ${
                    activeFilter === f
                      ? "bg-white text-slate-800 shadow-sm"
                      : "text-slate-400 hover:text-slate-600"
                  }`}
                >
                  {f === "all" ? "全部" : f === "beginner" ? "入门" : f === "intermediate" ? "进阶" : "高级"}
                </button>
              ))}
            </div>

            {/* Node list */}
            <div className="flex-1 overflow-auto scrollbar-thin -mx-1 px-1">
              {filteredNodeIds.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs">
                  <div className="mb-2 opacity-40"><Icon.check /></div>
                  本组节点全部完成
                </div>
              ) : (
                <div className="space-y-1">
                  {filteredNodeIds.map((nodeId, i) => {
                    const nodeDetail = detailMap.get(nodeId);
                    const diff = nodeDetail?.difficulty || "";
                    const diffMeta = DIFF_META[diff];
                    const isInPath = taskPath.some((n) => n.id === nodeId);
                    const isDone = nodeDetail?.status === "COMPLETED" || nodeDetail?.status === "MASTERED";
                    const isMastered = nodeDetail?.status === "MASTERED";
                    return (
                      <button
                        key={nodeId}
                        onClick={() => viewNode(nodeId)}
                        className={`w-full text-left px-3 py-2.5 rounded-xl flex items-center gap-2.5 transition-all
                          ${
                            selectedNode?.id === nodeId
                              ? "bg-primary-50 ring-2 ring-primary-200"
                              : isInPath
                              ? "bg-primary-50/50 ring-1 ring-primary-100"
                              : isDone
                              ? "bg-slate-50/60 hover:bg-slate-50"
                              : "hover:bg-slate-50"
                          }
                          animate-fade-in`}
                        style={{ animationDelay: `${i * 20}ms` }}
                      >
                        {/* Tier badge */}
                        {isDone && nodeDetail?.proficiency ? (
                          <div
                            className="w-8 h-8 rounded-lg text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                            style={{ backgroundColor: nodeDetail.proficiency.color }}
                          >
                            {nodeDetail.proficiency.icon}
                          </div>
                        ) : isMastered ? (
                          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0 shadow-sm shadow-violet-200">
                            ★
                          </div>
                        ) : isDone ? (
                          <div className="w-8 h-8 rounded-lg bg-emerald-500 text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                            ✓
                          </div>
                        ) : (
                          <NodeIdTag id={nodeId} />
                        )}

                        {/* Label */}
                        <div className="flex-1 min-w-0">
                          <p className={`text-xs font-medium truncate ${isDone ? "text-slate-500 line-through/30" : "text-slate-700"}`}>
                            {titleMap.get(nodeId) || nodeId}
                          </p>
                          <div className="flex items-center gap-1.5 flex-wrap mt-0.5">
                            {diffMeta && (
                              <span className={`inline-block text-[10px] px-1.5 py-0 rounded-full ${diffMeta.color}`}>
                                {diffMeta.label}
                              </span>
                            )}
                            {isMastered && (
                              <span className="inline-block text-[10px] px-1.5 py-0 rounded-full bg-violet-100 text-violet-600 font-semibold">
                                ★ MASTERED
                              </span>
                            )}
                            {isDone && !isMastered && (
                              <span className="inline-block text-[10px] px-1.5 py-0 rounded-full bg-emerald-100 text-emerald-600">
                                ✓ 已完成 · {nodeDetail?.score || 0}/80
                              </span>
                            )}
                          </div>
                        </div>
                        {isInPath && (
                          <span className="text-[10px] text-primary-400 flex-shrink-0">
                            {taskPath.findIndex((n) => n.id === nodeId) + 1}步
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Undo Timeline */}
          <div className="panel p-4">
            <button
              onClick={() => setShowUndoPanel(!showUndoPanel)}
              className="w-full flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider"
            >
              <span className="flex items-center gap-2">
                <Icon.undo />
                操作历史
                {undoStack && undoStack.count > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-600 text-[10px]">
                    {undoStack.count}
                  </span>
                )}
              </span>
              <svg
                className={`w-4 h-4 transition-transform ${showUndoPanel ? "rotate-180" : ""}`}
                fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Label for unlimited undo */}
            {undoStack && undoStack.unlimited && (
              <p className="text-[10px] text-slate-400 mt-1">无限制撤回</p>
            )}

            {showUndoPanel && (
              <div className="mt-3 space-y-1 max-h-60 overflow-auto scrollbar-thin">
                {(!undoStack || undoStack.count === 0) ? (
                  <p className="text-xs text-slate-400 text-center py-2">
                    暂无操作记录
                  </p>
                ) : (
                  <>
                    {/* Quick single-step undo button */}
                    <button
                      onClick={undoLastAction}
                      disabled={resetting}
                      className="w-full mb-2 px-3 py-2 rounded-xl text-xs font-semibold
                        bg-primary-600 text-white hover:bg-primary-700
                        shadow-sm shadow-primary-200
                        transition-all duration-150 disabled:opacity-50
                        inline-flex items-center justify-center gap-1.5"
                    >
                      <Icon.undo />
                      撤回最近一步（#{undoStack?.entries?.[0]?.index ?? 0}）
                    </button>

                    <div className="text-[10px] text-slate-400 mb-1 flex items-center gap-1 px-1">
                      <span>点击节点标题查看详情，点击 ↩ 撤回该步之后的所有操作</span>
                    </div>

                    {undoStack.entries.slice(0, 20).map((entry: any) => {
                      const title = titleMap.get(entry.node_id) || entry.node_id;
                      const stepsFromTop = (undoStack?.entries?.[0]?.index ?? 0) - entry.index + 1;
                      return (
                        <div
                          key={entry.index}
                          className="px-2 py-1.5 rounded-lg bg-slate-50 text-[10px] text-slate-500 flex items-center gap-1.5 group hover:bg-slate-100 transition-colors"
                        >
                          <span className="w-4 h-4 rounded bg-slate-300 text-white flex items-center justify-center text-[8px] font-bold flex-shrink-0">
                            {entry.index}
                          </span>
                          <button
                            onClick={() => viewNode(entry.node_id)}
                            className="flex-1 min-w-0 text-left truncate hover:text-primary-600 hover:underline"
                            title={title}
                          >
                            <span className="truncate">{title}</span>
                          </button>
                          <span className="text-slate-400 flex-shrink-0 tabular-nums">
                            {entry.timestamp?.slice(11, 16) || ""}
                          </span>
                          <button
                            onClick={() => undoMultiple(stepsFromTop)}
                            disabled={resetting}
                            className="w-6 h-6 rounded-md flex items-center justify-center
                              text-slate-400 hover:text-rose-600 hover:bg-rose-50
                              disabled:opacity-40 transition-all opacity-60 group-hover:opacity-100"
                            title={`撤回该步骤（以及之后的 ${stepsFromTop - 1} 步新操作）`}
                          >
                            ↩
                          </button>
                        </div>
                      );
                    })}
                    {undoStack.count > 1 && (
                      <div className="pt-1 mt-1 border-t border-slate-100 space-y-1">
                        <button
                          onClick={() => undoMultiple(Math.min(undoStack.count, 3))}
                          disabled={resetting}
                          className="w-full px-3 py-1.5 rounded-lg text-xs font-medium
                            bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200
                            transition-all duration-150 disabled:opacity-50"
                        >
                          撤回最近 {Math.min(undoStack.count, 3)} 步
                        </button>
                        {undoStack.count > 3 && (
                          <button
                            onClick={() => undoMultiple(Math.min(undoStack.count, 10))}
                            disabled={resetting}
                            className="w-full px-3 py-1.5 rounded-lg text-xs font-medium
                              text-rose-500 hover:bg-rose-50 border border-rose-100
                              transition-all duration-150 disabled:opacity-50"
                          >
                            批量撤回最近 {Math.min(undoStack.count, 10)} 步
                          </button>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </aside>

        {/* ═══ CENTER: Detail panel / Skill Tree ═══ */}
        <main className="flex-1 min-w-0">
          {viewMode === "tree" ? (
            /* Tree / skill-tree view */
            <SkillTree
              nodes={allNodes}
              edges={edges}
              selectedId={selectedNode?.id || null}
              onSelect={(id) => viewNode(id)}
              onSetTaskTarget={(id) => startTaskMode(id)}
              taskTargetId={taskTarget}
              taskPath={taskPath}
              nodeDetails={Object.fromEntries(
                allNodes.map((n) => [n.id, { title: n.title, description: n.description }])
              )}
            />
          ) : selectedNode ? (
            <div className="panel p-6 h-full overflow-auto animate-slide-up">
              {/* Back button */}
              <button
                onClick={() => setSelectedNode(null)}
                className="btn-ghost mb-4 -ml-2 flex items-center gap-1"
              >
                <Icon.arrowLeft />
                返回列表
              </button>

              {/* Title */}
              <h2 className="text-xl font-bold text-slate-900 mb-2">
                {selectedNode.title}
              </h2>

              {/* Badges */}
              <div className="flex items-center gap-2 mb-4 flex-wrap">
                {selectedNode.difficulty &&
                  DIFF_META[selectedNode.difficulty] && (
                    <span
                      className={`status-badge ${DIFF_META[selectedNode.difficulty].color}`}
                    >
                      {DIFF_META[selectedNode.difficulty].icon}{" "}
                      {DIFF_META[selectedNode.difficulty].label}
                    </span>
                  )}
                {selectedNode.type &&
                  TYPE_META[selectedNode.type] && (
                    <span className="status-badge bg-slate-100 text-slate-600">
                      {TYPE_META[selectedNode.type]}
                    </span>
                  )}
                {selectedNode.status &&
                  STATUS_META[selectedNode.status] && (
                    <span className={`status-badge ${STATUS_META[selectedNode.status].cls}`}>
                      {STATUS_META[selectedNode.status].label}
                    </span>
                  )}
                {/* Node ID tag */}
                <span className="status-badge bg-slate-100 text-slate-400 font-mono text-[10px]">
                  {selectedNode.id}
                </span>
                {/* Task mode button */}
                <button
                  onClick={() => startTaskMode(selectedNode.id)}
                  className={`status-badge text-[10px] font-medium cursor-pointer ${
                    taskTarget === selectedNode.id
                      ? "bg-primary-100 text-primary-700"
                      : "bg-slate-100 text-slate-400 hover:text-primary-500"
                  }`}
                >
                  {taskTarget === selectedNode.id ? "已设为目标" : "设为学习目标"}
                </button>
              </div>

              {/* Description */}
              <div className="prose prose-sm max-w-none mb-6">
                <p className="text-slate-600 leading-relaxed whitespace-pre-line">
                  {selectedNode.description}
                </p>
              </div>

              {/* Current score */}
              {selectedNode.score > 0 && (
                <div className="flex items-center gap-2 mb-4 p-3 bg-slate-50 rounded-xl text-xs text-slate-500">
                  <span>累计评分:</span>
                  <span className={`font-bold ${selectedNode.score >= 80 ? "text-violet-600" : "text-slate-700"}`}>
                    {selectedNode.score}
                  </span>
                  {selectedNode.proficiency && (
                    <span
                      className="px-1.5 py-0.5 rounded-md text-[10px] font-bold text-white"
                      style={{ backgroundColor: selectedNode.proficiency.color }}
                    >
                      {selectedNode.proficiency.label_en}
                    </span>
                  )}
                  {selectedNode.score >= 80 && isMastered ? (
                    <span className="ml-1 px-1.5 py-0.5 rounded-md bg-violet-100 text-violet-700 text-[10px] font-bold">
                      MASTERED
                    </span>
                  ) : selectedNode.score >= 80 && isCompleted ? (
                    <span className="ml-1 px-1.5 py-0.5 rounded-md bg-violet-50 text-violet-500 text-[10px] font-medium">
                      ≥80 (已达精通线)
                    </span>
                  ) : (
                    <span className="ml-1 text-slate-400">
                      / 80 (精通线)
                    </span>
                  )}
                  <div className="flex gap-0.5 ml-1">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <div
                        key={n}
                        className={`w-2 h-3 rounded-sm ${
                          n <= Math.ceil(selectedNode.score / 16)
                            ? "bg-amber-400"
                            : "bg-slate-200"
                        }`}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Resources */}
              {selectedNode.resources.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-bold text-slate-500 mb-3 flex items-center gap-1.5">
                    <Icon.link />
                    学习资源
                  </h3>
                  <div className="space-y-2">
                    {selectedNode.resources.map((r, i) => (
                      <a
                        key={i}
                        href={r.uri}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-50 hover:bg-primary-50 hover:text-primary-700 transition-colors group"
                      >
                        <span className="text-xs font-mono font-bold text-slate-400 bg-white px-2 py-0.5 rounded-md border border-slate-200">
                          {r.type}
                        </span>
                        <span className="text-sm font-medium flex-1 group-hover:text-primary-600">
                          {r.label || r.uri}
                        </span>
                        <span className="text-slate-300 group-hover:text-primary-400 transition-transform group-hover:translate-x-0.5">
                          <Icon.arrowRight />
                        </span>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Action buttons */}
              <div className="border-t border-slate-100 pt-4 mt-4">
                {/* Learning record section — for all nodes */}
                <div>
                  <p className="text-xs text-slate-400 mb-3 font-medium">
                    {isCompleted
                      ? isMastered
                        ? "此节点已精通！继续添加学习记录以巩固。"
                        : "此节点已完成。通过自评为节点积累分数，达到80分自动晋升为 MASTERED。"
                      : "记录你的学习进度，每次记录都会积累分数。"}
                  </p>

                  {/* Score warning */}
                  <div className="flex items-center gap-1.5 mb-3 text-slate-400 text-xs italic">
                    <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 16v-4M12 8h.01" strokeLinecap="round" />
                    </svg>
                    学贵有恒，勿以虚分自欺。
                  </div>

                  {/* Custom self-assessment input — customizable description + score */}
                  <div className="border-2 border-dashed border-violet-200 bg-violet-50/40 rounded-xl p-3 mb-3 space-y-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-bold text-violet-600 flex items-center gap-1">
                        ✨ 学习记录
                      </span>
                      <span className="text-[10px] text-violet-500/80">
                        输入事项 → 选择分数 → 记录
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={scoreDesc}
                        onChange={(e) => setScoreDesc(e.target.value)}
                        placeholder="做了什么？（如：阅读论文、代码实践、视频学习...）"
                        className="flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white
                          text-slate-700 placeholder:text-slate-300
                          focus:outline-none focus:ring-2 focus:ring-violet-200 focus:border-violet-300"
                        disabled={scoring}
                      />
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] text-slate-400">分数:</span>
                      {[1, 3, 5, 10, 20, 30].map((s) => (
                        <button
                          key={s}
                          onClick={() => setCustomScore(s)}
                          className={`w-9 h-7 rounded-md text-[11px] font-bold tabular-nums transition-all
                            ${customScore === s
                              ? "bg-violet-600 text-white shadow-sm shadow-violet-200"
                              : "bg-white text-slate-500 border border-slate-200 hover:border-violet-300 hover:text-violet-600"
                              }`}
                        >
                          +{s}
                        </button>
                      ))}
                      <input
                        type="number"
                        min={1}
                        max={99}
                        value={customScore}
                        onChange={(e) => {
                          const v = e.target.value;
                          if (v === "") setCustomScore("");
                          else {
                            const n = parseInt(v, 10);
                            if (!isNaN(n)) setCustomScore(Math.max(1, Math.min(99, n)));
                          }
                        }}
                        className="w-16 h-7 rounded-md border border-slate-200 bg-white
                          text-slate-600 text-center text-[11px] font-bold tabular-nums
                          focus:outline-none focus:ring-2 focus:ring-violet-200 focus:border-violet-300"
                        placeholder="自定义"
                      />
                      <button
                        onClick={() => {
                          const desc = scoreDesc.trim() || (typeof customScore === "number" ? `学习记录 (+${customScore})` : "");
                          const s = typeof customScore === "number" ? customScore : 5;
                          if (desc) addScore(selectedNode.id, s, desc);
                        }}
                        disabled={scoring || (!scoreDesc.trim() && customScore === "")}
                        className="ml-auto px-4 py-1.5 rounded-lg text-xs font-semibold
                          bg-violet-600 text-white hover:bg-violet-700 shadow-sm shadow-violet-200
                          transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed
                          inline-flex items-center gap-1.5"
                      >
                        {scoring ? (
                          <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                        ) : (
                          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                            <polyline points="2 6 5 9 10 3" />
                          </svg>
                        )}
                        记录
                        {typeof customScore === "number" ? (
                          <span className="opacity-90 font-bold">+{customScore}</span>
                        ) : ""}
                      </button>
                    </div>
                  </div>

                  {/* Quick preset buttons */}
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {SCORE_PRESETS.map((preset) => (
                      <button
                        key={preset.label}
                        onClick={() => addScore(selectedNode.id, preset.score, preset.label)}
                        disabled={scoring}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium
                          bg-white border border-slate-200 text-slate-600
                          hover:border-violet-300 hover:text-violet-600 hover:bg-violet-50
                          transition-all duration-150 disabled:opacity-50"
                      >
                        {preset.label} (+{preset.score})
                      </button>
                    ))}
                  </div>

                  {/* Undo button */}
                  <button
                    onClick={() => undoLastAction()}
                    disabled={resetting}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm
                      bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200
                      transition-all duration-150 disabled:opacity-50"
                  >
                    {resetting ? (
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : (
                      <Icon.undo />
                    )}
                    撤销上一步 (恢复之前状态)
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Empty state */
            <div className="panel h-full flex items-center justify-center">
              <div className="text-center animate-fade-in">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100 text-slate-300 mb-4">
                  <Icon.target />
                </div>
                <h3 className="text-lg font-semibold text-slate-400 mb-1">
                  选择一个节点
                </h3>
                <p className="text-sm text-slate-300">
                  从左侧列表中点击任意节点查看详情
                </p>
                {availableNodes.length === 0 && status && status.completed > 0 && (
                  <div className="mt-6 px-4 py-3 rounded-xl bg-emerald-50 text-emerald-700 text-sm font-medium animate-bounce-in">
                    所有可用节点已完成！
                  </div>
                )}
              </div>
            </div>
          )}
        </main>

        {/* ═══ RIGHT: Stats & Achievements ═══ */}
        <aside className="w-72 flex-shrink-0 flex flex-col gap-3 hidden lg:flex">
          {/* Quick stats */}
          <div className="panel p-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              我的进度
            </h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500">完成率</span>
                  <span className="font-bold text-slate-700">
                    {status ? Math.round(status.percentage) : 0}%
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-400 rounded-full transition-all duration-700"
                    style={{
                      width: `${status ? Math.round(status.percentage) : 0}%`,
                    }}
                  />
                </div>
              </div>
              {xp && (
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500">
                      等级 {xp.global_level ?? xp.level} 进度
                    </span>
                    <span className="font-bold text-amber-600">
                      {xpPercent}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-400 rounded-full transition-all duration-700"
                      style={{ width: `${xpPercent}%` }}
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    还需 {xp.xp_to_next_level} XP 升至 Lv.{(xp.global_level ?? xp.level) + 1}
                    {xp.global_xp !== undefined && (
                      <span className="ml-1"> · 当前图谱 {xp.total_xp} XP</span>
                    )}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Achievements — compact icon grid with hover tooltips */}
          <div className="panel p-4 flex-1 overflow-visible min-h-0 relative">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Icon.trophy />
              成就 ({earnedCount}/{totalAch})
            </h3>
            <div className="overflow-y-auto max-h-[calc(100%-2rem)]">
            {achievements.earned.length === 0 && achievements.locked.length === 0 && (
              <p className="text-xs text-slate-400 text-center py-4">加载中...</p>
            )}
            {/* Earned achievements — icon grid */}
            {achievements.earned.length > 0 && (
              <div className="mb-3">
                <p className="text-[10px] text-slate-400 mb-2">已获得</p>
                <div className="flex flex-wrap gap-1.5">
                  {achievements.earned.map((a) => (
                    <div key={a.id} className="relative group">
                      <div className="w-8 h-8 rounded-lg bg-emerald-100 border border-emerald-200 flex items-center justify-center text-sm cursor-default transition-transform hover:scale-110">
                        {a.icon || "⭐"}
                      </div>
                      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 px-2.5 py-1.5 rounded-lg bg-slate-800 text-white text-[10px] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-lg">
                        <p className="font-semibold">{a.name}</p>
                        <p className="text-slate-300 mt-0.5">{a.description}</p>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 -mb-0.5 w-2 h-2 bg-slate-800 rotate-45" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* Locked achievements — icon grid */}
            {achievements.locked.length > 0 && (
              <div>
                <p className="text-[10px] text-slate-400 mb-2">未解锁</p>
                <div className="flex flex-wrap gap-1.5">
                  {achievements.locked.map((a) => (
                    <div key={a.id} className="relative group">
                      <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-sm opacity-40 cursor-default transition-transform hover:scale-110 hover:opacity-60">
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                      </div>
                      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-1 px-2.5 py-1.5 rounded-lg bg-slate-800 text-white text-[10px] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-lg">
                        <p className="font-semibold">{a.name}</p>
                        <p className="text-slate-300 mt-0.5">{a.description}</p>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 -mb-0.5 w-2 h-2 bg-slate-800 rotate-45" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            </div>
          </div>
        </aside>
      </div>

      {/* Learning Record Modal */}
      {showLearningRecord && (
        <LearningRecord
          apiUrl={getApiUrl()}
          onClose={() => setShowLearningRecord(false)}
        />
      )}

      {/* Share Modal */}
      {showShareModal && shareData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-800">学习成果分享</h3>
              <button onClick={() => setShowShareModal(false)} className="text-slate-400 hover:text-slate-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="bg-amber-50 rounded-xl p-4 mb-4 border border-amber-200">
              <p className="text-sm font-semibold text-amber-800 mb-2">{shareData.package_name}</p>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <p className="text-2xl font-bold text-amber-600">{shareData.progress?.percentage ?? 0}%</p>
                  <p className="text-[10px] text-slate-400">完成度</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-600">{shareData.progress?.completed ?? 0}</p>
                  <p className="text-[10px] text-slate-400">已完成</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-600">Lv.{shareData.level}</p>
                  <p className="text-[10px] text-slate-400">等级 · {shareData.total_xp}XP</p>
                </div>
              </div>
              {shareData.earned_achievements?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-amber-200">
                  <p className="text-[10px] text-slate-400 mb-1">已获成就</p>
                  <div className="flex flex-wrap gap-1">
                    {shareData.earned_achievements.map((a: any, i: number) => (
                      <span key={i} className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">{a.icon} {a.name}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  const text = `我在 LearningOS 学习「${shareData.package_name}」\n完成度: ${shareData.progress?.percentage ?? 0}%\n等级: Lv.${shareData.level} (${shareData.total_xp}XP)\n成就: ${shareData.earned_achievements?.length ?? 0}个`;
                  navigator.clipboard.writeText(text).then(() => alert('已复制到剪贴板'));
                }}
                className="flex-1 px-4 py-2.5 rounded-xl font-medium text-sm bg-teal-500 text-white hover:bg-teal-600 transition-colors"
              >
                复制分享文本
              </button>
              <button
                onClick={() => setShowShareModal(false)}
                className="px-4 py-2.5 rounded-xl font-medium text-sm bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
