import React from "react";
import { motion } from "framer-motion";

const Stat = ({ label, value, unit }) => (
  <div className="rounded-2xl border border-white/10 bg-black/40 p-4">
    <p className="text-xs uppercase tracking-[0.3em] text-muted">{label}</p>
    <div className="mt-2 flex items-baseline gap-2">
      <span className="text-2xl font-semibold text-foreground">{value}</span>
      {unit && <span className="text-xs text-muted">{unit}</span>}
    </div>
  </div>
);

const TelemetryPanel = ({ telemetry = {} }) => {
  const gps = telemetry.gps || {};
  const odom = telemetry.odometry || {};
  const imu = telemetry.imu || {};
  const battery = telemetry.battery || {};

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-card"
    >
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.35em] text-muted">Telemetry</p>
        <h3 className="font-display text-xl text-foreground">Rover vitals</h3>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Stat label="Speed" value={(odom.speed_mps || 0).toFixed(2)} unit="m/s" />
        <Stat label="Heading" value={(imu.yaw_deg || 0).toFixed(1)} unit="deg" />
        <Stat label="Battery" value={(battery.percent || 0).toFixed(0)} unit="%" />
        <Stat label="Sonar" value={(telemetry.sonar_cm || 0).toFixed(1)} unit="cm" />
        <Stat label="GPS" value={gps.fix ? "LOCK" : "NO FIX"} unit={`${gps.sats || 0} sats`} />
        <Stat label="Distance" value={(odom.distance_m || 0).toFixed(1)} unit="m" />
      </div>
    </motion.div>
  );
};

export default TelemetryPanel;
