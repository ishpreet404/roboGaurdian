import React from "react";
import { motion } from "framer-motion";

const buttonStyles =
  "rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold uppercase tracking-[0.2em] text-foreground transition hover:border-accent hover:bg-accent/10";

const Controls = ({ onCommand, disabled }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-card"
    >
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.35em] text-muted">Manual override</p>
        <h3 className="font-display text-xl text-foreground">Control array</h3>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div />
        <button
          type="button"
          className={buttonStyles}
          disabled={disabled}
          onClick={() => onCommand("forward")}
        >
          Forward
        </button>
        <div />
        <button
          type="button"
          className={buttonStyles}
          disabled={disabled}
          onClick={() => onCommand("left")}
        >
          Left
        </button>
        <button
          type="button"
          className={`${buttonStyles} border-danger/40 text-danger hover:border-danger hover:bg-danger/10`}
          disabled={disabled}
          onClick={() => onCommand("stop")}
        >
          Stop
        </button>
        <button
          type="button"
          className={buttonStyles}
          disabled={disabled}
          onClick={() => onCommand("right")}
        >
          Right
        </button>
        <div />
        <button
          type="button"
          className={buttonStyles}
          disabled={disabled}
          onClick={() => onCommand("backward")}
        >
          Reverse
        </button>
        <div />
      </div>
    </motion.div>
  );
};

export default Controls;
