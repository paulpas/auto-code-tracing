package main

import (
	"fmt"
	"os"
	"runtime"
	"strings"
	"sync"
	"time"
)

// Debug telemetry globals for service: serviceB
var (
	debugEnabled   bool
	serviceName    string
	debugMutex     sync.RWMutex
)

func init() {
	// Initialize debug settings for serviceB
	debugVars := []string{"DEBUG", "DEBUG_MODE", "TRACE", "VERBOSE"}
	for _, envVar := range debugVars {
		if val := os.Getenv(envVar); val != "" {
			debugEnabled = strings.ToLower(val) == "true" || strings.ToLower(val) == "enabled"
			if debugEnabled {
				break
			}
		}
	}
	serviceName = os.Getenv("SERVICE_NAME")
	if serviceName == "" {
		serviceName = "serviceB"
	}
}

func debug_enter(functionName string) time.Time {
	if !debugEnabled {
		return time.Time{}
	}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	fmt.Printf("[TELEMETRY|%s|%d] ENTER: %s | Memory: %d bytes | Goroutines: %d\n",
		serviceName, timestamp.UnixNano(), functionName, memStats.HeapInuse, runtime.NumGoroutine())
	return timestamp
}

func debug_exit(functionName string, startTime time.Time) {
	if !debugEnabled {
		return
	}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	duration := timestamp.Sub(startTime).Nanoseconds()
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	fmt.Printf("[TELEMETRY|%s|%d] EXIT: %s | Duration: %d ns (%.3f ms) | Memory: %d bytes\n",
		serviceName, timestamp.UnixNano(), functionName, duration, float64(duration)/1e6, memStats.HeapInuse)
}

func debug_data_flow(direction, dataType string, dataSize int64, destination string) {
	if !debugEnabled {
		return
	}
	debugMutex.RLock()  
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	fmt.Printf("[TELEMETRY|%s|%d] DATA-FLOW: %s | Type: %s | Size: %d bytes | Destination: %s\n",
		serviceName, timestamp.UnixNano(), direction, dataType, dataSize, destination)
}

func debug_network_call(method, url string, requestSize, responseSize int64, duration time.Duration, statusCode int) {
	if !debugEnabled {
		return
	}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	fmt.Printf("[TELEMETRY|%s|%d] NETWORK: %s %s | Request: %d bytes | Response: %d bytes | Duration: %d ns (%.3f ms) | Status: %d\n",
		serviceName, timestamp.UnixNano(), method, url, requestSize, responseSize, duration.Nanoseconds(), float64(duration.Nanoseconds())/1e6, statusCode)
}

func debug_error(functionName, errorMsg string) {
	if !debugEnabled {
		return
	}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	fmt.Printf("[TELEMETRY|%s|%d] ERROR in %s: %s\n",
		serviceName, timestamp.UnixNano(), functionName, errorMsg)
}
