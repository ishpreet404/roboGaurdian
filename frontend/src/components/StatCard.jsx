import React from 'react';
import { motion } from 'framer-motion';

const variants = {
  initial: { opacity: 0, y: 16, scale: 0.97 },
  animate: { opacity: 1, y: 0, scale: 1 }
};

const gradientMap = {
  success: 'from-green-500/20 via-green-500/5 to-transparent',
  warning: 'from-yellow-500/20 via-yellow-500/5 to-transparent',
  danger: 'from-rose-500/20 via-rose-500/5 to-transparent',
  info: 'from-sky-500/20 via-sky-500/5 to-transparent',
  accent: 'from-accent/30 via-accent/10 to-transparent'
};

const normalizeValue = raw => {
  if (raw === null || raw === undefined) return '—';
  if (typeof raw === 'number') return raw.toLocaleString();

  const trimmed = String(raw).trim();
  if (!trimmed) return '—';

  const lowered = trimmed.toLowerCase();
  if (['unknown', 'undefined', 'offline', 'n/a'].includes(lowered)) {
    return 'Unknown';
  }

  return trimmed;
};

const StatCard = ({ title, value, icon: Icon, tone = 'accent', description }) => {
  const gradient = gradientMap[tone] ?? gradientMap.accent;
  const displayValue = normalizeValue(value);
  const isCompact = typeof displayValue === 'string' && displayValue.length > 10;

  return (
    <motion.div
      initial="initial"
      animate="animate"
      variants={variants}
      transition={{ type: 'spring', stiffness: 130, damping: 18 }}
      className={`relative overflow-hidden rounded-3xl border border-white/5 bg-[#0d1023]/70 p-6 shadow-card backdrop-blur-lg`}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient}`} />
      <div className="relative flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-[0.35em] text-muted">{title}</p>
          <p
            className={`font-display font-semibold text-foreground ${
              isCompact ? 'text-2xl leading-tight' : 'text-3xl'
            }`}
          >
            {displayValue}
          </p>
        </div>
        {Icon && (
          <div className="gradient-ring flex h-12 w-12 items-center justify-center rounded-2xl bg-white/5 text-accent">
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
      {description && <p className="mt-4 text-sm text-muted">{description}</p>}
    </motion.div>
  );
};

export default StatCard;
