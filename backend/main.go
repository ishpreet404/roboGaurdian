package main

import (
	"log"
	"net/http"
	"os"
	"strings"
	"time"
)

func main() {
	config := Config{
		Port:              envOr("PORT", "8080"),
		PiCameraStreamURL: envOr("PI_CAMERA_STREAM_URL", "http://raspberrypi:8000/camera/stream"),
		AllowedOrigins:    parseOrigins(envOr("ALLOWED_ORIGINS", "*")),
	}

	server := NewServer(config)
	go server.hub.Run()

	addr := ":" + config.Port
	httpServer := &http.Server{
		Addr:              addr,
		Handler:           server.Router(),
		ReadHeaderTimeout: 10 * time.Second,
	}

	log.Printf("backend listening on %s", addr)
	if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("server error: %v", err)
	}
}

func envOr(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func parseOrigins(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	var origins []string
	for _, part := range parts {
		cleaned := strings.TrimSpace(part)
		if cleaned != "" {
			origins = append(origins, cleaned)
		}
	}
	return origins
}
