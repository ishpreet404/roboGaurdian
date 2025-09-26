import React, { useMemo } from 'react';
import { useRobotStatus } from '../hooks/useRobotStatus.js';
import AlertFeed from '../components/AlertFeed.jsx';
import LogTimeline from '../components/LogTimeline.jsx';

const AlertsPage = () => {
  const { status } = useRobotStatus(10000);

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
    <div className="space-y-8">
      <AlertFeed alerts={status.alerts} />
      <LogTimeline events={timeline} />
    </div>
  );
};

export default AlertsPage;
