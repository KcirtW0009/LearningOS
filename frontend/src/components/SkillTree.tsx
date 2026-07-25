"use client";

import React, { useMemo, useState, useRef, useEffect } from "react";

type NodeItem = {
  id: string;
  title: string;
  status: string;
  difficulty: string;
  type: string;
  score: number;
  proficiency?: { label: string; label_en: string; color: string; icon: string };
};

type EdgeItem = {
  from: string;
  to: string;
  relation: string;
};

type Props = {
  nodes: NodeItem[];
  edges: EdgeItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onSetTaskTarget?: (id: string) => void;
  taskTargetId?: string | null;
  taskPath: { id: string; status: string }[];
  nodeDetails?: Record<string, { title: string; description?: string }>;
};

const STATUS_FILL: Record<string, string> = {
  MASTERED: "#8b5cf6",
  COMPLETED: "#3b82f6",
  AVAILABLE: "#10b981",
  IN_PROGRESS: "#f59e0b",
  NOT_STARTED: "#94a3b8",
  LOCKED: "#cbd5e1",
};

export const PROFICIENCY_COLORS: Record<string, string> = {
  "None": "#94a3b8",
  "Done": "#94a3b8",
  "Known": "#3b82f6",
  "Skilled": "#8b5cf6",
  "Expert": "#f59e0b",
  "Master": "#ef4444",
};

export const PROFICIENCY_LABELS: Record<string, string> = {
  "None": "未开始",
  "Done": "完成",
  "Known": "熟悉",
  "Skilled": "掌握",
  "Expert": "熟练",
  "Master": "精通",
};

const STATUS_TEXT: Record<string, string> = {
  MASTERED: "text-violet-700",
  COMPLETED: "text-blue-700",
  AVAILABLE: "text-emerald-700",
  IN_PROGRESS: "text-amber-700",
  NOT_STARTED: "text-slate-500",
  LOCKED: "text-slate-400",
};

const TYPE_META: Record<string, { icon: string; label: string; color: string }> = {
  concept: { icon: "📖", label: "概念", color: "bg-sky-100 text-sky-700" },
  skill: { icon: "🔧", label: "技能", color: "bg-amber-100 text-amber-700" },
  project: { icon: "🚀", label: "项目", color: "bg-rose-100 text-rose-700" },
  milestone: { icon: "🏁", label: "里程碑", color: "bg-violet-100 text-violet-700" },
};

const DIFF_META: Record<string, { label: string; cls: string }> = {
  beginner: { label: "入门", cls: "bg-emerald-100 text-emerald-700" },
  intermediate: { label: "进阶", cls: "bg-amber-100 text-amber-700" },
  advanced: { label: "高级", cls: "bg-rose-100 text-rose-700" },
};

const STATUS_LABEL: Record<string, string> = {
  NOT_STARTED: "待解锁",
  LOCKED: "🔒 锁定",
  AVAILABLE: "可学习",
  IN_PROGRESS: "⋯ 学习中",
  COMPLETED: "✓ 已完成",
  MASTERED: "★ 已精通",
};

type TreeNode = {
  id: string;
  node: NodeItem;
  depth: number;
  children: TreeNode[];
  parents: string[];
};

export default function SkillTree({
  nodes,
  edges,
  selectedId,
  onSelect,
  onSetTaskTarget,
  taskTargetId,
  taskPath,
  nodeDetails,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const dragStateRef = useRef({
    startX: 0,
    startY: 0,
    startTranslateX: 0,
    startTranslateY: 0,
    isActive: false,
  });

  const pathIds = useMemo(() => new Set(taskPath.map((n) => n.id)), [taskPath]);
  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  const { roots, childrenMap, parentMap } = useMemo(() => {
    const childrenMap = new Map<string, string[]>();
    const parentMap = new Map<string, string[]>();
    const nodeIds = new Set(nodes.map((n) => n.id));

    for (const e of edges) {
      const from = e.from;
      const to = e.to;
      if (!nodeIds.has(from) || !nodeIds.has(to)) continue;
      const isBlocking = e.relation === "prerequisite" || e.relation === "progression" || e.relation === "dependency";
      if (!isBlocking) continue;
      if (!childrenMap.has(from)) childrenMap.set(from, []);
      childrenMap.get(from)!.push(to);
      if (!parentMap.has(to)) parentMap.set(to, []);
      parentMap.get(to)!.push(from);
    }

    const roots = nodes.filter((n) => !parentMap.has(n.id) || parentMap.get(n.id)!.length === 0).map((n) => n.id);
    return { roots, childrenMap, parentMap };
  }, [nodes, edges]);

  const depthMap = useMemo(() => {
    const dm = new Map<string, number>();
    const queue: string[] = [...roots];
    roots.forEach((r) => dm.set(r, 0));
    while (queue.length > 0) {
      const cur = queue.shift()!;
      const d = dm.get(cur) ?? 0;
      for (const child of childrenMap.get(cur) ?? []) {
        const prev = dm.get(child);
        const next = d + 1;
        if (prev === undefined || next > prev) {
          dm.set(child, next);
          queue.push(child);
        }
      }
    }
    let maxD = 0;
    for (const v of dm.values()) maxD = Math.max(maxD, v);
    for (const n of nodes) {
      if (!dm.has(n.id)) dm.set(n.id, maxD + 1);
    }
    return dm;
  }, [roots, childrenMap, nodes]);

  const rows = useMemo(() => {
    const byDepth = new Map<number, string[]>();
    for (const n of nodes) {
      const d = depthMap.get(n.id) ?? 0;
      if (!byDepth.has(d)) byDepth.set(d, []);
      byDepth.get(d)!.push(n.id);
    }
    const maxD = Math.max(...byDepth.keys(), 0);
    const r: string[][] = [];
    for (let d = 0; d <= maxD; d++) {
      r.push(byDepth.get(d) ?? []);
    }
    return r;
  }, [nodes, depthMap]);

  const colMap = useMemo(() => {
    const cm = new Map<string, number>();
    rows.forEach((row) => {
      row.forEach((id, ci) => {
        cm.set(id, ci);
      });
    });
    return cm;
  }, [rows]);

  const maxCols = useMemo(() => Math.max(...rows.map((r) => r.length), 1), [rows]);

  const CELL_W = 90;
  const CELL_H = 90;
  const COL_GAP = 24;
  const ROW_GAP = 48;

  const SVG_W = Math.max(maxCols * (CELL_W + COL_GAP) + 80, 800);
  const SVG_H = Math.max(rows.length * (CELL_H + ROW_GAP) - ROW_GAP + 200, 800);

  const getPos = (id: string) => {
    const d = depthMap.get(id) ?? 0;
    const ci = colMap.get(id) ?? 0;
    const row = rows[d] ?? [];
    const colsInRow = row.length;
    const rowWidth = colsInRow * CELL_W + (colsInRow - 1) * COL_GAP;
    const rowStartX = (SVG_W - rowWidth) / 2;
    const x = rowStartX + ci * (CELL_W + COL_GAP) + CELL_W / 2;
    const y = 60 + d * (CELL_H + ROW_GAP) + CELL_H / 2;
    return { x, y };
  };

  useEffect(() => {
    if (selectedId) {
      const pos = getPos(selectedId);
      setTranslate({
        x: -pos.x + window.innerWidth / 2,
        y: -pos.y + window.innerHeight / 2,
      });
    }
  }, [selectedId]);

  const isCompleted = (id: string) => {
    const n = nodeMap.get(id);
    return n?.status === "COMPLETED" || n?.status === "MASTERED";
  };

  const hoveredNode = hoveredId ? nodeMap.get(hoveredId) : null;
  const hoveredDetail = hoveredId ? nodeDetails?.[hoveredId] : null;
  const hoveredPos = hoveredId ? getPos(hoveredId) : null;

  const getIdAbbr = (id: string) => {
    const parts = id.split("-");
    if (parts.length >= 2) {
      return (parts[0].slice(0, 1) + parts[1].slice(0, 1)).toUpperCase();
    }
    return id.slice(0, 2).toUpperCase();
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();

    dragStateRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      startTranslateX: translate.x,
      startTranslateY: translate.y,
      isActive: true,
    };
    setIsDragging(true);

    const handleMouseMove = (e: MouseEvent) => {
      if (!dragStateRef.current.isActive) return;
      e.preventDefault();

      const dx = e.clientX - dragStateRef.current.startX;
      const dy = e.clientY - dragStateRef.current.startY;

      setTranslate({
        x: dragStateRef.current.startTranslateX + dx,
        y: dragStateRef.current.startTranslateY + dy,
      });
    };

    const handleMouseUp = () => {
      dragStateRef.current.isActive = false;
      setIsDragging(false);
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    if (e.shiftKey) {
      e.preventDefault();
      setTranslate((prev) => ({
        ...prev,
        x: prev.x + e.deltaY,
      }));
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-50 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="font-semibold text-slate-700">🌳 技能树视图</span>
          <span>·</span>
          <span>{nodes.length} 节点</span>
          <span>·</span>
          <span>{rows.length} 层</span>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-slate-400">
          <span className="inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> 可学习
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500" /> 已完成
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-slate-300" /> 锁定
          </span>
          <span className="inline-flex items-center gap-1 text-amber-600">
            🎯 双击设为目标
          </span>
          <span className="inline-flex items-center gap-1 text-indigo-600 pl-2 border-l border-slate-200">
            🖱️ 拖拽 / 滚轮导航
          </span>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-hidden p-4 relative select-none"
        style={{
          cursor: isDragging ? "grabbing" : "grab",
          minHeight: 0,
        } as React.CSSProperties}
        onMouseDown={handleMouseDown}
        onWheel={handleWheel}
      >
        {hoveredId && hoveredNode && hoveredPos && (
          <div
            className="absolute z-50 pointer-events-none"
            style={{
              left: Math.min(Math.max(hoveredPos.x + translate.x + 40, 16), window.innerWidth - 260),
              top: Math.max(hoveredPos.y + translate.y - 20, 16),
            }}
          >
            <div className="bg-white rounded-xl shadow-2xl border border-slate-200 p-3 w-60 animate-fade-in">
              <div className="text-sm font-bold text-slate-800 mb-2">
                {hoveredDetail?.title || hoveredNode.title}
              </div>
              <div className="flex items-center gap-1.5 flex-wrap mb-2">
                {hoveredNode.difficulty && DIFF_META[hoveredNode.difficulty] && (
                  <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-medium ${DIFF_META[hoveredNode.difficulty].cls}`}>
                    {DIFF_META[hoveredNode.difficulty].label}
                  </span>
                )}
                {hoveredNode.type && TYPE_META[hoveredNode.type] && (
                  <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-medium ${TYPE_META[hoveredNode.type].color}`}>
                    {TYPE_META[hoveredNode.type].icon} {TYPE_META[hoveredNode.type].label}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium
                  ${hoveredNode.status === "COMPLETED" || hoveredNode.status === "MASTERED"
                    ? "bg-emerald-100 text-emerald-700"
                    : hoveredNode.status === "AVAILABLE"
                    ? "bg-indigo-100 text-indigo-700"
                    : hoveredNode.status === "IN_PROGRESS"
                    ? "bg-blue-100 text-blue-700"
                    : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {STATUS_LABEL[hoveredNode.status] || hoveredNode.status}
                </span>
                {(hoveredNode.status === "COMPLETED" || hoveredNode.status === "MASTERED") && hoveredNode.score > 0 && (
                  <span className="text-[10px] font-bold text-emerald-600">
                    ✓ {hoveredNode.score}分
                  </span>
                )}
              </div>
              {hoveredNode.score > 0 && (
                <div className="flex items-center gap-1.5 mb-2">
                  <span className="text-[10px] text-slate-400">熟练度:</span>
                  <span className="text-[10px] font-semibold" style={{ color: (hoveredNode as any).proficiency?.color || PROFICIENCY_COLORS.Completed }}>
                    {(hoveredNode as any).proficiency?.label || ""}
                  </span>
                </div>
              )}
              {hoveredDetail?.description && (
                <div className="text-[10px] text-slate-500 leading-relaxed line-clamp-3">
                  {hoveredDetail.description.length > 60
                    ? hoveredDetail.description.slice(0, 60) + "..."
                    : hoveredDetail.description}
                </div>
              )}
            </div>
          </div>
        )}

        <div
          style={{
            minWidth: SVG_W,
            minHeight: SVG_H,
            position: "relative",
            transform: `translate(${translate.x}px, ${translate.y}px)`,
            transformOrigin: "top left",
            transition: isDragging ? "none" : "transform 100ms ease-out",
          }}
        >
          <svg
            width={SVG_W}
            height={SVG_H}
            style={{ display: "block" }}
          >
            <defs>
              <marker
                id="arrow-complete"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
              </marker>
              <marker
                id="arrow-path"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1" />
              </marker>
              <marker
                id="arrow-lock"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#cbd5e1" />
              </marker>
              <linearGradient id="rowGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f8fafc" />
                <stop offset="100%" stopColor="#f1f5f9" />
              </linearGradient>
            </defs>

            {rows.map((_, d) => (
              <rect
                key={`row-bg-${d}`}
                x={0}
                y={60 + d * (CELL_H + ROW_GAP) - ROW_GAP / 2}
                width={SVG_W}
                height={CELL_H + ROW_GAP}
                fill={d % 2 === 0 ? "url(#rowGrad)" : "#ffffff"}
                opacity={0.4}
              />
            ))}

            {rows.map((_, d) => (
              <g key={`row-label-${d}`}>
                <text
                  x={10}
                  y={60 + d * (CELL_H + ROW_GAP) + CELL_H / 2 + 4}
                  fontSize={11}
                  fontWeight={700}
                  fill="#94a3b8"
                >
                  L{d + 1}
                </text>
              </g>
            ))}

            {edges.map((e, ei) => {
              const from = e.from;
              const to = e.to;
              const fromPos = getPos(from);
              const toPos = getPos(to);
              if (!fromPos || !toPos) return null;
              const isBlocking =
                e.relation === "prerequisite" || e.relation === "progression" || e.relation === "dependency";
              if (!isBlocking) return null;

              const isPathEdge = pathIds.has(from) && pathIds.has(to);
              const fromDone = isCompleted(from);

              const sx = fromPos.x;
              const sy = fromPos.y + 28;
              const tx = toPos.x;
              const ty = toPos.y - 28;
              const midY = (sy + ty) / 2;

              return (
                <g key={`edge-${ei}`}>
                  <path
                    d={`M ${sx} ${sy} C ${sx} ${midY}, ${tx} ${midY}, ${tx} ${ty}`}
                    fill="none"
                    stroke={isPathEdge ? "#6366f1" : fromDone ? "#10b981" : "#cbd5e1"}
                    strokeWidth={isPathEdge ? 2.5 : fromDone ? 1.5 : 1}
                    strokeDasharray={fromDone || isPathEdge ? "none" : "4 4"}
                    opacity={isPathEdge ? 0.95 : fromDone ? 0.7 : 0.4}
                    markerEnd={
                      isPathEdge ? "url(#arrow-path)" : fromDone ? "url(#arrow-complete)" : "url(#arrow-lock)"
                    }
                  />
                </g>
              );
            })}

            {nodes.map((n) => {
              const pos = getPos(n.id);
              const isSelected = n.id === selectedId;
              const isInPath = pathIds.has(n.id);
              const isTarget = n.id === taskTargetId;
              const isHovered = hoveredId === n.id;
              const taskIndex = taskPath.findIndex((tp) => tp.id === n.id);
              const prof = n.proficiency;
              const fillColor = (n.score > 0 && prof?.label_en)
                ? (PROFICIENCY_COLORS[prof.label_en] || STATUS_FILL[n.status] || "#94a3b8")
                : (STATUS_FILL[n.status] || "#94a3b8");
              const abbr = getIdAbbr(n.id);

              return (
                <g
                  key={`node-${n.id}`}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (n.status !== "LOCKED") {
                      onSelect(n.id);
                    }
                  }}
                  onDoubleClick={(e) => {
                    e.stopPropagation();
                    if (onSetTaskTarget) {
                      onSetTaskTarget(n.id);
                    }
                  }}
                  onMouseEnter={() => setHoveredId(n.id)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  {isTarget && (
                    <circle
                      cx={0}
                      cy={0}
                      r={40}
                      fill="none"
                      stroke="#f59e0b"
                      strokeWidth={2.5}
                      strokeDasharray="6 4"
                      opacity={0.9}
                    />
                  )}

                  {(isSelected || isInPath) && (
                    <circle
                      cx={0}
                      cy={0}
                      r={isSelected ? 35 : 33}
                      fill="none"
                      stroke={isSelected ? "#6366f1" : "#a5b4fc"}
                      strokeWidth={isSelected ? 3 : 2}
                      opacity={isSelected ? 1 : 0.8}
                    />
                  )}

                  {isHovered && n.status !== "LOCKED" && (
                    <circle
                      cx={0}
                      cy={0}
                      r={36}
                      fill={fillColor}
                      opacity={0.15}
                    />
                  )}

                  {taskIndex >= 0 && (
                    <g>
                      <rect
                        x={-10}
                        y={-48}
                        width={20}
                        height={16}
                        rx={8}
                        fill="#6366f1"
                      />
                      <text
                        x={0}
                        y={-36}
                        fontSize={10}
                        fontWeight={700}
                        fill="#ffffff"
                        textAnchor="middle"
                      >
                        #{taskIndex + 1}
                      </text>
                    </g>
                  )}

                  <circle
                    cx={0}
                    cy={0}
                    r={28}
                    fill={fillColor}
                    stroke={n.status === "LOCKED" ? "#e2e8f0" : "rgba(255,255,255,0.3)"}
                    strokeWidth={2}
                    style={{
                      filter: isSelected
                        ? "drop-shadow(0 4px 12px rgba(99,102,241,0.4))"
                        : isHovered && n.status !== "LOCKED"
                        ? "drop-shadow(0 2px 8px rgba(0,0,0,0.15))"
                        : undefined,
                      transition: "all 150ms ease",
                      transform: isHovered && n.status !== "LOCKED" ? "translateY(-1px)" : undefined,
                    }}
                  />

                  <text
                    x={0}
                    y={4}
                    fontSize={11}
                    fontWeight={700}
                    fill="#ffffff"
                    textAnchor="middle"
                    style={{ pointerEvents: "none" }}
                  >
                    {abbr}
                  </text>
                  {n.score > 0 && prof?.icon && (
                    <text
                      x={0}
                      y={18}
                      fontSize={14}
                      fill="#ffffff"
                      textAnchor="middle"
                      style={{ pointerEvents: "none" }}
                    >
                      {prof.icon}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        </div>

        {nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
            暂无节点数据
          </div>
        )}
      </div>

      <div className="px-4 py-1.5 border-t border-slate-200 bg-white/50 text-[10px] text-slate-400 flex items-center justify-between">
        <span>↕ 上下滑动查看后续节点 · ↔ 左右滑动查看宽图</span>
        <span>点击节点 = 查看详情 · 双击节点 = 设为目标</span>
      </div>
    </div>
  );
}
