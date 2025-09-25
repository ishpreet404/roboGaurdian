import React from 'react';
import { motion } from 'framer-motion';

const LogTimeline = ({ events = [] }) => {
  if (!events.length) {
    return null;
  }

  return (
    <div className="mt-10 rounded-3xl border border-white/5 bg-[#0d1023]/70 p-8 shadow-card backdrop-blur-lg">
      <p className="text-xs uppercase tracking-[0.35em] text-muted">Recent activity</p>
      <h3 className="mt-1 font-display text-2xl text-foreground">Event Timeline</h3>

      <ul className="mt-6 space-y-5 border-l border-white/5 pl-6">
        {events.map((event, index) => (
          <motion.li
            key={event.id || event.timestamp || index}
            initial={{ opacity: 0, x: -18 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="relative"
          >
            <span className="absolute -left-[30px] top-2 h-2 w-2 rounded-full bg-accent" />
            <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <div className="flex items-center justify-between text-sm text-muted">
                <span>{event.timestamp}</span>
                <span className="rounded-full bg-accent/15 px-3 py-0.5 text-xs text-accent">
                  {event.level || 'info'}
                </span>
              </div>
              <p className="mt-3 font-medium text-foreground">{event.title}</p>
              <p className="mt-1 text-sm text-muted">{event.details}</p>
            </div>
          </motion.li>
        ))}
      </ul>
    </div>
  );
};

export default LogTimeline;
