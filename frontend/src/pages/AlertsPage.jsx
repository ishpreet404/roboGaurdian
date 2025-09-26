import React, { useMemo } from 'react';
import { useRobotStatus } from '../hooks/useRobotStatus.js';
import { useAssistant } from '../hooks/useAssistant.js';
import AlertFeed from '../components/AlertFeed.jsx';
import LogTimeline from '../components/LogTimeline.jsx';
import AssistantConsole from '../components/AssistantConsole.jsx';

const AlertsPage = () => {
  const { status } = useRobotStatus(10000);
  const {
    messages,
    sendMessage,
    sending,
    error,
    voiceReady,
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

      <div className="xl:col-span-2">
        <LogTimeline events={timeline} />
      </div>
    </div>
  );
};

export default AlertsPage;
