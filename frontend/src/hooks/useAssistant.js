import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useRobot } from "../context/RobotContext.jsx";

const normaliseReminder = (reminder) => ({
	id: reminder?.id,
	message: reminder?.message ?? "",
	remindAt: reminder?.remind_at ?? reminder?.remindAt ?? null,
	createdAt: reminder?.created_at ?? reminder?.createdAt ?? null,
	voiceNote: reminder?.voice_note ?? reminder?.voiceNote ?? null,
	delivered: Boolean(reminder?.delivered),
});

export const useAssistant = () => {
	const { piBaseUrl, windowsBaseUrl } = useRobot();
	const assistantBase = useMemo(
		() => `${windowsBaseUrl.replace(/\/$/, "")}/api/assistant`,
		[windowsBaseUrl]
	);
	const modeEndpoint = useMemo(
		() => `${windowsBaseUrl.replace(/\/$/, "")}/api/mode`,
		[windowsBaseUrl]
	);

	const [messages, setMessages] = useState([]);
	const [sending, setSending] = useState(false);
	const [error, setError] = useState(null);
	const [voiceReady, setVoiceReady] = useState(false);
	const [reminders, setReminders] = useState([]);
	const [loadingReminders, setLoadingReminders] = useState(false);
	const [operatingMode, setOperatingMode] = useState("care_companion");
	const [modeMetadata, setModeMetadata] = useState({});
	const [availableModes, setAvailableModes] = useState([]);
	const [watchdogAlarmActive, setWatchdogAlarmActive] = useState(false);
	const [updatingMode, setUpdatingMode] = useState(false);
	const [modeError, setModeError] = useState(null);

	const fetchStatus = useCallback(async () => {
		try {
			const { data } = await axios.get(`${assistantBase}/status`, {
				timeout: 4000,
			});
			setVoiceReady(Boolean(data?.voice_ready ?? data?.voiceReady));
			if (data?.mode) {
				setOperatingMode(String(data.mode));
			}
			if (data?.mode_metadata) {
				setModeMetadata(data.mode_metadata);
			}
			if (Array.isArray(data?.available_modes)) {
				setAvailableModes(data.available_modes);
			}
			if (typeof data?.watchdog_alarm_active === "boolean") {
				setWatchdogAlarmActive(Boolean(data.watchdog_alarm_active));
			}
			if (Array.isArray(data?.history) && data.history.length > 0) {
				setMessages(
					data.history.map((item) => ({
						role: item.role,
						content: item.content,
						timestamp: item.timestamp ?? null,
					}))
				);
			}
			if (Array.isArray(data?.reminders)) {
				setReminders(data.reminders.map(normaliseReminder));
			}
		} catch {
			setVoiceReady(false);
		}
	}, [assistantBase]);

	const fetchReminders = useCallback(async () => {
		try {
			setLoadingReminders(true);
			const { data } = await axios.get(`${assistantBase}/reminders`, {
				timeout: 5000,
			});
			if (data?.status === "success" && Array.isArray(data.reminders)) {
				setReminders(data.reminders.map(normaliseReminder));
			}
		} catch (fetchError) {
			console.error("Failed to load reminders", fetchError);
		} finally {
			setLoadingReminders(false);
		}
	}, [assistantBase]);

	const fetchModeInfo = useCallback(async () => {
		try {
			const { data } = await axios.get(modeEndpoint, { timeout: 4000 });
			if (data?.mode) {
				setOperatingMode(String(data.mode));
			}
			if (data?.metadata) {
				setModeMetadata(data.metadata);
			}
			if (Array.isArray(data?.available_modes)) {
				setAvailableModes(data.available_modes);
			}
			if (typeof data?.watchdog_alarm_active === "boolean") {
				setWatchdogAlarmActive(Boolean(data.watchdog_alarm_active));
			}
		} catch (modeFetchError) {
			console.warn("Mode status fetch failed", modeFetchError);
		}
	}, [modeEndpoint]);

	useEffect(() => {
		fetchStatus();
		fetchReminders();
		fetchModeInfo();
		const id = setInterval(() => {
			fetchStatus();
			fetchModeInfo();
		}, 15000);
		return () => clearInterval(id);
	}, [fetchStatus, fetchReminders, fetchModeInfo]);

	const sendMessage = useCallback(
		async (text, { speak = true } = {}) => {
			const trimmed = (text || "").trim();
			if (!trimmed) {
				throw new Error("Message cannot be empty.");
			}

			const userMessage = {
				role: "user",
				content: trimmed,
				timestamp: new Date().toISOString(),
			};

			setMessages((prev) => [...prev, userMessage]);
			setSending(true);
			setError(null);

			try {
				const { data } = await axios.post(
					`${assistantBase}/message`,
					{ text: trimmed, speak, history_limit: 40 },
					{ timeout: 15000 }
				);

				if (data?.status !== "success") {
					throw new Error(data?.message || "Assistant error");
				}

				const replyMessage = {
					role: "assistant",
					content: data.reply,
					timestamp: data.timestamp || new Date().toISOString(),
				};

				const mergedHistory = Array.isArray(data.history)
					? data.history.map((item) => ({
							role: item.role,
							content: item.content,
							timestamp: item.timestamp ?? null,
					  }))
					: [
							{
								role: "user",
								content: trimmed,
								timestamp: userMessage.timestamp,
							},
							replyMessage,
					  ];

				setMessages(mergedHistory);

				return replyMessage;
			} catch (requestError) {
				console.error("Assistant request failed", requestError);
				const serverMessage =
					requestError?.response?.data?.message ||
					requestError?.response?.data?.details;
				const friendlyMessage =
					serverMessage ||
					requestError?.message ||
					"Assistant unavailable. Please try again.";
				setError(friendlyMessage);
				setMessages((prev) => prev.filter((msg) => msg !== userMessage));
				throw requestError;
			} finally {
				setSending(false);
			}
		},
		[assistantBase]
	);

	const addReminder = useCallback(
		async ({ message, remindAt, delayMinutes, voiceNote }) => {
			const payload = { message, voice_note: voiceNote };

			if (remindAt) {
				payload.remind_at = remindAt;
			} else if (delayMinutes) {
				payload.delay_minutes = delayMinutes;
			}

			const { data } = await axios.post(`${assistantBase}/reminders`, payload, {
				timeout: 8000,
			});

			if (data?.status !== "success") {
				throw new Error(data?.message || "Unable to create reminder");
			}

			const reminder = normaliseReminder(data.reminder);
			setReminders((prev) => [reminder, ...prev]);
			return reminder;
		},
		[assistantBase]
	);

	const deleteReminder = useCallback(
		async (id) => {
			if (!id) return;
			const { data } = await axios.delete(`${assistantBase}/reminders/${id}`, {
				timeout: 5000,
			});

			if (data?.status !== "success") {
				throw new Error(data?.message || "Failed to delete reminder");
			}

			setReminders((prev) => prev.filter((rem) => rem.id !== id));
			return data.reminder;
		},
		[assistantBase]
	);

	const changeMode = useCallback(
		async (nextMode, metadata = {}) => {
			const normalized = (nextMode || "").toLowerCase();
			if (!normalized) {
				throw new Error("Mode cannot be empty");
			}
			setUpdatingMode(true);
			setModeError(null);
			try {
				const { data } = await axios.post(
					modeEndpoint,
					{ mode: normalized, metadata },
					{ timeout: 8000 }
				);
				if (data?.status !== "success") {
					throw new Error(data?.message || "Unable to change mode");
				}
				if (data.mode) {
					setOperatingMode(String(data.mode));
				}
				if (data.metadata) {
					setModeMetadata(data.metadata);
				}
				if (Array.isArray(data.available_modes)) {
					setAvailableModes(data.available_modes);
				}
				if (typeof data.watchdog_alarm_active === "boolean") {
					setWatchdogAlarmActive(Boolean(data.watchdog_alarm_active));
				}
				return data;
			} catch (modeChangeError) {
				console.error("Mode switch failed", modeChangeError);
				setModeError(modeChangeError?.message || "Mode change failed");
				throw modeChangeError;
			} finally {
				setUpdatingMode(false);
			}
		},
		[modeEndpoint]
	);

	const silenceWatchdogAlarm = useCallback(async () => {
		setUpdatingMode(true);
		setModeError(null);
		try {
			const { data } = await axios.post(
				modeEndpoint,
				{ action: "silence_alarm" },
				{ timeout: 5000 }
			);
			if (data?.status !== "success") {
				throw new Error(data?.message || "Unable to silence alarm");
			}
			if (data.metadata) {
				setModeMetadata(data.metadata);
			}
			if (typeof data.watchdog_alarm_active === "boolean") {
				setWatchdogAlarmActive(Boolean(data.watchdog_alarm_active));
			}
			return data;
		} catch (alarmError) {
			console.error("Silencing watchdog alarm failed", alarmError);
			setModeError(alarmError?.message || "Alarm silence failed");
			throw alarmError;
		} finally {
			setUpdatingMode(false);
		}
	}, [modeEndpoint]);

	return {
		messages,
		sendMessage,
		sending,
		error,
		voiceReady,
		reminders,
		loadingReminders,
		refreshReminders: fetchReminders,
		addReminder,
		deleteReminder,
		operatingMode,
		modeMetadata,
		availableModes,
		watchdogAlarmActive,
		updatingMode,
		modeError,
		refreshMode: fetchModeInfo,
		setMode: changeMode,
		silenceWatchdogAlarm,
	};
};
