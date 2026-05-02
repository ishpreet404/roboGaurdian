import React from "react";
import { motion } from "framer-motion";

const toneMap = {
  info: "text-info border-info/40 bg-info/10",
  warning: "text-warning border-warning/40 bg-warning/10",
  danger: "text-danger border-danger/40 bg-danger/10",
  success: "text-success border-success/40 bg-success/10",
};

const AlertsBar = ({ alerts = [] }) => {
  const active = alerts.slice(0, 3);
  return (
    <div className="flex flex-wrap items-center gap-3">
      {active.length === 0 ? (
        <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.32em] text-muted">
          No active alerts
        </div>
      ) : (
        active.map((alert, idx) => (
          <motion.div
            key={alert.id || idx}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-full border px-4 py-2 text-xs uppercase tracking-[0.25em] ${toneMap[alert.level] || toneMap.warning}`}
          >
            {alert.message}
          </motion.div>
        ))
      )}
    </div>
  );
};

export default AlertsBar;
