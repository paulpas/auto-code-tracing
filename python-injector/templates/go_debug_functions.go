// Debug telemetry functions template for Go services
// This template defines the exact function signatures that all files will use

package main

import (
	"fmt"
	"os"
	"runtime"
	"strings"
	"sync"
	"time"
)

// Debug telemetry globals - ONLY DEFINE ONCE PER PACKAGE
var (
	debugEnabled   bool
	serviceName    string
	startupTime    time.Time
	debugMutex     sync.RWMutex
)

func init() {
	// Initialize debug settings
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
		serviceName = "{{SERVICE_NAME}}"  // Template variable
	}
	
	startupTime = time.Now()
}

// Debug function signatures that all files must use consistently
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

func debug_sub(taskName string, fn func()) {
	if !debugEnabled {
		fn()
		return
	}
	
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	
	startTime := time.Now()
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)
	
	fmt.Printf("[TELEMETRY|%s|%d] SUB-TASK-START: %s | Memory-Before: %d bytes\n",
		serviceName, startTime.UnixNano(), taskName, memBefore.HeapInuse)
	
	fn()
	
	endTime := time.Now()
	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)
	duration := endTime.Sub(startTime).Nanoseconds()
	memDelta := int64(memAfter.HeapInuse) - int64(memBefore.HeapInuse)
	
	fmt.Printf("[TELEMETRY|%s|%d] SUB-TASK-END: %s | Duration: %d ns (%.3f ms) | Memory-After: %d bytes | Memory-Delta: %+d bytes\n",
		serviceName, endTime.UnixNano(), taskName, duration, float64(duration)/1e6, memAfter.HeapInuse, memDelta)
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

func debug_memory() int64 {
	if !debugEnabled {
		return 0
	}
	
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	timestamp := time.Now()
	
	fmt.Printf("[TELEMETRY|%s|%d] MEMORY: HeapInuse: %d bytes | HeapAlloc: %d bytes | NumGC: %d\n",
		serviceName, timestamp.UnixNano(), memStats.HeapInuse, memStats.HeapAlloc, memStats.NumGC)
	
	return int64(memStats.HeapInuse)
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
