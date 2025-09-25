import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const AlertFeed = ({ alerts = [] }) => {
  return (
    <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
      <div className="mb-6 flex items-center gap-3">
        <div className="gradient-ring flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5 text-danger">
          <ExclamationTriangleIcon className="h-6 w-6" />
        </div>
        <div>
          <h3 className="font-display text-xl text-foreground">Alert Center</h3>
          <p className="text-sm text-muted">Critical events and safety notifications</p>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {alerts.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-center text-muted"
          >
            All clear. No alerts from the robot.
          </motion.div>
        ) : (
          <div className="space-y-3">
            {alerts.map(alert => (
              <motion.div
                key={alert.id || alert.timestamp}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                className="flex items-start justify-between gap-6 rounded-2xl border border-white/5 bg-[#151835]/80 p-5"
              >
                <div>
                  <p className="font-medium text-foreground">{alert.title}</p>
                  <p className="text-sm text-muted">{alert.message}</p>
                </div>
                <p className="text-xs text-muted">{alert.timestamp}</p>
              </motion.div>
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AlertFeed;
