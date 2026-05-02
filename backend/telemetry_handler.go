package main

import (
	"encoding/json"
	"io"
	"net/http"
	"time"
)

const (
	maxAlerts = 200
	maxLogs   = 300
)

func (s *Server) handleState(w http.ResponseWriter, _ *http.Request) {
	s.stateMu.RLock()
	defer s.stateMu.RUnlock()

	writeJSON(w, http.StatusOK, s.state)
}

func (s *Server) handleTelemetry(w http.ResponseWriter, r *http.Request) {
	var payload Telemetry
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid telemetry payload"})
		return
	}
	if payload.Timestamp.IsZero() {
		payload.Timestamp = time.Now().UTC()
	}

	s.setTelemetry(payload)
	s.broadcast("telemetry", payload)

	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handlePath(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid path payload"})
		return
	}

	var update PathUpdate
	if err := json.Unmarshal(body, &update); err == nil && len(update.Points) > 0 {
		s.setPath(update.Points)
		s.broadcast("path", update.Points)
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
		return
	}

	var points []PathPoint
	if err := json.Unmarshal(body, &points); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid path payload"})
		return
	}

	s.setPath(points)
	s.broadcast("path", points)
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleVictims(w http.ResponseWriter, r *http.Request) {
	var victims []Victim
	if err := json.NewDecoder(r.Body).Decode(&victims); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid victims payload"})
		return
	}

	s.setVictims(victims)
	s.broadcast("victims", victims)
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleAlerts(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid alert payload"})
		return
	}

	var single Alert
	if err := json.Unmarshal(body, &single); err == nil && single.Message != "" {
		if single.Timestamp.IsZero() {
			single.Timestamp = time.Now().UTC()
		}
		s.addAlert(single)
		s.broadcast("alert", single)
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
		return
	}

	var alerts []Alert
	if err := json.Unmarshal(body, &alerts); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid alert payload"})
		return
	}
	for idx := range alerts {
		if alerts[idx].Timestamp.IsZero() {
			alerts[idx].Timestamp = time.Now().UTC()
		}
	}

	s.setAlerts(alerts)
	s.broadcast("alerts", alerts)
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleCommand(w http.ResponseWriter, r *http.Request) {
	var cmd Command
	if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid command payload"})
		return
	}
	if cmd.Action == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "missing command action"})
		return
	}

	s.broadcast("command", cmd)
	s.addLog(LogEntry{
		ID:        "cmd-" + time.Now().UTC().Format("150405.000"),
		Level:     "info",
		Message:   "command issued: " + cmd.Action,
		Timestamp: time.Now().UTC(),
	})

	writeJSON(w, http.StatusOK, map[string]string{"status": "sent"})
}

func (s *Server) broadcast(msgType string, data interface{}) {
	s.hub.broadcast <- WsMessage{Type: msgType, Data: data}
}

func (s *Server) setTelemetry(payload Telemetry) {
	s.stateMu.Lock()
	defer s.stateMu.Unlock()
	s.state.Telemetry = &payload
}

func (s *Server) setPath(points []PathPoint) {
	s.stateMu.Lock()
	defer s.stateMu.Unlock()
	s.state.Path = points
}

func (s *Server) setVictims(victims []Victim) {
	s.stateMu.Lock()
	defer s.stateMu.Unlock()
	s.state.Victims = victims
}

func (s *Server) setAlerts(alerts []Alert) {
	s.stateMu.Lock()
	defer s.stateMu.Unlock()
	s.state.Alerts = alerts
}

func (s *Server) addAlert(alert Alert) {
	s.stateMu.Lock()
	defer s.stateMu.Unlock()
	s.state.Alerts = append([]Alert{alert}, s.state.Alerts...)
	if len(s.state.Alerts) > maxAlerts {
		s.state.Alerts = s.state.Alerts[:maxAlerts]
	}
}

func (s *Server) addLog(entry LogEntry) {
	s.stateMu.Lock()
	defer s.stateMu.Unlock()
	s.state.Logs = append([]LogEntry{entry}, s.state.Logs...)
	if len(s.state.Logs) > maxLogs {
		s.state.Logs = s.state.Logs[:maxLogs]
	}
}

func writeJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}
