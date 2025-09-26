import React, { useMemo } from 'react';
import { useRobotStatus } from '../hooks/useRobotStatus.js';
import { useAssistant } from '../hooks/useAssistant.js';
import AlertFeed from '../components/AlertFeed.jsx';
import LogTimeline from '../components/LogTimeline.jsx';
import AssistantConsole from '../components/AssistantConsole.jsx';
import AssistantReminders from '../components/AssistantReminders.jsx';

const AlertsPage = () => {
  const { status } = useRobotStatus(10000);
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
    <div className="grid gap-8 xl:grid-cols-[1.2fr,1fr]">
      <div className="space-y-8">
        <AlertFeed alerts={status.alerts} />
        <AssistantConsole
          messages={messages}
          onSend={sendMessage}
          sending={sending}
          error={error}
          voiceReady={voiceReady || status.voiceReady}
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

      <div className="space-y-8">
        <AssistantReminders
          reminders={reminders}
          onCreate={addReminder}
          onDelete={deleteReminder}
          loading={loadingReminders}
        />
        <div className="rounded-3xl border border-white/5 bg-[#0d1023]/70 p-8 shadow-card backdrop-blur-lg">
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Assistant presence</p>
          <h3 className="mt-1 font-display text-2xl text-foreground">Voice Companion</h3>
          <p className="mt-4 text-sm text-muted">
            The Raspberry Pi voice assistant "Chirpy" now accepts dashboard commands, schedules Hindi voice note reminders, and replays them automatically on the Pi speaker. Keep the device powered for timely alerts.
          </p>
        </div>
      </div>

      <div className="xl:col-span-2">
        <LogTimeline events={timeline} />
      </div>
    </div>
  );
};

export default AlertsPage;
