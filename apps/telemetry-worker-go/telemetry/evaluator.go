package telemetry

import (
	"errors"
	"strings"
	"time"
)

type AlertSeverity string

const (
	SeverityLow      AlertSeverity = "LOW"
	SeverityMedium   AlertSeverity = "MEDIUM"
	SeverityHigh     AlertSeverity = "HIGH"
	SeverityCritical AlertSeverity = "CRITICAL"
)

type StudentTelemetryInput struct {
	UserID                  string    `json:"user_id"`
	Email                   string    `json:"email"`
	PendingDeadlines        []TaskDue `json:"pending_deadlines"`
	AvgSleepHours7D         float64   `json:"avg_sleep_hours_7d"`
	DaysSinceDospemMeeting  int       `json:"days_since_dospem_meeting"`
	ActiveWorkPastNightHour bool      `json:"active_work_past_night_hour"`
}

type TaskDue struct {
	TaskID   int       `json:"task_id"`
	Title    string    `json:"title"`
	Deadline time.Time `json:"deadline"`
	IsUrgent bool      `json:"is_urgent"`
}

type TelemetryAlert struct {
	UserID    string        `json:"user_id"`
	AlertType string        `json:"alert_type"`
	Severity  AlertSeverity `json:"severity"`
	Message   string        `json:"message"`
	CreatedAt time.Time     `json:"created_at"`
}

type Evaluator struct{}

func NewEvaluator() *Evaluator {
	return &Evaluator{}
}

// Evaluate memproses kondisi hidup & studi mahasiswa berdasarkan 4 Pilar Kehidupan
func (e *Evaluator) Evaluate(input StudentTelemetryInput, now time.Time) ([]TelemetryAlert, error) {
	if strings.TrimSpace(input.UserID) == "" {
		return nil, errors.New("user_id cannot be empty")
	}

	var alerts []TelemetryAlert

	// 1. Pilar #1: Kesehatan & Vitalitas - Bedtime Guardian
	if input.ActiveWorkPastNightHour {
		alerts = append(alerts, TelemetryAlert{
			UserID:    input.UserID,
			AlertType: "BEDTIME_VIOLATION",
			Severity:  SeverityCritical,
			Message:   "🌙 Aktivitas terdeteksi melewati jam cutoff malam (23:00). Prioritaskan tidur untuk pemulihan kognitif.",
			CreatedAt: now,
		})
	}

	// 2. Pilar #1: Kesehatan & Vitalitas - Sleep Debt Radar
	if input.AvgSleepHours7D > 0 && input.AvgSleepHours7D < 6.0 {
		alerts = append(alerts, TelemetryAlert{
			UserID:    input.UserID,
			AlertType: "SLEEP_DEBT_RISK",
			Severity:  SeverityHigh,
			Message:   "⚠️ Rata-rata tidur 7 hari terakhir di bawah 6 jam. Risiko penurunan konsentrasi dan burnout meningkat.",
			CreatedAt: now,
		})
	}

	// 3. Pilar #2: Kuliah & Akademik - Deadline Radar (<24 jam)
	for _, task := range input.PendingDeadlines {
		timeRemaining := task.Deadline.Sub(now)
		if timeRemaining > 0 && timeRemaining <= 24*time.Hour {
			alerts = append(alerts, TelemetryAlert{
				UserID:    input.UserID,
				AlertType: "URGENT_DEADLINE",
				Severity:  SeverityHigh,
				Message:   "🚨 Tugas mendekati batas pengumpulan (<24 jam): " + task.Title,
				CreatedAt: now,
			})
		}
	}

	// 4. Pilar #3: Riset & Skripsi - Anti-Ghosting Dospem Radar (>14 hari)
	if input.DaysSinceDospemMeeting > 14 {
		alerts = append(alerts, TelemetryAlert{
			UserID:    input.UserID,
			AlertType: "DOSPEM_GHOSTING_ALERT",
			Severity:  SeverityMedium,
			Message:   "📡 Sudah lebih dari 14 hari belum bimbingan dengan dosen pembimbing. Jadwalkan update progres bab naskah.",
			CreatedAt: now,
		})
	}

	return alerts, nil
}

