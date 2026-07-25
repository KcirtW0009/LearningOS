"use client";

import React, { useMemo } from "react";

/* ═══════════════════════════════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════════════════════════════ */

type NodeItem = {
  id: string;
  title: string;
  status: string;
  difficulty: string;
  type: string;
  score: number;
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
  width?: number;
  height?: number;
};

/* ═══════════════════════════════════════════════════════════════════
   STATUS COLORS
   ═══════════════════════════════════════════════════════════════════ */

const STATUS_COLORS: Record<string, string> = {
  MASTERED: "#8b5cf6",
  COMPLETED: "#10b981",
  AVAILABLE: "#6366f1",
  IN_PROGRESS: "#3b82f6",
  NOT_STARTED: "#94a3b8",
  LOCKED: "#cbd5e1",
};

const STATUS_RING: Record<string, string> = {
  MASTERED: "#c4b5fd",
  COMPLETED: "#6ee7b7",
  AVAILABLE: "#a5b4fc",
  IN_PROGRESS: "#93c5fd",
  NOT_STARTED: "#cbd5e1",
  LOCKED: "#e2e8f0",
};

const TIER_COLORS = [
  "#475569", "#0284c7", "#4338ca", "#a21caf",
  "#0d9488", "#d97706", "#e11d48", "#ef4444",
];

/* ═══════════════════════════════════════════════════════════════════
   STAR CHART COMPONENT
   ═══════════════════════════════════════════════════════════════════ */

export default function StarChart({
  nodes,
  edges,
  selectedId,
  onSelect,
  onSetTaskTarget,
  taskTargetId,
  taskPath,
  width = 900,
  height = 700,
}: Props) {
  const pathIds = useMemo(() => new Set(taskPath.map((n) => n.id)), [taskPath]);
  const taskTargetSet = useMemo(() => taskTargetId, [taskTargetId]);

  /* Group nodes by tier prefix */
  const tiers = useMemo(() => {
    const tierMap: Map<string, NodeItem[]> = new Map();
    for (const n of nodes) {
      const prefix = n.id.split("-")[0] || "other";
      if (!tierMap.has(prefix)) tierMap.set(prefix, []);
      tierMap.get(prefix)!.push(n);
    }
    // Ensure consistent tier order
    const orderedTiers = Array.from(tierMap.entries()).sort(([a], [b]) => {
      const order = ["found", "vis", "lang", "gen", "mm", "agent", "emb", "boss"];
      return order.indexOf(a) - order.indexOf(b);
    });
    return orderedTiers;
  }, [nodes]);

  /* Compute node positions in concentric rings */
  const positions = useMemo(() => {
    const cx = width / 2;
    const cy = height / 2;
    const baseRadius = 40;
    const tierGap = 75;
    const maxRadius = Math.min(cx, cy) - 60;
    const pos = new Map<string, { x: number; y: number; r: number }>();

    tiers.forEach(([_tierName, tierNodes], ti) => {
      const radius = Math.min(baseRadius + ti * tierGap, maxRadius);
      const count = tierNodes.length;
      const startAngle = -Math.PI / 2; // Start from top

      tierNodes.forEach((node, i) => {
        // For the center (tier 0), place in the middle
        if (ti === 0 && count === 1) {
          pos.set(node.id, { x: cx, y: cy, r: 18 });
          return;
        }
        const angle = startAngle + (2 * Math.PI * i) / count;
        pos.set(node.id, {
          x: cx + radius * Math.cos(angle),
          y: cy + radius * Math.sin(angle),
          r: 14,
        });
      });
    });

    return pos;
  }, [tiers, width, height]);

  /* Build edge map for rendering */
  const edgeMap = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const e of edges) {
      if (!map.has(e.from)) map.set(e.from, []);
      map.get(e.from)!.push(e.to);
    }
    return map;
  }, [edges]);

  return (
    <div className="w-full h-full flex items-center justify-center overflow-hidden bg-slate-50 rounded-xl">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="select-none"
        style={{ maxWidth: "100%", maxHeight: "100%" }}
      >
        {/* Background gradient */}
        <defs>
          <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#f8fafc" />
            <stop offset="100%" stopColor="#f1f5f9" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <rect width={width} height={height} fill="url(#bgGrad)" />

        {/* Tier rings */}
        {tiers.map(([tierName], ti) => {
          const radius = Math.min(40 + ti * 75, Math.min(width, height) / 2 - 60);
          if (ti === 0) return null;
          return (
            <circle
              key={tierName}
              cx={width / 2}
              cy={height / 2}
              r={radius}
              fill="none"
              stroke="#e2e8f0"
              strokeWidth={0.5}
              strokeDasharray="4 4"
              opacity={0.5}
            />
          );
        })}

        {/* Tier labels */}
        {tiers.map(([tierName], ti) => {
          const radius = Math.min(40 + ti * 75, Math.min(width, height) / 2 - 60);
          const labelRadius = ti === 0 ? 20 : radius;
          const color = TIER_COLORS[ti % TIER_COLORS.length];
          return (
            <text
              key={`label-${tierName}`}
              x={width / 2 + labelRadius}
              y={height / 2 - 8}
              textAnchor="middle"
              fill={color}
              fontSize={10}
              fontWeight={700}
              opacity={0.4}
            >
              {tierName.toUpperCase()}
            </text>
          );
        })}

        {/* Edges */}
        {edges.map((edge, ei) => {
          const from = positions.get(edge.from);
          const to = positions.get(edge.to);
          if (!from || !to) return null;

          const isPathEdge =
            pathIds.has(edge.from) && pathIds.has(edge.to);
          const isBlocking =
            edge.relation === "prerequisite" || edge.relation === "progression";

          return (
            <line
              key={`edge-${ei}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={
                isPathEdge ? "#6366f1" : isBlocking ? "#94a3b8" : "#cbd5e1"
              }
              strokeWidth={isPathEdge ? 2 : isBlocking ? 1 : 0.5}
              strokeDasharray={isBlocking && !isPathEdge ? "" : isPathEdge ? "" : "3 3"}
              opacity={isPathEdge ? 0.9 : isBlocking ? 0.5 : 0.3}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const pos = positions.get(node.id);
          if (!pos) return null;

          const isSelected = node.id === selectedId;
          const isInPath = pathIds.has(node.id);
          const isTarget = node.id === taskTargetSet;
          const color = STATUS_COLORS[node.status] || "#94a3b8";
          const ringColor = STATUS_RING[node.status] || "#cbd5e1";
          const taskIndex = taskPath.findIndex((n) => n.id === node.id);

          return (
            <g
              key={node.id}
              onClick={() => onSelect(node.id)}
              onDoubleClick={() => onSetTaskTarget && onSetTaskTarget(node.id)}
              className="cursor-pointer"
              style={{ transition: "transform 0.2s" }}
            >
              {/* Target indicator ring (outermost) */}
              {isTarget && (
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={pos.r + 12}
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  strokeDasharray="4 3"
                  opacity={0.9}
                />
              )}
              {/* Outer ring for selected/path */}
              {(isSelected || isInPath) && (
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={pos.r + 6}
                  fill="none"
                  stroke={isSelected ? "#6366f1" : "#a5b4fc"}
                  strokeWidth={isSelected ? 3 : 2}
                  opacity={isSelected ? 1 : 0.7}
                  filter={isSelected ? "url(#glow)" : undefined}
                />
              )}

              {/* Node circle */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={pos.r}
                fill={color}
                stroke={ringColor}
                strokeWidth={2}
                opacity={node.status === "LOCKED" ? 0.4 : 0.9}
              />

              {/* Mastered star indicator */}
              {node.status === "MASTERED" && (
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fill="white"
                  fontSize={12}
                  fontWeight={700}
                >
                  ★
                </text>
              )}

              {/* Score indicator for completed */}
              {node.status === "COMPLETED" && node.score > 0 && (
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fill="white"
                  fontSize={9}
                  fontWeight={700}
                >
                  ✓
                </text>
              )}

              {/* Task path step number */}
              {isInPath && taskIndex >= 0 && (
                <text
                  x={pos.x}
                  y={pos.y - pos.r - 10}
                  textAnchor="middle"
                  fill="#6366f1"
                  fontSize={9}
                  fontWeight={700}
                >
                  {taskIndex + 1}
                </text>
              )}

              {/* Label */}
              <text
                x={pos.x}
                y={pos.y + pos.r + 14}
                textAnchor="middle"
                fill={node.status === "LOCKED" ? "#94a3b8" : "#334155"}
                fontSize={9}
                fontWeight={isSelected ? 600 : 400}
                opacity={node.status === "LOCKED" ? 0.5 : 0.85}
              >
                {node.title.length > 10
                  ? node.title.slice(0, 10) + "..."
                  : node.title}
              </text>
            </g>
          );
        })}

        {/* Legend */}
        <g transform={`translate(${width - 130}, 10)`}>
          {[
            { label: "任务目标", color: "#f59e0b", dashed: true },
            { label: "已精通", color: STATUS_COLORS.MASTERED },
            { label: "已完成", color: STATUS_COLORS.COMPLETED },
            { label: "可学习", color: STATUS_COLORS.AVAILABLE },
            { label: "学习中", color: STATUS_COLORS.IN_PROGRESS },
            { label: "锁定", color: STATUS_COLORS.LOCKED },
          ].map((item, i) => (
            <g key={item.label} transform={`translate(0, ${i * 18})`}>
              <circle
                cx={6} cy={6} r={5}
                fill={(item as any).dashed ? "none" : item.color}
                stroke={(item as any).dashed ? item.color : "none"}
                strokeWidth={(item as any).dashed ? 1.5 : 0}
                strokeDasharray={(item as any).dashed ? "2 2" : "none"}
                opacity={0.9}
              />
              {!(item as any).dashed && <circle cx={6} cy={6} r={5} fill={item.color} opacity={0.8} />}
              <text x={16} y={9} fill="#64748b" fontSize={9}>
                {item.label}
              </text>
            </g>
          ))}
        </g>
        {/* Hint text */}
        <text
          x={10}
          y={height - 10}
          fill="#94a3b8"
          fontSize={9}
        >
          💡 单击查看详情 · 双击设为任务目标
        </text>
      </svg>
    </div>
  );
}
