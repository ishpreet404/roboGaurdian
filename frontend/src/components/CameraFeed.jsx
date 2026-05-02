import React from "react";
import { motion } from "framer-motion";

const CameraFeed = ({ src }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-card"
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Live camera</p>
          <h3 className="font-display text-xl text-foreground">Hazard feed</h3>
        </div>
        <span className="rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-[11px] uppercase tracking-[0.3em] text-accent">
          MJPEG
        </span>
      </div>
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/40">
        {src ? (
          <img
            src={src}
            alt="Rover camera feed"
            className="h-56 w-full object-cover"
          />
        ) : (
          <div className="flex h-56 items-center justify-center text-sm text-muted">
            Camera stream offline
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default CameraFeed;
