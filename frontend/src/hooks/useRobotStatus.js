import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { useRobot } from "../context/RobotContext.jsx";

const friendly = (value, fallback = "—") => {
	if (value === null || value === undefined) return fallback;
	if (typeof value === "number") return value;
	const trimmed = String(value).trim();
	if (!trimmed) return fallback;
	const lowered = trimmed.toLowerCase();
	if (["unknown", "undefined", "offline", "n/a"].includes(lowered)) {
		return "Unknown";
	}
	return trimmed;
};

const defaultStatus = {
	server: "Offline",
	uart: "Unknown",
	camera: "Unknown",
	uptime: "—",
	commands: 0,
	framesServed: 0,
	cpu: "—",
	memory: "—",
	temperature: "—",
	lastCommand: "None",
	lastCommandTime: "—",
	alerts: [],
	voiceReady: false,
};

export const useRobotStatus = (pollInterval = 7000) => {
	const { piBaseUrl, windowsBaseUrl } = useRobot();
	const [status, setStatus] = useState(defaultStatus);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	const fetchStatus = useCallback(async () => {
		try {
			setError(null);
			const [{ data: piStatus }, { data: windowsStatus }] = await Promise.all([
				axios
					.get(`${piBaseUrl.replace(/\/$/, "")}/status`, { timeout: 4000 })
					.catch(() => ({ data: null })),
				axios
					.get(`${windowsBaseUrl.replace(/\/$/, "")}/api/status`, {
						timeout: 4000,
					})
					.catch(() => ({ data: null })),
			]);

			setStatus((prev) => ({
				...prev,
				...(piStatus
					? {
							server: friendly(piStatus.status, prev.server),
							uart: friendly(piStatus.uart_status, prev.uart),
							camera: friendly(piStatus.camera_status, prev.camera),
							uptime: friendly(piStatus.uptime, prev.uptime),
							commands:
								typeof piStatus.commands_received === "number"
									? piStatus.commands_received
									: prev.commands,
							framesServed:
								typeof piStatus.frames_served === "number"
									? piStatus.frames_served
									: prev.framesServed,
							cpu: friendly(piStatus.cpu_usage, prev.cpu),
							memory: friendly(piStatus.memory_usage, prev.memory),
							temperature: friendly(piStatus.temperature, prev.temperature),
							lastCommand: friendly(piStatus.last_command, prev.lastCommand),
							lastCommandTime: friendly(
								piStatus.last_command_time,
								prev.lastCommandTime
							),
					  }
					: {}),
				...(windowsStatus
					? {
							alerts: windowsStatus.alerts || prev.alerts,
							voiceReady: !!windowsStatus.voice_ready,
					  }
					: {}),
			}));
		} catch (err) {
			console.error("Failed to load status", err);
			setError(
				"Unable to fetch robot status. Check network and device uptime."
			);
		} finally {
			setLoading(false);
		}
	}, [piBaseUrl, windowsBaseUrl]);

	useEffect(() => {
		fetchStatus();
		const id = setInterval(fetchStatus, pollInterval);
		return () => clearInterval(id);
	}, [fetchStatus, pollInterval]);

	return { status, loading, error, refresh: fetchStatus };
};
