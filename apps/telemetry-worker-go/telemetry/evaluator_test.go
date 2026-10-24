package telemetry

import (
	"context"
	"testing"
	"time"
)

func TestEvaluator_AllRules(t *testing.T) {
	evaluator := NewEvaluator()
	now := time.Date(2026, 10, 25, 10, 0, 0, 0, time.UTC)

	input := StudentTelemetryInput{
		UserID:                  "usr-123",
		Email:                   "student@ugm.ac.id",
		AvgSleepHours7D:         5.2, // < 6.0 -> SLEEP_DEBT_RISK
		DaysSinceDospemMeeting:  18,  // > 14 -> DOSPEM_GHOSTING_ALERT
		ActiveWorkPastNightHour: true, // BEDTIME_VIOLATION
		PendingDeadlines: []TaskDue{
			{
				TaskID:   1,
				Title:    "Tubes Machine Learning",
				Deadline: now.Add(12 * time.Hour), // < 24 jam -> URGENT_DEADLINE
				IsUrgent: true,
			},
			{
				TaskID:   2,
				Title:    "Reading Paper IEEE",
				Deadline: now.Add(72 * time.Hour), // > 24 jam (Aman)
				IsUrgent: false,
			},
		},
	}

	alerts, err := evaluator.Evaluate(input, now)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	expectedTypes := map[string]bool{
		"BEDTIME_VIOLATION":     false,
		"SLEEP_DEBT_RISK":       false,
		"URGENT_DEADLINE":       false,
		"DOSPEM_GHOSTING_ALERT": false,
	}

	for _, a := range alerts {
		if _, ok := expectedTypes[a.AlertType]; ok {
			expectedTypes[a.AlertType] = true
		}
	}

	for aType, found := range expectedTypes {
		if !found {
			t.Errorf("expected alert type %s not triggered", aType)
		}
	}

	if len(alerts) != 4 {
		t.Errorf("expected exactly 4 alerts, got %d", len(alerts))
	}
}

func TestEvaluator_EmptyUserValidation(t *testing.T) {
	evaluator := NewEvaluator()
	_, err := evaluator.Evaluate(StudentTelemetryInput{UserID: ""}, time.Now())
	if err == nil {
		t.Error("expected error for empty user_id, got nil")
	}
}

func TestWorkerPool_ConcurrencyAndRetry(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	mockDispatcher := &MockDispatcher{
		ShouldFailOn: 1, // Percobaan pertama gagal, kedua berhasil (uji exponential retry)
	}
	metrics := NewMetrics()
	pool := NewWorkerPool(4, 50, mockDispatcher, metrics)
	pool.Start(ctx)

	alert := TelemetryAlert{
		UserID:    "usr-001",
		AlertType: "TEST_ALERT",
		Severity:  SeverityMedium,
		Message:   "Test worker pool execution",
		CreatedAt: time.Now(),
	}

	submitted := pool.Submit(alert)
	if !submitted {
		t.Fatal("failed to submit alert to pool")
	}

	// Beri waktu goroutine menyelesaikan retry
	time.Sleep(100 * time.Millisecond)
	pool.Stop()

	processed, failed := pool.GetStats()
	if processed != 1 {
		t.Errorf("expected 1 processed alert, got %d (failed: %d)", processed, failed)
	}

	snapshot := metrics.Snapshot()
	if snapshot.AlertsDispatchedTotal != 1 {
		t.Errorf("expected 1 dispatched metric, got %d", snapshot.AlertsDispatchedTotal)
	}
}

