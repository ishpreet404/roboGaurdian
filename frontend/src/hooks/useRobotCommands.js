import { useCallback, useState } from "react";
import axios from "axios";
import { useRobot } from "../context/RobotContext.jsx";

const COMMAND_MAP = {
	forward: "F",
	backward: "B",
	left: "L",
	right: "R",
	stop: "S",
};

export const useRobotCommands = () => {
	const { piBaseUrl, windowsBaseUrl } = useRobot();
	const [isSending, setIsSending] = useState(false);
	const [lastResult, setLastResult] = useState(null);

	const sendCommand = useCallback(
		async (direction, { via = "pi" } = {}) => {
			const mapped = COMMAND_MAP[direction];
			if (!mapped) {
				throw new Error(`Unsupported command direction: ${direction}`);
			}

			const baseUrl = (via === "windows" ? windowsBaseUrl : piBaseUrl).replace(
				/\/$/,
				""
			);
			const endpoint = via === "windows" ? "/api/command" : "/move";

			setIsSending(true);
			setLastResult(null);

			try {
				const { data } = await axios.post(
					`${baseUrl}${endpoint}`,
					via === "windows" ? { command: mapped } : { direction: mapped },
					{ timeout: 4000 }
				);
				setLastResult({ success: data?.status === "success", data });
				return data;
			} catch (error) {
				console.error("Command failed", error);
				setLastResult({ success: false, error });
				throw error;
			} finally {
				setIsSending(false);
			}
		},
		[piBaseUrl, windowsBaseUrl]
	);

	const sendMultiStep = useCallback(
		async (sequence, options = {}) => {
			for (const step of sequence) {
				const { action, hold = 0.35 } = step;
				await sendCommand(action, options);
				await new Promise((resolve) => setTimeout(resolve, hold * 1000));
			}
		},
		[sendCommand]
	);

	return {
		sendCommand,
		sendMultiStep,
		isSending,
		lastResult,
	};
};
