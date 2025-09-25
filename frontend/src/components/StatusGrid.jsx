import React from 'react';
import {
  BoltIcon,
  CpuChipIcon,
  ClockIcon,
  SignalIcon,
  VideoCameraIcon,
  CommandLineIcon
} from '@heroicons/react/24/outline';
import StatCard from './StatCard.jsx';

const StatusGrid = ({ status }) => {
  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      <StatCard
        title="System Uptime"
        value={status.uptime}
        icon={ClockIcon}
        tone="info"
        description={`Voice assistant ready: ${status.voiceReady ? 'Yes' : 'No'}`}
      />
      <StatCard
        title="UART Link"
        value={status.uart}
        icon={SignalIcon}
        tone={status.uart?.includes('✅') ? 'success' : 'warning'}
        description={`Last command: ${status.lastCommand} → ${status.lastCommandTime}`}
      />
      <StatCard
        title="Camera Stream"
        value={status.camera}
        icon={VideoCameraIcon}
        tone={status.camera?.includes('✅') ? 'success' : 'danger'}
        description={`Frames served: ${status.framesServed}`}
      />
      <StatCard
        title="System Load"
        value={status.cpu}
        icon={CpuChipIcon}
        tone="warning"
        description={`Memory usage: ${status.memory}`}
      />
      <StatCard
        title="Thermal Status"
        value={status.temperature}
        icon={BoltIcon}
        tone={status.temperature?.startsWith('⚠️') ? 'danger' : 'info'}
        description="Auto polling every 7 seconds"
      />
      <StatCard
        title="Commands Sent"
        value={status.commands}
        icon={CommandLineIcon}
        tone="accent"
        description="Includes manual and autonomous maneuvers"
      />
    </div>
  );
};

export default StatusGrid;
