import React, { useMemo } from 'react';
import { PlayPauseIcon } from '@heroicons/react/24/outline';
import { useRobot } from '../context/RobotContext.jsx';

const VideoStream = () => {
  const { piBaseUrl } = useRobot();

  const videoSrc = useMemo(() => {
    const base = piBaseUrl.replace(/\/$/, '');
    return `${base}/video_feed?${Date.now()}`;
  }, [piBaseUrl]);

  return (
    <div className="relative overflow-hidden rounded-3xl border border-white/5 bg-[#090b1f] p-6 shadow-card">
      <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-accent/20 to-transparent" />
      <div className="relative flex items-center justify-between pb-6">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted mb-2">Live vision</p>
          <h3 className="font-display text-3xl text-foreground">Robot Camera Stream</h3>
        </div>
        <span className="flex items-center gap-3 rounded-full bg-success/20 border border-success/30 px-6 py-2 text-sm font-medium text-success">
          <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-success" /> Live Stream
        </span>
      </div>
      <div className="relative overflow-hidden rounded-[24px] border border-white/10 bg-black shadow-lg">
        <img
          src={videoSrc}
          alt="Pi camera stream"
          className="h-[480px] w-full object-cover"
          onError={event => {
            event.currentTarget.src = `https://dummyimage.com/1280x720/101225/ffffff&text=Stream+Offline`;
          }}
        />
        <button className="absolute bottom-6 right-6 flex items-center gap-2 rounded-full bg-black/40 border border-white/20 px-5 py-2.5 text-sm font-medium text-white backdrop-blur-sm transition hover:bg-black/60 hover:border-white/40">
          <PlayPauseIcon className="h-4 w-4" /> Refresh
        </button>
      </div>
    </div>
  );
};

export default VideoStream;
