import React, { useState, useEffect } from 'react';
import { useRobot } from '../context/RobotContext.jsx';
import { useAssistant } from '../hooks/useAssistant.js';
import AssistantConsole from '../components/AssistantConsole.jsx';
import AssistantReminders from '../components/AssistantReminders.jsx';

const AssistantPage = () => {
  const { windowsBaseUrl } = useRobot();
  const {
    messages,
    sendMessage,
    sending,
    error,
    voiceReady,
    reminders,
    loadingReminders,
    addReminder,
    deleteReminder,
    operatingMode,
    modeMetadata,
    availableModes,
    watchdogAlarmActive,
    updatingMode,
    modeError,
    setMode,
    silenceWatchdogAlarm,
  } = useAssistant();

  const [loading, setLoading] = useState(false);

  // Load initial data
  useEffect(() => {
    checkVoiceStatus();
  }, []);

  const checkVoiceStatus = async () => {
    try {
      const response = await fetch(`${windowsBaseUrl}/api/status`);
      const data = await response.json();
      setVoiceReady(data.pi_connected && data.voice_ready);
    } catch (err) {
      console.error('Failed to check voice status:', err);
      setVoiceReady(false);
    }
  };

  // All reminder and message functions are now provided by useAssistant hook

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0b1f] via-[#111225] to-[#1a1b2f] px-6 py-12">
      <div className="mx-auto max-w-7xl space-y-12">
        {/* Header Section */}
        <div className="text-center">
          <h1 className="font-display text-4xl font-bold text-foreground mb-4">
            🤖 Voice Assistant & Reminder Center
          </h1>
          <p className="text-lg text-muted max-w-2xl mx-auto">
            Send Hindi voice commands and schedule smart reminders 
            that play automatically through the Pi speaker.
          </p>
        </div>

        {/* Main Features Grid */}
        <section className="grid gap-8 xl:grid-cols-[1fr,1fr]">
          {/* Left Column - Voice Assistant */}
          <div className="space-y-8">
            <AssistantConsole
              messages={messages}
              onSend={sendMessage}
              sending={sending}
              error={error}
              voiceReady={voiceReady}
              mode={operatingMode}
              modeMetadata={modeMetadata}
              availableModes={availableModes}
              onModeSelect={setMode}
              updatingMode={updatingMode}
              modeError={modeError}
              watchdogAlarmActive={watchdogAlarmActive}
              onSilenceAlarm={silenceWatchdogAlarm}
            />
          </div>

          {/* Right Column - Smart Reminders */}
          <div className="space-y-8">
            <AssistantReminders
              reminders={reminders}
              onCreate={addReminder}
              onDelete={deleteReminder}
              loading={loadingReminders}
            />

            {/* Voice Companion */}
            <div className="rounded-3xl border border-white/5 bg-[#0d1023]/70 p-8 shadow-card backdrop-blur-lg">
              <div className="mb-6 flex items-center gap-4">
                <div className="gradient-ring flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent border border-accent/20">
                  🤖
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.35em] text-muted">Assistant presence</p>
                  <h3 className="font-display text-2xl text-foreground">Voice Companion "Chirpy"</h3>
                </div>
              </div>
              <p className="text-sm text-muted">
                The Raspberry Pi voice assistant "Chirpy" now accepts dashboard commands, schedules Hindi voice note reminders, and replays them automatically on the Pi speaker. Keep the device powered for timely alerts.
              </p>
            </div>

            {/* Feature Overview */}
            <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
              <h3 className="font-display text-2xl text-foreground mb-6">🎯 Assistant Features</h3>
              <div className="space-y-4 text-sm">
                <div className="rounded-2xl border border-success/20 bg-success/10 p-4">
                  <div className="font-semibold text-success mb-2">🔊 Multi-Engine Hindi TTS</div>
                  <p className="text-success/80">Enhanced text-to-speech with gTTS for quality, pyttsx3 for offline use, and espeak as fallback.</p>
                </div>
                <div className="rounded-2xl border border-warning/20 bg-warning/10 p-4">
                  <div className="font-semibold text-warning mb-2">⏰ Smart Reminder System</div>
                  <p className="text-warning/80">Schedule voice reminders with detailed logging and automatic delivery through the Pi speaker.</p>
                </div>
                <div className="rounded-2xl border border-purple-500/20 bg-purple-500/10 p-4">
                  <div className="font-semibold text-purple-400 mb-2">🌐 Cross-Platform Integration</div>
                  <p className="text-purple-300/80">Seamless communication between Windows laptop and Raspberry Pi through network API.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AssistantPage;