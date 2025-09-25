import React, { useMemo } from 'react';
import { useRobotStatus } from '../hooks/useRobotStatus.js';
import AlertFeed from '../components/AlertFeed.jsx';
import LogTimeline from '../components/LogTimeline.jsx';

const AlertsPage = () => {
  const { status } = useRobotStatus(10000);

  const timeline = useMemo(() => {
    if (!status.alerts?.length) return [];
    return status.alerts.map((alert, index) => ({
      id: alert.id || `${alert.timestamp}-${index}`,
      timestamp: alert.timestamp || 'Just now',
      title: alert.title || 'Alert',
      details: alert.message || alert.details,
      level: alert.level || 'info'
    }));
  }, [status.alerts]);

  return (
    <div className="grid gap-8 lg:grid-cols-[1.2fr,1fr]">
      <AlertFeed alerts={status.alerts} />
      <div className="rounded-3xl border border-white/5 bg-[#0d1023]/70 p-8 shadow-card backdrop-blur-lg">
        <p className="text-xs uppercase tracking-[0.35em] text-muted">Assistant presence</p>
        <h3 className="mt-1 font-display text-2xl text-foreground">Voice Companion</h3>
        <p className="mt-4 text-sm text-muted">
          The Raspberry Pi voice assistant "Chirpy" offers proactive support in natural Hindi. Keep the Pi speaker nearby for immediate alerts and acknowledgements. Voice status: {status.voiceReady ? 'Ready' : 'Booting'}.
        </p>
      </div>
      <div className="lg:col-span-2">
        <LogTimeline events={timeline} />
      </div>
    </div>
  );
};

export default AlertsPage;
