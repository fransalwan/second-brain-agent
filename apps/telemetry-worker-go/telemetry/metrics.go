package telemetry

import (
	"runtime"
	"sync/atomic"
	"time"
)

type Metrics struct {
	EvaluationsTotal      uint64 `json:"evaluations_total"`
	AlertsDispatchedTotal uint64 `json:"alerts_dispatched_total"`
	StartTime             time.Time
}

func NewMetrics() *Metrics {
	return &Metrics{
		StartTime: time.Now(),
	}
}

func (m *Metrics) IncEvaluations() {
	atomic.AddUint64(&m.EvaluationsTotal, 1)
}

func (m *Metrics) IncAlertsDispatched() {
	atomic.AddUint64(&m.AlertsDispatchedTotal, 1)
}

type MetricsSnapshot struct {
	EvaluationsTotal      uint64  `json:"evaluations_total"`
	AlertsDispatchedTotal uint64  `json:"alerts_dispatched_total"`
	GoroutineCount        int     `json:"goroutine_count"`
	UptimeSeconds         float64 `json:"uptime_seconds"`
}

func (m *Metrics) Snapshot() MetricsSnapshot {
	return MetricsSnapshot{
		EvaluationsTotal:      atomic.LoadUint64(&m.EvaluationsTotal),
		AlertsDispatchedTotal: atomic.LoadUint64(&m.AlertsDispatchedTotal),
		GoroutineCount:        runtime.NumGoroutine(),
		UptimeSeconds:         time.Since(m.StartTime).Seconds(),
	}
}

