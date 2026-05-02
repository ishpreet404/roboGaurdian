import React, { useMemo } from "react";
import { motion } from "framer-motion";

const normalizePoints = (points) => {
  if (!points.length) {
    return {
      toPlot: () => ({ x: 50, y: 50 }),
    };
  }
  const xs = points.map((p) => p.x ?? 0);
  const ys = points.map((p) => p.y ?? 0);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;

  const toPlot = (p) => ({
    x: ((p.x - minX) / rangeX) * 100,
    y: 100 - ((p.y - minY) / rangeY) * 100,
  });

  return { toPlot, bounds: { minX, maxX, minY, maxY } };
};

const MapView = ({ path = [], victims = [], heading = 0 }) => {
  const { toPlot } = useMemo(() => normalizePoints(path), [path]);

  const pathD = useMemo(() => {
    if (!path.length || !toPlot) return "";
    return path
      .map((p, index) => {
        const point = toPlot(p);
        return `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`;
      })
      .join(" ");
  }, [path, toPlot]);

  const robot = path.length ? toPlot(path[path.length - 1]) : { x: 50, y: 50 };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-card"
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Mission map</p>
          <h3 className="font-display text-2xl text-foreground">Exploration trail</h3>
        </div>
        <span className="rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-[11px] uppercase tracking-[0.3em] text-accent">
          Heading {Math.round(heading)} deg
        </span>
      </div>

      <div className="relative h-72 rounded-2xl border border-white/10 bg-[#05070f]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(0,245,212,0.12),_transparent_60%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,_rgba(255,255,255,0.04)_1px,_transparent_1px),linear-gradient(to_bottom,_rgba(255,255,255,0.04)_1px,_transparent_1px)] bg-[size:24px_24px]" />
        <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="rgba(0,245,212,0.9)"
              strokeWidth="1.2"
            />
          )}
          {path.length > 0 && (
            <circle cx={robot.x} cy={robot.y} r="2.4" fill="#00f5d4" />
          )}
          {victims.map((victim, index) => {
            const point = toPlot({ x: victim.x, y: victim.y });
            return (
              <circle
                key={victim.id || index}
                cx={point.x}
                cy={point.y}
                r="2.8"
                fill="#ff7a18"
              />
            );
          })}
        </svg>
      </div>
    </motion.div>
  );
};

export default MapView;
