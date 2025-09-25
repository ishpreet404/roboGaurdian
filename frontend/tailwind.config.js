export default {
	content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
	theme: {
		extend: {
			colors: {
				surface: "#070819",
				surfaceAlt: "#101225",
				card: "#12152e",
				accent: "#7c5cff",
				accentSoft: "#a48dff",
				foreground: "#f5f7ff",
				muted: "#9aa3c2",
				success: "#4ade80",
				warning: "#facc15",
				danger: "#f87171",
				info: "#38bdf8",
			},
			fontFamily: {
				display: ["Space Grotesk", "system-ui", "sans-serif"],
				body: ["Urbanist", "system-ui", "sans-serif"],
			},
			boxShadow: {
				glow: "0 20px 45px rgba(124, 92, 255, 0.35)",
				card: "0 20px 50px rgba(6, 10, 40, 0.55)",
			},
			backdropBlur: {
				xs: "2px",
			},
			animation: {
				pulseFast: "pulse 1.8s ease-in-out infinite",
				float: "float 6s ease-in-out infinite",
			},
			keyframes: {
				float: {
					"0%, 100%": { transform: "translateY(0)" },
					"50%": { transform: "translateY(-12px)" },
				},
			},
		},
	},
	plugins: [],
};
