import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const defaultHttpBase =
	import.meta.env.VITE_BACKEND_HTTP_BASE || __BACKEND_HTTP__;
const defaultWsUrl = import.meta.env.VITE_BACKEND_WS_URL || __BACKEND_WS__;

const emptyState = {
	telemetry: null,
	path: [],
	victims: [],
	alerts: [],
	logs: [],
};

const addLogEntry = (logs, entry) => {
	const next = [entry, ...logs];
	return next.slice(0, 200);
};

export const useMissionSocket = ({
	httpBase = defaultHttpBase,
	wsUrl = defaultWsUrl,
} = {}) => {
	const [state, setState] = useState(emptyState);
	const [connected, setConnected] = useState(false);
	const socketRef = useRef(null);

	const fetchState = useCallback(async () => {
		try {
			const response = await fetch(`${httpBase.replace(/\/$/, "")}/api/state`);
			if (!response.ok) return;
			const data = await response.json();
			setState((prev) => ({
				...prev,
				telemetry: data.telemetry || prev.telemetry,
				path: data.path || prev.path,
				victims: data.victims || prev.victims,
				alerts: data.alerts || prev.alerts,
				logs: data.logs || prev.logs,
			}));
		} catch {
			// ignore initial state errors
		}
	}, [httpBase]);

	useEffect(() => {
		fetchState();
	}, [fetchState]);

	useEffect(() => {
		if (!wsUrl) return undefined;
		const socket = new WebSocket(wsUrl);
		socketRef.current = socket;

		socket.addEventListener("open", () => {
			setConnected(true);
			socket.send(JSON.stringify({ type: "hello", data: { role: "ui" } }));
		});

		socket.addEventListener("close", () => setConnected(false));
		socket.addEventListener("error", () => setConnected(false));

		socket.addEventListener("message", (event) => {
			try {
				const payload = JSON.parse(event.data);
				setState((prev) => {
					switch (payload.type) {
						case "telemetry":
							return { ...prev, telemetry: payload.data };
						case "path":
							return { ...prev, path: payload.data.points || payload.data };
						case "victims":
							return { ...prev, victims: payload.data };
						case "alert":
							return {
								...prev,
								alerts: [payload.data, ...prev.alerts].slice(0, 200),
								logs: addLogEntry(prev.logs, {
									id: payload.data.id,
									level: payload.data.level,
									message: payload.data.message,
									timestamp: payload.data.timestamp,
								}),
							};
						case "alerts":
							return { ...prev, alerts: payload.data };
						case "command":
							return {
								...prev,
								logs: addLogEntry(prev.logs, {
									id: `cmd-${Date.now()}`,
									level: "info",
									message: `command issued: ${payload.data.action}`,
									timestamp: new Date().toISOString(),
								}),
							};
						default:
							return prev;
					}
				});
			} catch {
				// ignore parse errors
			}
		});

		return () => {
			socket.close();
		};
	}, [wsUrl]);

	const sendCommand = useCallback(
		async (action, options = {}) => {
			const payload = {
				action,
				speed: options.speed || 0.6,
				duration_ms: options.durationMs || 0,
			};

			const endpoint = `${httpBase.replace(/\/$/, "")}/api/command`;
			const response = await fetch(endpoint, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload),
			});

			if (!response.ok) {
				throw new Error("Command failed");
			}
		},
		[httpBase],
	);

	const telemetry = useMemo(() => state.telemetry || {}, [state.telemetry]);

	return {
		state,
		telemetry,
		connected,
		sendCommand,
		httpBase,
	};
};
