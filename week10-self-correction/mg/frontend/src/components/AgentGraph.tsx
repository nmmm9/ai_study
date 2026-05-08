"use client";

import { useMemo } from "react";
import type { AgentNode } from "@/types/chat";
import type { GraphLiveState } from "@/hooks/useChat";

interface NodePos {
  id: AgentNode | "START" | "END";
  label: string;
  x: number;
  y: number;
  type: "start" | "router" | "agent" | "writer" | "critic" | "end";
}

interface EdgeDef {
  from: NodePos["id"];
  to: NodePos["id"];
  loop?: boolean;
}

const DOMAINS: AgentNode[] = [
  "shopping", "lifestyle", "sports", "news",
  "finance", "government", "education", "info",
];

const TOP_Y = 30;
const BOTTOM_Y = 470;
const DOMAIN_X = 320;
const ROW_GAP = (BOTTOM_Y - TOP_Y) / (DOMAINS.length - 1);

const DOMAIN_LABELS: Record<AgentNode, string> = {
  supervisor: "Supervisor",
  shopping: "Shopping",
  lifestyle: "Lifestyle",
  sports: "Sports",
  news: "News",
  finance: "Finance",
  government: "Government",
  education: "Education",
  info: "Info",
  writer: "Writer",
  critic: "Critic",
};

const NODES: NodePos[] = [
  { id: "START",      label: "START",      x: 40,  y: 250, type: "start" },
  { id: "supervisor", label: "Supervisor", x: 160, y: 250, type: "router" },
  ...DOMAINS.map((d, i) => ({
    id: d,
    label: DOMAIN_LABELS[d],
    x: DOMAIN_X,
    y: TOP_Y + i * ROW_GAP,
    type: "agent" as const,
  })),
  { id: "writer", label: "Writer", x: 480, y: 220, type: "writer" },
  { id: "critic", label: "Critic", x: 480, y: 320, type: "critic" },
  { id: "END",    label: "END",    x: 660, y: 270, type: "end" },
];

const EDGES: EdgeDef[] = [
  { from: "START", to: "supervisor" },
  ...DOMAINS.map((d) => ({ from: "supervisor" as const, to: d })),
  { from: "supervisor", to: "writer" },
  ...DOMAINS.map((d) => ({ from: d, to: "writer" as const })),
  { from: "writer", to: "critic" },
  { from: "critic", to: "writer", loop: true },
  { from: "critic", to: "END" },
];

const NODE_W = 110;
const NODE_H = 36;

function nodeColor(type: NodePos["type"]) {
  switch (type) {
    case "start":  return { fill: "#2A2A31", stroke: "#7D7972", text: "#B5B0A6" };
    case "end":    return { fill: "#2A2A31", stroke: "#7D7972", text: "#B5B0A6" };
    case "router": return { fill: "#1f1f24", stroke: "#B39DDB", text: "#B39DDB" };
    case "agent":  return { fill: "#1f1f24", stroke: "#64B5F6", text: "#64B5F6" };
    case "writer": return { fill: "#1f1f24", stroke: "#D4B07A", text: "#D4B07A" };
    case "critic": return { fill: "#1f1f24", stroke: "#E57373", text: "#E57373" };
  }
}

interface Props {
  state: GraphLiveState;
  isStreaming: boolean;
}

export default function AgentGraph({ state, isStreaming }: Props) {
  const { active, done, activeEdge, plan, iteration, lastScore } = state;

  const nodeMap = useMemo(() => {
    const m = new Map<string, NodePos>();
    NODES.forEach((n) => m.set(n.id, n));
    return m;
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-stroke/30 px-5 py-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-[0.2em] text-pearl-muted/60">
          Agent Graph
        </h2>
        <p className="text-[10px] text-pearl-muted/40 mt-1">
          {isStreaming ? "실행 중..." : "대기 중 — Self-Correction 루프"}
        </p>
        {(iteration > 0 || lastScore !== null) && (
          <div className="mt-2 flex gap-2">
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
                Score {lastScore}/10
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        <svg viewBox="0 0 740 510" className="w-full h-auto" style={{ minHeight: 460 }}>
          {/* Edges */}
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

            const planSet = new Set(plan);
            const isPlanned =
              (e.from === "START" && e.to === "supervisor") ||
              (e.from === "supervisor" && (planSet.has(e.to) || (plan.length === 0 && e.to === "writer"))) ||
              (planSet.has(e.from as string) && e.to === "writer") ||
              (e.from === "writer" && e.to === "critic" && (active.has("writer") || done.has("writer"))) ||
              (e.from === "critic" && e.to === "END" && (done.has("critic") || active.has("critic"))) ||
              (e.loop && iteration > 1);

            const stroke = isActiveEdge
              ? "#D4B07A"
              : e.loop
              ? "#E57373"
              : isPlanned
              ? "#64B5F6"
              : "#383840";
            const opacity = isActiveEdge ? 1 : isPlanned ? 0.55 : e.loop ? 0.4 : 0.2;
            const width = isActiveEdge ? 2.5 : 1.4;

            // Loop edge curves above the writer/critic
            let path: string;
            if (e.loop) {
              const midX = (x1 + x2) / 2;
              path = `M ${x1} ${y1} C ${midX + 90} ${y1 - 30}, ${midX + 90} ${y2 - 30}, ${x2} ${y2}`;
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
                      from="0"
                      to="-14"
                      dur="0.6s"
                      repeatCount="indefinite"
                    />
                  )}
                </path>
                <circle cx={x2} cy={y2} r={3} fill={stroke} opacity={opacity} />
                {e.loop && (
                  <text
                    x={(x1 + x2) / 2 + 60}
                    y={Math.min(y1, y2) - 18}
                    fontSize="9"
                    fill="#E57373"
                    opacity={0.7}
                    fontStyle="italic"
                  >
                    재작성 (점수 &lt; 7)
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {NODES.map((n) => {
            const c = nodeColor(n.type);
            const isActive = n.id !== "START" && n.id !== "END" && active.has(n.id as AgentNode);
            const isDone = n.id !== "START" && n.id !== "END" && done.has(n.id as AgentNode);

            const fill = isActive ? c.stroke + "33" : c.fill;
            const strokeWidth = isActive ? 2.5 : 1.5;
            const opacity =
              !isActive && !isDone && n.type === "agent" && plan.length > 0 && !plan.includes(n.id)
                ? 0.35
                : 1;

            return (
              <g key={n.id} opacity={opacity}>
                {isActive && (
                  <rect
                    x={n.x - NODE_W / 2 - 4}
                    y={n.y - 4}
                    width={NODE_W + 8}
                    height={NODE_H + 8}
                    rx={10}
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
                  rx={7}
                  fill={fill}
                  stroke={c.stroke}
                  strokeWidth={strokeWidth}
                />
                <text
                  x={n.x}
                  y={n.y + NODE_H / 2 + 4}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight={isActive ? 600 : 500}
                  fill={c.text}
                >
                  {n.label}
                </text>
                {isDone && (
                  <circle
                    cx={n.x + NODE_W / 2 - 8}
                    cy={n.y + 8}
                    r={3.5}
                    fill="#81C784"
                  />
                )}
              </g>
            );
          })}
        </svg>

        {plan.length > 0 && (
          <div className="mt-4 rounded-lg border border-stroke/40 bg-base-50/40 px-3 py-2.5">
            <p className="text-[10px] uppercase tracking-wider text-pearl-muted/50 mb-1.5">
              Routing Plan
            </p>
            <div className="flex flex-wrap gap-1.5">
              {plan.map((p) => (
                <span
                  key={p}
                  className="rounded-full bg-blue-500/10 border border-blue-500/30 px-2 py-0.5 text-[10px] text-blue-400"
                >
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4 space-y-1 text-[10px] text-pearl-muted/50">
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-purple-400" />
            <span>Supervisor — 라우팅</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-blue-400" />
            <span>Domain Agent (8개) — 도구 실행</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-gold" />
            <span>Writer — 답변 작성</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-red-400" />
            <span>Critic — 답변 검수 (1~10점, 7점 미만 재작성)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
