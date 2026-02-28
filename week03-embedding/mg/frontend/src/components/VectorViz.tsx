"use client";

import { useState } from "react";
import type { VizData, ScoredChunk } from "@/types/vector";

interface VectorVizProps {
  vizData: VizData;
  usedChunks: ScoredChunk[];
}

const SVG_SIZE = 400;
const PADDING = 30;
const INNER = SVG_SIZE - 2 * PADDING;

function starPoints(
  cx: number,
  cy: number,
  outerR: number,
  innerR: number
): string {
  const pts: string[] = [];
  for (let i = 0; i < 10; i++) {
    const angle = (Math.PI / 5) * i - Math.PI / 2;
    const r = i % 2 === 0 ? outerR : innerR;
    pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
  }
  return pts.join(" ");
}

export default function VectorViz({ vizData, usedChunks }: VectorVizProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const usedIndices = new Set(usedChunks.map((c) => c.index));
  const usedScoreMap = new Map(usedChunks.map((c) => [c.index, c.score]));

  return (
    <div className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xs font-medium tracking-widest uppercase text-pearl-dim">
          임베딩 2D 시각화
        </h2>
        <div className="flex items-center gap-4 text-[10px] text-pearl-muted">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full bg-pearl-muted/40" />
            청크
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-gold" />
            검색됨
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-gold">★</span>
            질문
          </span>
        </div>
      </div>
      <div className="flex justify-center">
        <svg
          viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`}
          className="w-full max-w-md rounded-xl"
          style={{ background: "var(--color-base-100)" }}
        >
          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map((t) => (
            <g key={t} opacity={0.15}>
              <line
                x1={PADDING + t * INNER}
                y1={PADDING}
                x2={PADDING + t * INNER}
                y2={PADDING + INNER}
                stroke="var(--color-stroke)"
                strokeDasharray="4 4"
              />
              <line
                x1={PADDING}
                y1={PADDING + t * INNER}
                x2={PADDING + INNER}
                y2={PADDING + t * INNER}
                stroke="var(--color-stroke)"
                strokeDasharray="4 4"
              />
            </g>
          ))}

          {/* Chunk dots */}
          {vizData.points.map((p) => {
            const cx = PADDING + p.x * INNER;
            const cy = PADDING + p.y * INNER;
            const isUsed = usedIndices.has(p.index);
            const isHovered = hoveredIndex === p.index;

            return (
              <g key={p.index}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={isUsed ? 8 : 5}
                  fill={
                    isUsed
                      ? "var(--color-gold)"
                      : "var(--color-pearl-muted)"
                  }
                  opacity={isUsed ? 0.9 : 0.4}
                  stroke={isHovered ? "var(--color-pearl)" : "none"}
                  strokeWidth={2}
                  onMouseEnter={() => setHoveredIndex(p.index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                  style={{ cursor: "pointer", transition: "all 0.2s" }}
                />
                {(isUsed || isHovered) && (
                  <text
                    x={cx}
                    y={cy + (isUsed ? 18 : 14)}
                    textAnchor="middle"
                    fill={
                      isUsed
                        ? "var(--color-gold)"
                        : "var(--color-pearl-muted)"
                    }
                    fontSize={9}
                  >
                    #{p.index + 1}
                    {isUsed &&
                      usedScoreMap.has(p.index) &&
                      ` (${((usedScoreMap.get(p.index) ?? 0) * 100).toFixed(0)}%)`}
                  </text>
                )}
              </g>
            );
          })}

          {/* Query star */}
          {vizData.query_point && (
            <g>
              <polygon
                points={starPoints(
                  PADDING + vizData.query_point.x * INNER,
                  PADDING + vizData.query_point.y * INNER,
                  12,
                  5
                )}
                fill="var(--color-gold)"
                stroke="var(--color-pearl)"
                strokeWidth={1}
                opacity={0.95}
              />
              <text
                x={PADDING + vizData.query_point.x * INNER}
                y={PADDING + vizData.query_point.y * INNER + 20}
                textAnchor="middle"
                fill="var(--color-gold)"
                fontSize={10}
                fontWeight="bold"
              >
                Query
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Hover tooltip */}
      {hoveredIndex !== null && (
        <div className="mt-3 rounded-lg border border-stroke bg-base-100 px-3 py-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-medium text-pearl-dim">
              청크 #{hoveredIndex + 1}
            </span>
            {usedScoreMap.has(hoveredIndex) && (
              <span className="text-[10px] text-gold">
                유사도{" "}
                {((usedScoreMap.get(hoveredIndex) ?? 0) * 100).toFixed(1)}%
              </span>
            )}
          </div>
          <p className="mt-1 text-xs leading-relaxed text-pearl-dim">
            {vizData.points.find((p) => p.index === hoveredIndex)
              ?.text_preview ?? ""}
            ...
          </p>
        </div>
      )}
    </div>
  );
}
