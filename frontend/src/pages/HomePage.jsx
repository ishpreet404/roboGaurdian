import React from 'react';
import { useRobotStatus } from '../hooks/useRobotStatus.js';
import StatusGrid from '../components/StatusGrid.jsx';
import VideoStream from '../components/VideoStream.jsx';
import ConnectionPanel from '../components/ConnectionPanel.jsx';

const HomePage = () => {
  const { status, loading, error, refresh } = useRobotStatus();

  return (
    <div className="space-y-10">
      <section className="grid gap-8 lg:grid-cols-[2fr,1.2fr]">
        <VideoStream />
        <div className="space-y-8">
          <ConnectionPanel />
          <div className="rounded-3xl border border-white/5 bg-[#0d1023]/75 p-8 shadow-card backdrop-blur-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-muted">Live status</p>
                <h2 className="font-display text-2xl text-foreground">Robot Health Snapshot</h2>
              </div>
              <button
                onClick={refresh}
                className="rounded-full bg-white/10 px-4 py-2 text-xs font-semibold text-white transition hover:bg-accent/80"
              >
                Refresh now
              </button>
            </div>
            {loading ? (
              <p className="mt-6 animate-pulse text-sm text-muted">Fetching telemetry…</p>
            ) : error ? (
              <p className="mt-6 text-sm text-danger">{error}</p>
            ) : (
              <div className="mt-6">
                <StatusGrid status={status} />
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
