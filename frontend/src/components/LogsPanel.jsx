import React from "react";
import { motion } from "framer-motion";

const LogsPanel = ({ logs = [] }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-card"
    >
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.35em] text-muted">Field logs</p>
        <h3 className="font-display text-xl text-foreground">Mission console</h3>
      </div>
      <div className="space-y-3 text-sm">
        {logs.length === 0 ? (
          <p className="text-muted">Awaiting telemetry...</p>
        ) : (
          logs.slice(0, 8).map((log) => (
            <div key={log.id} className="rounded-xl border border-white/10 bg-black/40 p-3 font-mono text-xs text-muted">
              <div className="flex items-center justify-between">
                <span className="uppercase tracking-[0.2em]">{log.level || "info"}</span>
                <span>{log.timestamp}</span>
              </div>
              <p className="mt-2 text-foreground">{log.message}</p>
            </div>
          ))
        )}
      </div>
    </motion.div>
  );
};

export default LogsPanel;
