import React from "react";
import AlertsBar from "./components/AlertsBar.jsx";
import CameraFeed from "./components/CameraFeed.jsx";
import Controls from "./components/Controls.jsx";
import LogsPanel from "./components/LogsPanel.jsx";
import MapView from "./components/MapView.jsx";
import TelemetryPanel from "./components/TelemetryPanel.jsx";
import { useMissionSocket } from "./hooks/useMissionSocket.js";

const App = () => {
  const { state, telemetry, connected, sendCommand, httpBase } = useMissionSocket();
  const heading = telemetry?.imu?.yaw_deg ?? telemetry?.pose?.heading_deg ?? 0;
  const cameraSrc = `${httpBase.replace(/\/$/, "")}/camera/stream`;

  return (
    <div className="min-h-screen bg-surface text-foreground">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(0,245,212,0.15),_transparent_60%)]" />
      <div className="absolute inset-0 opacity-30 mix-blend-screen bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col gap-8 px-6 py-10">
        <header className="flex flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-card">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.45em] text-muted">Disaster rescue rover</p>
              <h1 className="font-display text-3xl text-foreground">Mission Control</h1>
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full border px-4 py-2 text-xs uppercase tracking-[0.3em] ${connected ? "border-success/50 bg-success/10 text-success" : "border-warning/50 bg-warning/10 text-warning"}`}>
                {connected ? "Link active" : "Link offline"}
              </span>
              <span className="rounded-full border border-accent/40 bg-accent/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-accent">
                {telemetry?.system?.mode || "auto"}
              </span>
            </div>
          </div>
          <AlertsBar alerts={state.alerts} />
        </header>

        <section className="grid gap-6 lg:grid-cols-[2fr,1fr]">
          <MapView path={state.path} victims={state.victims} heading={heading} />
          <div className="flex flex-col gap-6">
            <CameraFeed src={cameraSrc} />
            <Controls onCommand={sendCommand} disabled={!connected} />
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[2fr,1fr]">
          <TelemetryPanel telemetry={telemetry} />
          <LogsPanel logs={state.logs} />
        </section>
      </div>
    </div>
  );
};

export default App;
