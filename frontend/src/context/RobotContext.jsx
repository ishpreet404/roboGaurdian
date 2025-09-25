import React, { createContext, useContext, useMemo, useState } from 'react';

const RobotContext = createContext(null);

export const RobotProvider = ({ children }) => {
  const [piBaseUrl, setPiBaseUrl] = useState(
    import.meta.env.VITE_PI_API_BASE || __PI_API__
  );
  const [windowsBaseUrl, setWindowsBaseUrl] = useState(
    import.meta.env.VITE_WINDOWS_API_BASE || __WINDOWS_API__
  );

  const value = useMemo(
    () => ({
      piBaseUrl,
      windowsBaseUrl,
      setPiBaseUrl,
      setWindowsBaseUrl
    }),
    [piBaseUrl, windowsBaseUrl]
  );

  return <RobotContext.Provider value={value}>{children}</RobotContext.Provider>;
};

export const useRobot = () => {
  const ctx = useContext(RobotContext);
  if (!ctx) {
    throw new Error('useRobot must be used within a RobotProvider');
  }
  return ctx;
};
