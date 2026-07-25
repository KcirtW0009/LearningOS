"use client";

import React, { useState, useEffect, useCallback } from "react";

type DailySummary = {
  date: string;
  nodes_completed: number;
  total_score: number;
};

type RecentActivity = {
  date: string;
  time: string;
  node_id: string;
  title: string;
  field: string;
  old_value: string;
  new_value: string;
  description?: string;
  timestamp: string;
};

type Streaks = {
  current: number;
  longest: number;
};

type LearningLogData = {
  daily_summary: DailySummary[];
  recent_activity: RecentActivity[];
  streaks: Streaks;
  total_days_active: number;
  total_nodes_completed: number;
  total_xp: number;
} | null;

type Props = {
  apiUrl: string;
  onClose: () => void;
};

export default function LearningRecord({ apiUrl, onClose }: Props) {
  const [data, setData] = useState<LearningLogData>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"heatmap" | "activity">("heatmap");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/learning-log`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Build heatmap data — last 12 weeks
  const buildHeatmap = () => {
    if (!data?.daily_summary) return [];
    const today = new Date();
    const weeks: { weekLabel: string; days: { date: string; count: number; level: number }[] }[] = [];

    // Build 12 weeks
    for (let w = 11; w >= 0; w--) {
      const weekStart = new Date(today);
      weekStart.setDate(today.getDate() - today.getDay() - w * 7);
      const days: { date: string; count: number; level: number }[] = [];
      for (let d = 0; d < 7; d++) {
        const day = new Date(weekStart);
        day.setDate(weekStart.getDate() + d);
        const dateStr = day.toISOString().slice(0, 10);
        const entry = data.daily_summary.find((s) => s.date === dateStr);
        const count = entry?.nodes_completed || 0;
        const level = count === 0 ? 0 : count <= 1 ? 1 : count <= 3 ? 2 : count <= 5 ? 3 : 4;
        days.push({ date: dateStr, count, level });
      }
      const mon = days[1]; // Monday
      const weekLabel = mon ? `${parseInt(mon.date.slice(5, 7))}/${parseInt(mon.date.slice(8, 10))}` : "";
      weeks.push({ weekLabel, days });
    }
    return weeks;
  };

  const heatmap = buildHeatmap();
  const heatLevels = ["bg-slate-100", "bg-emerald-200", "bg-emerald-400", "bg-emerald-500", "bg-emerald-600"];

  const activityLabel = (entry: RecentActivity) => {
    if (entry.field === "status" && (entry.new_value === "COMPLETED" || entry.new_value === "MASTERED")) {
      return entry.new_value === "MASTERED" ? "精通" : "完成";
    }
    if (entry.field === "score") {
      if (entry.description) return entry.description;
      return `评分 +${parseInt(entry.new_value) - parseInt(entry.old_value)}`;
    }
    if (entry.field === "undo") return "撤回";
    return entry.field;
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            学习记录
          </h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-slate-400">
              <p className="text-sm">加载失败: {error}</p>
              <button onClick={fetchData} className="mt-2 text-xs text-primary-500 hover:underline">重试</button>
            </div>
          ) : !data ? (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          ) : (
            <div className="space-y-6">
              {/* Stats cards */}
              <div className="grid grid-cols-4 gap-3">
                <div className="bg-slate-50 rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold text-slate-700">{data.total_nodes_completed}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">已完成节点</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold text-amber-600">{data.total_xp}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">累计经验</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold text-emerald-600">{data.streaks.current}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">连续天数</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold text-primary-500">{data.total_days_active}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">活跃天数</p>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
                <button
                  onClick={() => setTab("heatmap")}
                  className={`flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    tab === "heatmap" ? "bg-white text-slate-700 shadow-sm" : "text-slate-400 hover:text-slate-600"
                  }`}
                >
                  📅 学习热力图
                </button>
                <button
                  onClick={() => setTab("activity")}
                  className={`flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    tab === "activity" ? "bg-white text-slate-700 shadow-sm" : "text-slate-400 hover:text-slate-600"
                  }`}
                >
                  📋 近期活动
                </button>
              </div>

              {tab === "heatmap" && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-slate-500">过去 12 周学习热力图</p>
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] text-slate-400">少</span>
                      {heatLevels.map((cls, i) => (
                        <div key={i} className={`w-3 h-3 rounded-sm ${cls}`} />
                      ))}
                      <span className="text-[9px] text-slate-400">多</span>
                    </div>
                  </div>
                  <div className="flex gap-1 overflow-x-auto pb-2">
                    {heatmap.map((week, wi) => (
                      <div key={wi} className="flex flex-col gap-1">
                        {week.days.map((day) => (
                          <div
                            key={day.date}
                            className={`w-3.5 h-3.5 rounded-sm ${heatLevels[day.level]}`}
                            title={`${day.date}: ${day.count} 节点`}
                          />
                        ))}
                        <span className="text-[8px] text-slate-400 text-center mt-0.5">
                          {week.weekLabel}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {tab === "activity" && (
                <div className="space-y-1 max-h-80 overflow-auto">
                  {data.recent_activity.length === 0 ? (
                    <p className="text-xs text-slate-400 text-center py-4">暂无活动记录</p>
                  ) : (
                    data.recent_activity.map((entry, i) => (
                      <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors">
                        <div className="flex-shrink-0 text-[10px] text-slate-400 tabular-nums w-20">
                          <div>{entry.date.slice(5)}</div>
                          <div className="text-[9px]">{entry.time}</div>
                        </div>
                        <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                          entry.field === "status" ? "bg-emerald-500" :
                          entry.field === "score" ? "bg-amber-500" :
                          entry.field === "undo" ? "bg-rose-500" : "bg-slate-400"
                        }`} />
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-medium text-slate-700 truncate">{entry.title}</span>
                          {entry.description && entry.field === "score" && (
                            <div className="text-[10px] text-slate-400 truncate">{entry.description}</div>
                          )}
                        </div>
                        <span className={`text-[10px] flex-shrink-0 px-1.5 py-0.5 rounded-md font-medium ${
                          entry.field === "status" ? "bg-emerald-50 text-emerald-600" :
                          entry.field === "score" ? "bg-amber-50 text-amber-600" :
                          entry.field === "undo" ? "bg-rose-50 text-rose-600" : "bg-slate-50 text-slate-500"
                        }`}>
                          {activityLabel(entry)}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
