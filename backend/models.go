package main

import "time"

type Pose struct {
	X          float64 `json:"x"`
	Y          float64 `json:"y"`
	HeadingDeg float64 `json:"heading_deg"`
}

type IMUData struct {
	Ax       float64 `json:"ax"`
	Ay       float64 `json:"ay"`
	Az       float64 `json:"az"`
	Gx       float64 `json:"gx"`
	Gy       float64 `json:"gy"`
	Gz       float64 `json:"gz"`
	YawDeg   float64 `json:"yaw_deg"`
	PitchDeg float64 `json:"pitch_deg"`
	RollDeg  float64 `json:"roll_deg"`
}

type GPSData struct {
	Lat      float64 `json:"lat"`
	Lon      float64 `json:"lon"`
	SpeedMps float64 `json:"speed_mps"`
	Sats     int     `json:"sats"`
	Fix      bool    `json:"fix"`
}

type Odometry struct {
	DistanceM float64 `json:"distance_m"`
	SpeedMps  float64 `json:"speed_mps"`
}

type Battery struct {
	Voltage float64 `json:"voltage"`
	Percent float64 `json:"percent"`
}

type Motor struct {
	State string  `json:"state"`
	Speed float64 `json:"speed"`
}

type SystemStatus struct {
	UptimeSec float64 `json:"uptime_sec"`
	Mode      string  `json:"mode"`
}

type Telemetry struct {
	Timestamp time.Time    `json:"timestamp"`
	Pose      Pose         `json:"pose"`
	IMU       IMUData      `json:"imu"`
	GPS       GPSData      `json:"gps"`
	Odometry  Odometry     `json:"odometry"`
	SonarCM   float64      `json:"sonar_cm"`
	Battery   Battery      `json:"battery"`
	Motor     Motor        `json:"motor"`
	System    SystemStatus `json:"system"`
}

type PathPoint struct {
	X          float64   `json:"x"`
	Y          float64   `json:"y"`
	Lat        float64   `json:"lat"`
	Lon        float64   `json:"lon"`
	HeadingDeg float64   `json:"heading_deg"`
	Timestamp  time.Time `json:"timestamp"`
}

type PathUpdate struct {
	Points []PathPoint `json:"points"`
}

type Victim struct {
	ID         string    `json:"id"`
	Lat        float64   `json:"lat"`
	Lon        float64   `json:"lon"`
	X          float64   `json:"x"`
	Y          float64   `json:"y"`
	Confidence float64   `json:"confidence"`
	DetectedAt time.Time `json:"detected_at"`
}

type Alert struct {
	ID        string    `json:"id"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

type LogEntry struct {
	ID        string    `json:"id"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

type Command struct {
	Action     string  `json:"action"`
	Speed      float64 `json:"speed"`
	DurationMs int     `json:"duration_ms"`
}

type State struct {
	Telemetry *Telemetry  `json:"telemetry"`
	Path      []PathPoint `json:"path"`
	Victims   []Victim    `json:"victims"`
	Alerts    []Alert     `json:"alerts"`
	Logs      []LogEntry  `json:"logs"`
}

// ws message envelope

type WsMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}
