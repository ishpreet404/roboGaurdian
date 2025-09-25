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
    <div className="relative overflow-hidden rounded-3xl border border-white/5 bg-[#090b1f] p-4 shadow-card">
      <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-accent/20 to-transparent" />
      <div className="relative flex items-center justify-between pb-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Live vision</p>
          <h3 className="font-display text-2xl text-foreground">Robot Camera Stream</h3>
        </div>
        <span className="flex items-center gap-2 rounded-full bg-success/10 px-4 py-1 text-xs font-medium text-success">
          <span className="h-2 w-2 animate-pulse rounded-full bg-success" /> Streaming
        </span>
      </div>
      <div className="relative overflow-hidden rounded-[22px] border border-white/5 bg-black">
        <img
          src={videoSrc}
          alt="Pi camera stream"
          className="h-[420px] w-full object-cover"
          onError={event => {
            event.currentTarget.src = `https://dummyimage.com/1280x720/101225/ffffff&text=Stream+Offline`;
          }}
        />
        <button className="absolute bottom-6 right-6 flex items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-xs font-medium text-white backdrop-blur-sm transition hover:bg-white/25">
          <PlayPauseIcon className="h-4 w-4" /> Refresh
        </button>
      </div>
    </div>
  );
};

export default VideoStream;
