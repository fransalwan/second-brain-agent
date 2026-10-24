package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/fransalwan/second-brain-telemetry/telemetry"
)

type Server struct {
	evaluator *telemetry.Evaluator
	pool      *telemetry.WorkerPool
	metrics   *telemetry.Metrics
}

type StdoutDispatcher struct{}

func (s *StdoutDispatcher) Dispatch(ctx context.Context, alert telemetry.TelemetryAlert) error {
	log.Printf("[DISPATCH] [%s] User=%s: %s", alert.Severity, alert.UserID, alert.Message)
	return nil
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8085"
	}

	metrics := telemetry.NewMetrics()
	evaluator := telemetry.NewEvaluator()
	dispatcher := &StdoutDispatcher{}
	pool := telemetry.NewWorkerPool(8, 200, dispatcher, metrics)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	pool.Start(ctx)
	defer pool.Stop()

	server := &Server{
		evaluator: evaluator,
		pool:      pool,
		metrics:   metrics,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", server.handleHealth)
	mux.HandleFunc("GET /metrics", server.handleMetrics)
	mux.HandleFunc("POST /api/v1/telemetry/evaluate", server.handleEvaluate)

	httpServer := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	go func() {
		log.Printf("🚀 Second Brain Go Telemetry Engine running on port :%s", port)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("HTTP server error: %v", err)
		}
	}()

	// Graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	log.Println("Shutting down Go Telemetry Engine gracefully...")
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer shutdownCancel()

	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("HTTP shutdown error: %v", err)
	}
	log.Println("Server stopped cleanly.")
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "second-brain-telemetry-go",
		"time":    time.Now().UTC().Format(time.RFC3339),
	})
}

func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.metrics.Snapshot())
}

func (s *Server) handleEvaluate(w http.ResponseWriter, r *http.Request) {
	var input telemetry.StudentTelemetryInput
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, fmt.Sprintf("invalid request payload: %v", err), http.StatusBadRequest)
		return
	}

	s.metrics.IncEvaluations()
	alerts, err := s.evaluator.Evaluate(input, time.Now())
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	for _, a := range alerts {
		s.pool.Submit(a)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":       "success",
		"alerts_count": len(alerts),
		"alerts":       alerts,
	})
}

