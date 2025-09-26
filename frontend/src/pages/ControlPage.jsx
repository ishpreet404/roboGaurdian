import React from 'react';
import CommandPad from '../components/CommandPad.jsx';
import AudioChat from '../components/AudioChat.jsx';
import { useRobotStatus } from '../hooks/useRobotStatus.js';
import { useRobot } from '../context/RobotContext.jsx';

const ControlPage = () => {
  const { status } = useRobotStatus(10000);
  const { piBaseUrl } = useRobot();

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr,1fr]">
      <div className="space-y-8">
        <div className="rounded-3xl border border-white/5 bg-[#0d1023]/75 p-8 shadow-card backdrop-blur-lg">
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Control overview</p>
          <h2 className="mt-1 font-display text-3xl text-foreground">Manual & Assisted Control</h2>
          <p className="mt-3 text-sm text-muted">
            Engage manual drive, send precision maneuvers, or switch into assisted tracking modes. Commands are relayed to the Raspberry Pi via the local network.
          </p>
          <dl className="mt-6 grid gap-4 text-sm text-muted sm:grid-cols-2">
            <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <dt className="uppercase tracking-[0.25em] text-xs">Pi endpoint</dt>
              <dd className="mt-2 break-words font-medium text-foreground">{piBaseUrl}</dd>
            </div>
            <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <dt className="uppercase tracking-[0.25em] text-xs">Camera status</dt>
              <dd className="mt-2 font-medium text-foreground">{status.camera}</dd>
            </div>
            <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <dt className="uppercase tracking-[0.25em] text-xs">UART link</dt>
              <dd className="mt-2 font-medium text-foreground">{status.uart}</dd>
            </div>
            <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <dt className="uppercase tracking-[0.25em] text-xs">Voice assistant</dt>
              <dd className="mt-2 font-medium text-foreground">
                {status.voiceReady ? 'Ready to assist' : 'Initialising'}
              </dd>
            </div>
          </dl>
        </div>
        <CommandPad />
        <AudioChat />
      </div>

      <div className="space-y-8">
        <div className="rounded-3xl border border-white/5 bg-[#0d1023]/70 p-8 shadow-card backdrop-blur-lg">
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Safety assists</p>
          <h3 className="mt-1 font-display text-2xl text-foreground">Smart maneuvers</h3>
          <ul className="mt-5 space-y-4 text-sm text-muted">
            <li className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <span className="font-semibold text-foreground">Autonomous follow</span>
              <p className="mt-2">
                When enabled in the Windows Control Center, the robot will auto-follow the largest detected person while respecting safety stops.
              </p>
            </li>
            <li className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <span className="font-semibold text-foreground">Crying detection alerts</span>
              <p className="mt-2">
                Audio and visual cues trigger alerts that appear within the Alert Center to spotlight potential distress.
              </p>
            </li>
            <li className="rounded-2xl border border-white/5 bg-white/5 p-4">
              <span className="font-semibold text-foreground">Emergency stop</span>
              <p className="mt-2">
                The stop button issues a high-priority S command to halt all motors instantly via UART.
              </p>
            </li>
            <li className="rounded-2xl border border-success/30 bg-success/10 p-4">
              <span className="font-semibold text-success">🎤 Audio Chat</span>
              <p className="mt-2 text-success/90">
                Record voice messages from your laptop microphone and send them directly to the Pi speaker for real-time communication.
              </p>
            </li>
            <li className="rounded-2xl border border-accent/30 bg-accent/10 p-4">
              <span className="font-semibold text-accent">🔊 Hindi TTS</span>
              <p className="mt-2 text-accent/90">
                Enhanced text-to-speech system with smooth Hindi voice support using gTTS, with offline pyttsx3 and espeak fallbacks.
              </p>
            </li>
            <li className="rounded-2xl border border-warning/30 bg-warning/10 p-4">
              <span className="font-semibold text-warning">⏰ Smart Reminders</span>
              <p className="mt-2 text-warning/90">
                Intelligent reminder system with detailed logging and voice announcements through the Pi speaker.
              </p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ControlPage;
