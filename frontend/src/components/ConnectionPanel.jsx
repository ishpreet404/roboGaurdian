import React, { useState } from 'react';
import { useRobot } from '../context/RobotContext.jsx';
import { GlobeAltIcon } from '@heroicons/react/24/outline';

const ConnectionPanel = () => {
  const { piBaseUrl, setPiBaseUrl, windowsBaseUrl, setWindowsBaseUrl } = useRobot();
  const [piDraft, setPiDraft] = useState(piBaseUrl);
  const [winDraft, setWinDraft] = useState(windowsBaseUrl);

  const applyChanges = event => {
    event.preventDefault();
    setPiBaseUrl(piDraft.trim());
    setWindowsBaseUrl(winDraft.trim());
  };

  return (
    <form
      onSubmit={applyChanges}
      className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg"
    >
      <div className="mb-8 flex items-center gap-4">
        <div className="gradient-ring flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent border border-accent/20">
          <GlobeAltIcon className="h-6 w-6" />
        </div>
        <div>
          <h3 className="font-display text-2xl text-foreground">Connection Profiles</h3>
          <p className="text-sm text-muted">Configure API endpoints for Pi and Windows bridge</p>
        </div>
      </div>

      <div className="space-y-6">
        <label className="block">
          <span className="text-sm font-medium text-foreground mb-2 block">Raspberry Pi API Endpoint</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3.5 text-sm text-foreground placeholder-muted outline-none transition focus:border-accent focus:bg-white/10"
            value={piDraft}
            onChange={event => setPiDraft(event.target.value)}
            placeholder="http://192.168.x.x:5000"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-foreground mb-2 block">Windows Bridge API Endpoint</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3.5 text-sm text-foreground placeholder-muted outline-none transition focus:border-accent focus:bg-white/10"
            value={winDraft}
            onChange={event => setWinDraft(event.target.value)}
            placeholder="http://localhost:5050"
          />
        </label>
      </div>

      <div className="mt-8 flex items-center justify-end gap-3">
        <button
          type="submit"
          className="rounded-full bg-accent border border-accent/30 px-6 py-3 text-sm font-semibold text-white shadow-glow transition hover:bg-accent/90 hover:shadow-accent/25"
        >
          Apply Changes
        </button>
      </div>
    </form>
  );
};

export default ConnectionPanel;
