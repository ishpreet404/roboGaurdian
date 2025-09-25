import React from 'react';
import { useRobotStatus } from '../hooks/useRobotStatus.js';
import StatusGrid from '../components/StatusGrid.jsx';
import VideoStream from '../components/VideoStream.jsx';
import ConnectionPanel from '../components/ConnectionPanel.jsx';

const HomePage = () => {
  const { status, loading, error, refresh } = useRobotStatus();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0b1f] via-[#111225] to-[#1a1b2f] px-6 py-12">
      <div className="mx-auto max-w-7xl space-y-12">
        {/* Header Section */}
        <div className="text-center">
          <h1 className="font-display text-4xl font-bold text-foreground mb-4">
            Robot Command Center
          </h1>
          <p className="text-lg text-muted max-w-2xl mx-auto">
            Monitor your robot guardian in real-time with live telemetry, camera feed, and system diagnostics.
          </p>
        </div>

        {/* Main Dashboard Grid */}
        <section className="grid gap-12 xl:grid-cols-[1.8fr,1.2fr]">
          {/* Left Column - Video Stream */}
          <div className="space-y-8">
            <VideoStream />
            
            {/* Status Overview - Full Width on Large Screens */}
            <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-muted mb-2">System telemetry</p>
                  <h2 className="font-display text-3xl text-foreground">Robot Health Dashboard</h2>
                </div>
                <button
                  onClick={refresh}
                  className="rounded-full bg-accent/20 border border-accent/30 px-6 py-3 text-sm font-semibold text-accent transition hover:bg-accent hover:text-white shadow-glow"
                >
                  Refresh Status
                </button>
              </div>
              {loading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mx-auto mb-4"></div>
                    <p className="text-sm text-muted">Fetching telemetry data…</p>
                  </div>
                </div>
              ) : error ? (
                <div className="rounded-2xl bg-danger/10 border border-danger/20 p-6 text-center">
                  <p className="text-danger font-medium">{error}</p>
                  <button 
                    onClick={refresh}
                    className="mt-3 text-sm text-danger hover:text-danger/80 underline"
                  >
                    Try Again
                  </button>
                </div>
              ) : (
                <StatusGrid status={status} />
              )}
            </div>
          </div>

          {/* Right Column - Connection Panel */}
          <div className="space-y-8">
            <ConnectionPanel />
            
            {/* Quick Actions Panel */}
            <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
              <h3 className="font-display text-2xl text-foreground mb-6">Quick Actions</h3>
              <div className="space-y-4">
                <button className="w-full rounded-2xl bg-accent/10 border border-accent/20 p-4 text-left transition hover:bg-accent/20 hover:border-accent/40">
                  <div className="font-semibold text-accent mb-1">Voice Commands</div>
                  <div className="text-sm text-muted">Test Hindi voice assistant</div>
                </button>
                <button className="w-full rounded-2xl bg-success/10 border border-success/20 p-4 text-left transition hover:bg-success/20 hover:border-success/40">
                  <div className="font-semibold text-success mb-1">System Diagnostics</div>
                  <div className="text-sm text-muted">Run comprehensive system check</div>
                </button>
                <button className="w-full rounded-2xl bg-warning/10 border border-warning/20 p-4 text-left transition hover:bg-warning/20 hover:border-warning/40">
                  <div className="font-semibold text-warning mb-1">Emergency Stop</div>
                  <div className="text-sm text-muted">Halt all robot operations</div>
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default HomePage;
