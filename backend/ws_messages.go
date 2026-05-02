package main

import (
	"encoding/json"
	"time"
)

func (s *Server) handleWSMessage(client *Client, msg WsMessage) {
	raw, err := json.Marshal(msg.Data)
	if err != nil {
		return
	}

	switch msg.Type {
	case "hello":
		var payload map[string]interface{}
		if err := json.Unmarshal(raw, &payload); err == nil {
			if role, ok := payload["role"].(string); ok {
				client.role = role
			}
		}
		ack := WsMessage{Type: "hello", Data: map[string]string{"status": "ok"}}
		if encoded, err := json.Marshal(ack); err == nil {
			client.send <- encoded
		}
	case "telemetry":
		var payload Telemetry
		if err := json.Unmarshal(raw, &payload); err != nil {
			return
		}
		if payload.Timestamp.IsZero() {
			payload.Timestamp = time.Now().UTC()
		}
		s.setTelemetry(payload)
		s.broadcast("telemetry", payload)
	case "path":
		var update PathUpdate
		if err := json.Unmarshal(raw, &update); err == nil && len(update.Points) > 0 {
			s.setPath(update.Points)
			s.broadcast("path", update.Points)
			return
		}
		var points []PathPoint
		if err := json.Unmarshal(raw, &points); err != nil {
			return
		}
		s.setPath(points)
		s.broadcast("path", points)
	case "victims":
		var victims []Victim
		if err := json.Unmarshal(raw, &victims); err != nil {
			return
		}
		s.setVictims(victims)
		s.broadcast("victims", victims)
	case "alert":
		var alert Alert
		if err := json.Unmarshal(raw, &alert); err == nil && alert.Message != "" {
			if alert.Timestamp.IsZero() {
				alert.Timestamp = time.Now().UTC()
			}
			s.addAlert(alert)
			s.broadcast("alert", alert)
			return
		}
		var alerts []Alert
		if err := json.Unmarshal(raw, &alerts); err != nil {
			return
		}
		for idx := range alerts {
			if alerts[idx].Timestamp.IsZero() {
				alerts[idx].Timestamp = time.Now().UTC()
			}
		}
		s.setAlerts(alerts)
		s.broadcast("alerts", alerts)
	case "command":
		var cmd Command
		if err := json.Unmarshal(raw, &cmd); err != nil {
			return
		}
		if cmd.Action == "" {
			return
		}
		s.broadcast("command", cmd)
		s.addLog(LogEntry{
			ID:        "cmd-" + time.Now().UTC().Format("150405.000"),
			Level:     "info",
			Message:   "command issued: " + cmd.Action,
			Timestamp: time.Now().UTC(),
		})
	}
}
