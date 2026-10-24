package telemetry

import (
	"context"
	"fmt"
	"math"
	"sync"
	"sync/atomic"
	"time"
)

type Dispatcher interface {
	Dispatch(ctx context.Context, alert TelemetryAlert) error
}

type MockDispatcher struct {
	mu           sync.Mutex
	Dispatched   []TelemetryAlert
	ShouldFailOn int
	callCount    int
}

func (m *MockDispatcher) Dispatch(ctx context.Context, alert TelemetryAlert) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.callCount++
	if m.ShouldFailOn > 0 && m.callCount <= m.ShouldFailOn {
		return fmt.Errorf("transient network timeout: attempt %d", m.callCount)
	}
	m.Dispatched = append(m.Dispatched, alert)
	return nil
}

type WorkerPool struct {
	concurrency      int
	alertQueue       chan TelemetryAlert
	dispatcher       Dispatcher
	metrics          *Metrics
	wg               sync.WaitGroup
	quit             chan struct{}
	processedCount   uint64
	retryFailedCount uint64
}

func NewWorkerPool(concurrency int, queueCapacity int, dispatcher Dispatcher, metrics *Metrics) *WorkerPool {
	return &WorkerPool{
		concurrency: concurrency,
		alertQueue:  make(chan TelemetryAlert, queueCapacity),
		dispatcher:  dispatcher,
		metrics:     metrics,
		quit:        make(chan struct{}),
	}
}

func (p *WorkerPool) Start(ctx context.Context) {
	for i := 0; i < p.concurrency; i++ {
		p.wg.Add(1)
		go p.workerLoop(ctx, i)
	}
}

func (p *WorkerPool) Submit(alert TelemetryAlert) bool {
	select {
	case p.alertQueue <- alert:
		return true
	default:
		// Queue full (backpressure)
		return false
	}
}

func (p *WorkerPool) workerLoop(ctx context.Context, workerID int) {
	defer p.wg.Done()
	for {
		select {
		case <-ctx.Done():
			return
		case <-p.quit:
			return
		case alert, ok := <-p.alertQueue:
			if !ok {
				return
			}
			p.processWithRetry(ctx, alert)
		}
	}
}

// processWithRetry mengimplementasikan exponential backoff retry
func (p *WorkerPool) processWithRetry(ctx context.Context, alert TelemetryAlert) {
	maxRetries := 3
	baseDelay := 10 * time.Millisecond

	for attempt := 0; attempt <= maxRetries; attempt++ {
		err := p.dispatcher.Dispatch(ctx, alert)
		if err == nil {
			atomic.AddUint64(&p.processedCount, 1)
			if p.metrics != nil {
				p.metrics.IncAlertsDispatched()
			}
			return
		}

		if attempt < maxRetries {
			delay := time.Duration(float64(baseDelay) * math.Pow(2, float64(attempt)))
			select {
			case <-time.After(delay):
			case <-ctx.Done():
				return
			}
		}
	}

	atomic.AddUint64(&p.retryFailedCount, 1)
}

func (p *WorkerPool) Stop() {
	close(p.quit)
	p.wg.Wait()
}

func (p *WorkerPool) GetStats() (processed uint64, failed uint64) {
	return atomic.LoadUint64(&p.processedCount), atomic.LoadUint64(&p.retryFailedCount)
}

