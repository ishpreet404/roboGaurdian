package main

import (
	"net/http"
	"strings"
	"sync"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
)

type Config struct {
	Port              string
	PiCameraStreamURL string
	AllowedOrigins    []string
}

type Server struct {
	hub     *Hub
	state   State
	stateMu sync.RWMutex
	config  Config
}

func NewServer(config Config) *Server {
	return &Server{
		hub:    NewHub(),
		state:  State{},
		config: config,
	}
}

func (s *Server) Router() http.Handler {
	r := chi.NewRouter()

	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	allowedOrigins := s.config.AllowedOrigins
	if len(allowedOrigins) == 0 {
		allowedOrigins = []string{"*"}
	}

	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   allowedOrigins,
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: false,
		MaxAge:           300,
	}))

	r.Get("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	r.Get("/ws", s.handleWebsocket)
	if strings.TrimSpace(s.config.PiCameraStreamURL) != "" {
		r.Get("/camera/stream", s.handleCameraStream)
	}

	r.Route("/api", func(api chi.Router) {
		api.Get("/state", s.handleState)
		api.Post("/command", s.handleCommand)
		api.Post("/telemetry", s.handleTelemetry)
		api.Post("/path", s.handlePath)
		api.Post("/victims", s.handleVictims)
		api.Post("/alerts", s.handleAlerts)
	})

	return r
}
