import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), "");

	return {
		plugins: [react()],
		define: {
			__PI_API__: JSON.stringify(
				env.VITE_PI_API_BASE || "http://192.168.1.12:5000"
			),
			__WINDOWS_API__: JSON.stringify(
				env.VITE_WINDOWS_API_BASE || "http://localhost:5050"
			),
		},
		css: {
			postcss: "./postcss.config.js",
		},
		server: {
			port: 5173,
			host: true,
		},
	};
});
