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
      <div className="mb-6 flex items-center gap-3">
        <div className="gradient-ring flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5 text-info">
          <GlobeAltIcon className="h-6 w-6" />
        </div>
        <div>
          <h3 className="font-display text-xl text-foreground">Connection Profiles</h3>
          <p className="text-sm text-muted">Configure API endpoints for Pi and Windows bridge</p>
        </div>
      </div>

      <div className="space-y-4">
        <label className="block text-sm text-muted">
          Raspberry Pi API
          <input
            className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground outline-none transition focus:border-accent"
            value={piDraft}
            onChange={event => setPiDraft(event.target.value)}
            placeholder="http://192.168.x.x:5000"
          />
        </label>
        <label className="block text-sm text-muted">
          Windows Bridge API
          <input
            className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground outline-none transition focus:border-accent"
            value={winDraft}
            onChange={event => setWinDraft(event.target.value)}
            placeholder="http://localhost:5050"
          />
        </label>
      </div>

      <div className="mt-6 flex items-center justify-end gap-3">
        <button
          type="submit"
          className="rounded-full bg-accent px-5 py-2 text-sm font-semibold text-white shadow-glow transition hover:bg-accentSoft"
        >
          Apply Changes
        </button>
      </div>
    </form>
  );
};

export default ConnectionPanel;
