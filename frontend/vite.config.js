import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), "");

	return {
		plugins: [react()],
		define: {
			__BACKEND_HTTP__: JSON.stringify(
				env.VITE_BACKEND_HTTP_BASE || "http://localhost:8080",
			),
			__BACKEND_WS__: JSON.stringify(
				env.VITE_BACKEND_WS_URL || "ws://localhost:8080/ws",
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
