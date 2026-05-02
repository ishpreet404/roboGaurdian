export default {
	content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
	theme: {
		extend: {
			screens: {
				"3xl": "1920px",
			},
			colors: {
				surface: "#05060b",
				surfaceAlt: "#0a0f1a",
				card: "#0f1625",
				accent: "#00f5d4",
				accentSoft: "#66ffe6",
				highlight: "#ff7a18",
				foreground: "#eef2ff",
				muted: "#8b97b5",
				success: "#22c55e",
				warning: "#f59e0b",
				danger: "#ef4444",
				info: "#38bdf8",
			},
			fontFamily: {
				display: ["Oxanium", "system-ui", "sans-serif"],
				body: ["Manrope", "system-ui", "sans-serif"],
			},
			boxShadow: {
				glow: "0 20px 45px rgba(0, 245, 212, 0.35)",
				card: "0 22px 50px rgba(5, 10, 25, 0.6)",
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
