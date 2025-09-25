import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useRobotCommands } from '../hooks/useRobotCommands.js';
import {
  ArrowDownCircleIcon,
  ArrowLeftCircleIcon,
  ArrowRightCircleIcon,
  ArrowUpCircleIcon,
  HandRaisedIcon
} from '@heroicons/react/24/outline';

const buttonClasses =
  'flex h-24 flex-col items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/10 text-sm font-medium text-muted transition-all hover:-translate-y-1 hover:border-accent hover:bg-accent/30 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-[#0d1023] disabled:cursor-not-allowed disabled:opacity-60';

const CommandPad = () => {
  const { sendCommand, isSending, lastResult } = useRobotCommands();

  return (
    <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-xl">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="font-display text-xl text-foreground">Manual Controls</h3>
        <span className="text-xs uppercase tracking-[0.25em] text-muted">
          {isSending ? 'Sending…' : 'Ready'}
        </span>
      </div>

      <AnimatePresence>
        {lastResult && (
          <motion.div
            key={lastResult.success ? 'success' : 'error'}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className={`mb-5 rounded-2xl border px-4 py-3 text-sm ${
              lastResult.success
                ? 'border-success/30 bg-success/10 text-success'
                : 'border-danger/30 bg-danger/10 text-danger'
            }`}
          >
            {lastResult.success ? 'Command dispatched to robot.' : 'Command failed. Check the bridge logs.'}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mx-auto mt-4 grid max-w-xl grid-cols-3 gap-4">
        <div aria-hidden className="h-24" />
        <motion.button
          whileTap={{ scale: 0.96 }}
          disabled={isSending}
          className={buttonClasses}
          onClick={() => sendCommand('forward')}
          aria-label="Move forward"
        >
          <ArrowUpCircleIcon className="h-8 w-8 text-info" />
          Forward
        </motion.button>
        <div aria-hidden className="h-24" />

        <motion.button
          whileTap={{ scale: 0.96 }}
          disabled={isSending}
          className={buttonClasses}
          onClick={() => sendCommand('left')}
          aria-label="Turn left"
        >
          <ArrowLeftCircleIcon className="h-8 w-8 text-info" />
          Left
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.96 }}
          disabled={isSending}
          className={`${buttonClasses} border-warning/40 bg-warning/10 text-warning hover:bg-warning/40 hover:text-[#0d1023]`}
          onClick={() => sendCommand('stop')}
          aria-label="Emergency stop"
        >
          <HandRaisedIcon className="h-8 w-8" />
          Stop
        </motion.button>

        <motion.button
          whileTap={{ scale: 0.96 }}
          disabled={isSending}
          className={buttonClasses}
          onClick={() => sendCommand('right')}
          aria-label="Turn right"
        >
          <ArrowRightCircleIcon className="h-8 w-8 text-info" />
          Right
        </motion.button>

        <div aria-hidden className="h-24" />
        <motion.button
          whileTap={{ scale: 0.96 }}
          disabled={isSending}
          className={buttonClasses}
          onClick={() => sendCommand('backward')}
          aria-label="Move backward"
        >
          <ArrowDownCircleIcon className="h-8 w-8 text-info" />
          Reverse
        </motion.button>
        <div aria-hidden className="h-24" />
      </div>
    </div>
  );
};

export default CommandPad;
