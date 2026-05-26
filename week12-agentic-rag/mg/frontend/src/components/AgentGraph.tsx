"use client";

import { useMemo } from "react";
import type { AgentNode } from "@/types/chat";
import type { GraphLiveState } from "@/hooks/useChat";

interface NodePos {
  id: AgentNode | "START" | "END";
  label: string;
  x: number;
  y: number;
  type: "start" | "router" | "executor" | "agent" | "retriever" | "writer" | "critic" | "end";
}

interface EdgeDef {
  from: NodePos["id"];
  to: NodePos["id"];
  loop?: boolean;
}

// 13개 도메인을 2열로 배치 (col1: 7, col2: 6)
const DOMAINS_COL1: AgentNode[] = [
  "shopping", "lifestyle", "sports", "news", "finance", "government", "education",
];
const DOMAINS_COL2: AgentNode[] = [
  "info", "documents", "data", "travel", "culture", "health",
];
const ALL_DOMAINS: AgentNode[] = [...DOMAINS_COL1, ...DOMAINS_COL2];

const NODE_LABELS: Record<AgentNode, string> = {
  supervisor: "Supervisor",
  planner: "Planner",
  executor: "Executor",
  replanner: "Replanner",
  shopping: "Shopping",
  lifestyle: "Lifestyle",
  sports: "Sports",
  news: "News",
  finance: "Finance",
  government: "Government",
  education: "Education",
  info: "Info",
  documents: "Documents",
  data: "Data",
  travel: "Travel",
  culture: "Culture",
  health: "Health",
  writer: "Writer",
  critic: "Critic",
};

// Layout — viewBox 880 × 560
const TOP_Y = 30;
const BOTTOM_Y = 530;
const COL1_X = 340;
const COL2_X = 460;
const NODE_W = 92;
const NODE_H = 30;

const col1Gap = (BOTTOM_Y - TOP_Y) / (DOMAINS_COL1.length - 1);
const col2Gap = (BOTTOM_Y - TOP_Y) / (DOMAINS_COL2.length - 1);

const NODES: NodePos[] = [
  { id: "START",     label: "START",     x: 30,  y: 280, type: "start" },
  { id: "planner",   label: "Planner",   x: 130, y: 280, type: "router" },
  { id: "executor",  label: "Executor",  x: 230, y: 240, type: "executor" },
  { id: "replanner", label: "Replanner", x: 230, y: 320, type: "router" },
  ...DOMAINS_COL1.map((d, i) => ({
    id: d,
    label: NODE_LABELS[d],
    x: COL1_X,
    y: TOP_Y + i * col1Gap,
    type: (d === "documents" ? "retriever" : "agent") as const,
  })),
  ...DOMAINS_COL2.map((d, i) => ({
    id: d,
    label: NODE_LABELS[d],
    x: COL2_X,
    y: TOP_Y + i * col2Gap,
    type: (d === "documents" ? "retriever" : "agent") as const,
  })),
  { id: "writer", label: "Writer", x: 600, y: 240, type: "writer" },
  { id: "critic", label: "Critic", x: 600, y: 320, type: "critic" },
  { id: "END",    label: "END",    x: 720, y: 280, type: "end" },
];

const EDGES: EdgeDef[] = [
  { from: "START", to: "planner" },
  { from: "planner", to: "executor" },
  { from: "planner", to: "writer" },
  ...ALL_DOMAINS.map((d) => ({ from: "executor" as const, to: d })),
  ...ALL_DOMAINS.map((d) => ({ from: d, to: "executor" as const })),
  { from: "executor", to: "replanner" },
  { from: "replanner", to: "executor", loop: true },
  { from: "replanner", to: "writer" },
  { from: "writer", to: "critic" },
  { from: "critic", to: "writer", loop: true },
  { from: "critic", to: "END" },
];

function nodeColor(type: NodePos["type"]) {
  switch (type) {
    case "start":    return { fill: "#2A2A31", stroke: "#7D7972", text: "#B5B0A6" };
    case "end":      return { fill: "#2A2A31", stroke: "#7D7972", text: "#B5B0A6" };
    case "router":   return { fill: "#1f1f24", stroke: "#B39DDB", text: "#B39DDB" };
    case "executor": return { fill: "#1f1f24", stroke: "#81C784", text: "#81C784" };
    case "agent":    return { fill: "#1f1f24", stroke: "#64B5F6", text: "#64B5F6" };
    case "retriever":return { fill: "#1f1f24", stroke: "#22D3EE", text: "#22D3EE" };
    case "writer":   return { fill: "#1f1f24", stroke: "#D4B07A", text: "#D4B07A" };
    case "critic":   return { fill: "#1f1f24", stroke: "#E57373", text: "#E57373" };
  }
}

interface Props {
  state: GraphLiveState;
  isStreaming: boolean;
}

export default function AgentGraph({ state, isStreaming }: Props) {
  const { active, done, activeEdge, plan, currentStepId, iteration, lastScore } = state;

  const nodeMap = useMemo(() => {
    const m = new Map<string, NodePos>();
    NODES.forEach((n) => m.set(n.id, n));
    return m;
  }, []);

  const activeDomains = new Set(
    plan.filter((s) => s.status === "active" || s.status === "done").map((s) => s.domain),
  );

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-stroke/30 px-5 py-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-[0.2em] text-pearl-muted/60">
          Plan-and-Execute Graph
        </h2>
        <p className="text-[10px] text-pearl-muted/40 mt-1">
          {isStreaming ? "실행 중..." : "대기 중 · Planner → Executor → Replanner"}
        </p>
        {(plan.length > 0 || iteration > 0 || lastScore !== null) && (
          <div className="mt-2 flex gap-2 flex-wrap">
            {plan.length > 0 && (
              <span className="rounded-md bg-purple-500/15 border border-purple-500/30 px-2 py-0.5 text-[10px] text-purple-300">
                Plan {plan.filter((s) => s.status === "done").length}/{plan.filter((s) => s.status !== "skipped").length}
              </span>
            )}
            {currentStepId !== null && (
              <span className="rounded-md bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 text-[10px] text-amber-400">
                Step {currentStepId}
              </span>
            )}
            {iteration > 0 && (
              <span className="rounded-md bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 text-[10px] text-amber-400">
                Iter {iteration}
              </span>
            )}
            {lastScore !== null && (
              <span
                className={`rounded-md border px-2 py-0.5 text-[10px] ${
                  lastScore >= 7
                    ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                    : "bg-red-500/15 border-red-500/30 text-red-400"
                }`}
              >
                {lastScore}/10
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto p-3">
        <svg viewBox="0 0 780 580" className="w-full h-auto" style={{ minHeight: 500 }}>
          {EDGES.map((e, i) => {
            const from = nodeMap.get(e.from);
            const to = nodeMap.get(e.to);
            if (!from || !to) return null;

            const x1 = from.x + NODE_W / 2;
            const y1 = from.y + NODE_H / 2;
            const x2 = to.x - NODE_W / 2;
            const y2 = to.y + NODE_H / 2;

            const isActiveEdge =
              activeEdge?.from === e.from && activeEdge?.to === e.to;

            const isPlanned =
              (e.from === "START" && e.to === "planner") ||
              (e.from === "planner" && (e.to === "executor" || (plan.length === 0 && e.to === "writer"))) ||
              (e.from === "executor" && activeDomains.has(e.to as AgentNode)) ||
              (activeDomains.has(e.from as AgentNode) && e.to === "executor") ||
              (e.from === "executor" && e.to === "replanner" && plan.length > 0) ||
              (e.from === "replanner" && e.to === "writer" && (done.has("replanner") || active.has("writer"))) ||
              (e.from === "writer" && e.to === "critic" && (active.has("writer") || done.has("writer"))) ||
              (e.from === "critic" && e.to === "END" && done.has("critic"));

            // 도메인 fan-out 엣지는 평소에 거의 안 보이게
            const isDomainFan =
              (e.from === "executor" && ALL_DOMAINS.includes(e.to as AgentNode)) ||
              (ALL_DOMAINS.includes(e.from as AgentNode) && e.to === "executor");

            const stroke = isActiveEdge
              ? "#D4B07A"
              : e.loop
              ? "#E57373"
              : isPlanned
              ? "#64B5F6"
              : "#2A2A31";
            const opacity = isActiveEdge
              ? 1
              : isPlanned
              ? 0.6
              : e.loop
              ? 0.35
              : isDomainFan
              ? 0.05
              : 0.18;
            const width = isActiveEdge ? 2.5 : 1;

            let path: string;
            if (e.loop) {
              // 루프 엣지: 위로 휘는 곡선
              const midX = (x1 + x2) / 2;
              path = `M ${x1} ${y1} C ${midX + 60} ${y1 - 28}, ${midX + 60} ${y2 - 28}, ${x2} ${y2}`;
            } else if (isDomainFan) {
              // Executor ↔ Domain: orthogonal 라우팅 (계단형) → 시각 정리
              const midX = (x1 + x2) / 2;
              path = `M ${x1} ${y1} L ${midX} ${y1} L ${midX} ${y2} L ${x2} ${y2}`;
            } else {
              const dx = x2 - x1;
              path = `M ${x1} ${y1} C ${x1 + dx * 0.4} ${y1}, ${x2 - dx * 0.4} ${y2}, ${x2} ${y2}`;
            }

            return (
              <g key={i}>
                <path
                  d={path}
                  stroke={stroke}
                  strokeWidth={width}
                  fill="none"
                  opacity={opacity}
                  strokeDasharray={isActiveEdge ? "4 3" : e.loop ? "5 3" : undefined}
                >
                  {isActiveEdge && (
                    <animate
                      attributeName="stroke-dashoffset"
                      from="0" to="-14" dur="0.6s" repeatCount="indefinite"
                    />
                  )}
                </path>
                {(isActiveEdge || isPlanned) && (
                  <circle cx={x2} cy={y2} r={2.5} fill={stroke} opacity={opacity} />
                )}
              </g>
            );
          })}

          {NODES.map((n) => {
            const c = nodeColor(n.type);
            const isActive = n.id !== "START" && n.id !== "END" && active.has(n.id as AgentNode);
            const isDone = n.id !== "START" && n.id !== "END" && done.has(n.id as AgentNode);

            const fill = isActive ? c.stroke + "33" : c.fill;
            const strokeWidth = isActive ? 2.5 : 1.3;
            const opacity =
              !isActive && !isDone && n.type === "agent" && plan.length > 0 && !activeDomains.has(n.id as AgentNode)
                ? 0.22
                : !isActive && !isDone && n.type === "retriever" && plan.length > 0 && !activeDomains.has(n.id as AgentNode)
                ? 0.22
                : 1;

            return (
              <g key={n.id} opacity={opacity}>
                {isActive && (
                  <rect
                    x={n.x - NODE_W / 2 - 4}
                    y={n.y - 4}
                    width={NODE_W + 8}
                    height={NODE_H + 8}
                    rx={9}
                    fill="none"
                    stroke={c.stroke}
                    strokeWidth={2}
                    opacity={0.4}
                  >
                    <animate attributeName="opacity" values="0.2;0.7;0.2" dur="1.2s" repeatCount="indefinite" />
                  </rect>
                )}
                <rect
                  x={n.x - NODE_W / 2}
                  y={n.y}
                  width={NODE_W}
                  height={NODE_H}
                  rx={6}
                  fill={fill}
                  stroke={c.stroke}
                  strokeWidth={strokeWidth}
                />
                <text
                  x={n.x}
                  y={n.y + NODE_H / 2 + 3.5}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight={isActive ? 600 : 500}
                  fill={c.text}
                >
                  {n.label}
                </text>
                {isDone && (
                  <circle cx={n.x + NODE_W / 2 - 6} cy={n.y + 6} r={3} fill="#81C784" />
                )}
              </g>
            );
          })}
        </svg>

        <div className="mt-3 space-y-1 text-[10px] text-pearl-muted/50">
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-purple-400" />
            <span>Planner / Replanner — 계획 / 재계획</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
            <span>Executor — step 디스패치</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-blue-400" />
            <span>Domain Agent (13개) — 도구 실행</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-cyan-400" />
            <span>Documents — Self-RAG 내장</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-gold" />
            <span>Writer — 답변 작성</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-red-400" />
            <span>Critic — 채점 (7점 미만 재작성)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
