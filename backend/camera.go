package main

import (
	"io"
	"net/http"
)

func (s *Server) handleCameraStream(w http.ResponseWriter, r *http.Request) {
	if s.config.PiCameraStreamURL == "" {
		http.Error(w, "camera stream not configured", http.StatusServiceUnavailable)
		return
	}

	client := &http.Client{
		Timeout: 0,
	}

	req, err := http.NewRequestWithContext(r.Context(), http.MethodGet, s.config.PiCameraStreamURL, nil)
	if err != nil {
		http.Error(w, "invalid camera request", http.StatusBadRequest)
		return
	}

	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, "camera source unavailable", http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	w.Header().Set("Cache-Control", "no-store")
	if contentType := resp.Header.Get("Content-Type"); contentType != "" {
		w.Header().Set("Content-Type", contentType)
	} else {
		w.Header().Set("Content-Type", "multipart/x-mixed-replace; boundary=frame")
	}
	w.Header().Set("X-Stream-Proxy", "rover-backend")
	w.WriteHeader(http.StatusOK)

	_, _ = io.Copy(w, resp.Body)
}
