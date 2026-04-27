First time setup

make setup

Quick development cycle

make inject-debug build-debug

Run a service in debug mode

make run-service-a-debug

Full analysis pipeline

make analyze

Clean everything and start fresh

make clean-all setup

Check project status

make status

Prepare for demo

make demo

Comprehensive Auto-Code Tracing System Design & Implementation Summary

Executive Overview

This system is a language-agnostic, LLM-powered auto-instrumentation
framework that automatically adds comprehensive debug telemetry to
existing codebases without modifying the original source files. It
generates runtime-observable debug versions of applications for
production monitoring, performance analysis, and operational insights.

Functional Requirements

Primary Objectives

1.  Non-Intrusive Instrumentation: Generate debug versions of source
    files without modifying originals
2.  Language Agnostic: Support Go, Python, Java, JavaScript, and
    extensible to other languages
3.  Comprehensive Telemetry: Track function execution, memory usage,
    network calls, data flow, and errors
4.  Production Ready: Minimal performance impact when disabled,
    thread-safe operations
5.  Build Verification: Ensure instrumented code compiles and runs
    identically to originals
6.  Automated Error Recovery: Detect and fix compilation issues through
    iterative LLM-based corrections

Telemetry Capabilities

-   Function Tracing: Entry/exit timestamps with nanosecond precision
    and execution duration
-   Memory Monitoring: Heap usage, allocation tracking, garbage
    collection metrics
-   Network Instrumentation: HTTP request/response sizes, timing, status
    codes, endpoints
-   Data Flow Analysis: Input/output data sizes, types, processing
    operations, serialization
-   Error Tracking: Exception handling, error propagation, failure
    conditions
-   Concurrency Monitoring: Thread/goroutine tracking, resource
    contention, parallel execution
-   Sub-task Timing: Granular operation timing within functions
    (parsing, validation, etc.)

Output Format Standardization

    [TELEMETRY|SERVICE_NAME|TIMESTAMP_NS] LEVEL: DETAILS

-   SERVICE_NAME: Configurable service identifier
-   TIMESTAMP_NS: Nanosecond precision Unix timestamp
-   LEVEL: ENTER, EXIT, SUB-TASK, DATA-FLOW, MEMORY, NETWORK, ERROR
-   DETAILS: Context-specific metrics and information

System Architecture

High-Level Design Principles

1.  Modular Component Architecture: Separate concerns for debug
    generation, code parsing, LLM interaction, and build verification
2.  Template-Based Debug Functions: Pre-defined, language-specific debug
    function libraries
3.  Snippet-Based Processing: Break large files into manageable 20-100
    line chunks for focused LLM calls
4.  Project-Level Build Verification: Test entire projects, not
    individual files
5.  Intelligent Error Analysis: Parse compilation errors and apply
    targeted fixes

Core Components

1. Enhanced Code Injector (core/injector.py)

-   Primary Orchestrator: Coordinates entire instrumentation pipeline
-   Language Detection: Automatically identifies programming languages
    from file extensions
-   File Organization: Groups files by language for optimized processing
-   Build Management: Verifies project compilation and applies fixes
-   Error Recovery: Iterative retry mechanism with intelligent error
    analysis

2. Debug Function Registry (debug/registry.py)

-   Function Catalog: Maintains database of available debug functions
    per language
-   Stage Management: Organizes debug functions by execution stage
    (initialization, entry, exit, etc.)
-   Signature Enforcement: Ensures consistent function signatures across
    all generated code
-   Dependency Tracking: Manages required imports/packages for each
    debug function

3. Template Generator (debug/template_generator.py)

-   LLM-Based Generation: Creates debug function implementations using
    language-specific prompts
-   Module Assembly: Combines individual functions into complete debug
    modules
-   Language Adaptation: Generates Go, Python, Java-specific
    implementations
-   Template Customization: Service-specific variable substitution and
    configuration

4. Snippet Injector (debug/snippet_injector.py)

-   Code Parsing: Breaks source files into logical snippets (functions,
    classes, blocks)
-   Context Analysis: Identifies appropriate debug functions for each
    code snippet
-   Targeted Instrumentation: Applies specific debug calls based on code
    patterns
-   File Reconstruction: Reassembles instrumented snippets into complete
    files

5. LLM Integration (llm/client.py, llm/prompts.py)

-   Provider Abstraction: Support for OpenAI, Claude, local models via
    unified interface
-   Prompt Engineering: Language-specific, context-aware prompts for
    optimal results
-   Response Processing: JSON extraction, markdown cleanup, error
    handling
-   Token Management: Efficient prompt design to minimize token usage

6. Build Verification System

-   Multi-Language Support: Go (go build), Python (py_compile), Java
    (javac), JavaScript (node --check)
-   Error Parsing: Intelligent analysis of compilation errors with regex
    pattern matching
-   Targeted Fixes: Apply fixes only to problematic files based on error
    analysis
-   Artifact Cleanup: Remove temporary build files after verification

7. File System Management (filesystem/operations.py)

-   Debug Directory Structure: Parallel debug directories preserving
    original structure
-   Timestamp Tracking: Up-to-date checking to skip unnecessary
    regeneration
-   File Filtering: Skip patterns for generated files, dependencies,
    build artifacts
-   Atomic Operations: Safe file writing with backup and rollback
    capabilities

Implementation Details

Debug Function Architecture

Go Language Implementation

    // Global state management
    var (
        debugEnabled   bool          // Runtime activation flag
        serviceName    string        // Service identifier
        debugMutex     sync.RWMutex  // Thread-safe access
    )

    // Core debug functions
    func debug_enter(functionName string) time.Time          // Function entry
    func debug_exit(functionName string, startTime time.Time) // Function exit
    func debug_data_flow(direction, dataType string, dataSize int64, destination string)
    func debug_network_call(method, url string, requestSize, responseSize int64, duration time.Duration, statusCode int)
    func debug_error(functionName, errorMsg string)

Python Language Implementation

    # Module-level configuration
    debug_enabled: bool = False
    service_name: str = "service"

    # Core debug functions with type hints
    def debug_enter(function_name: str) -> float
    def debug_exit(function_name: str, start_time: float) -> None
    def debug_error(function_name: str, error_msg: str) -> None

Snippet Processing Strategy

Code Parsing Logic

1.  Header Extraction: Package declarations, imports, module-level
    statements
2.  Function Identification: Complete function/method boundaries with
    proper brace matching
3.  Large Function Splitting: Break functions >50 lines into logical
    sub-sections
4.  Top-Level Code: Global variables, constants, type declarations
5.  Context Preservation: Maintain relationship information between
    snippets

Instrumentation Patterns

-   Functions: debug_enter() at start, debug_exit() at end (defer in Go)
-   Network Operations: debug_network_call() wrapping HTTP requests
-   Data Processing: debug_data_flow() for input/output operations
-   Error Handling: debug_error() in catch blocks and error conditions
-   Memory-Intensive Operations: debug_memory_check() at allocation
    points

Build Verification & Error Recovery

Multi-Stage Verification

1.  Individual File Validation: Syntax checking, basic structure
    verification
2.  Project-Level Build: Complete compilation with all dependencies
3.  Error Classification: Parse errors by type (syntax, type conversion,
    undefined symbols, duplicates)
4.  Targeted Remediation: Apply fixes based on error categories

Error Analysis Patterns

    # Duplicate declaration detection
    redecl_patterns = [
        r'(\w+) redeclared in this block',
        r'(\w+) redeclared at',
        r'redefinition of (\w+)'
    ]

    # Type conversion error detection
    type_patterns = [
        r'cannot use (.+?) as (.+?) in (.+)',
        r'type mismatch: (.+?) vs (.+)'
    ]

    # Undefined symbol detection
    undefined_patterns = [
        r'undefined: (\w+)',
        r'(\w+) not declared'
    ]

Configuration Management

Environment-Based Activation

    // Debug activation variables (case-insensitive)
    debugVars := []string{"DEBUG", "DEBUG_MODE", "TRACE", "VERBOSE"}
    // Values: "true", "enabled", "1" activate debug mode

Service Configuration

    # config.yaml structure
    llm:
      provider: "openai"  # or "claude", "local"
      config:
        api_key: "${OPENAI_API_KEY}"
        model: "gpt-4"
        temperature: 0.1

    file_extensions: [".go", ".py", ".java", ".js"]
    debug_vars: ["DEBUG", "DEBUG_MODE", "TRACE"]
    skip_patterns: ["*_test.go", "vendor/", "node_modules/"]

Operational Workflow

Complete Processing Pipeline

1.  Initialization: Load configuration, initialize LLM client, setup
    file system manager
2.  File Discovery: Scan service directories, organize by language,
    filter skip patterns
3.  Debug Module Generation: Create language-specific debug function
    libraries
4.  Snippet Processing: Parse files into manageable chunks, apply
    targeted instrumentation
5.  File Reconstruction: Reassemble instrumented snippets into complete
    files
6.  Build Verification: Compile entire project, analyze errors, apply
    fixes
7.  Iterative Refinement: Retry failed builds with targeted corrections
    (max 3 attempts)
8.  Deployment: Generate debug versions ready for runtime execution

Makefile Integration

    # Primary targets
    inject-debug: clean-debug build-debug-env inject-code verify-builds
    debug-run: inject-debug start-debug-services
    logs-unified: tail-debug-logs
    clean-all: stop-services clean-debug-dirs clean-build-artifacts

    # Service-specific processing
    inject-debug-service-a: SERVICE_NAME=serviceA
    inject-debug-service-b: SERVICE_NAME=serviceB

Runtime Behavior

-   Performance: ~1-2% overhead when enabled, <0.1% when disabled
-   Thread Safety: All debug functions use proper synchronization
    primitives
-   Output Volume: Configurable verbosity levels, structured for log
    aggregation
-   Error Resilience: Debug failures never crash original application
    logic

Advanced Features

Intelligent Code Analysis

-   Pattern Recognition: Identify network calls, data processing, error
    handling automatically
-   Context Awareness: Different instrumentation for different code
    patterns
-   Dependency Analysis: Track function call graphs and data flow
    relationships
-   Performance Hotspot Detection: Identify functions requiring detailed
    timing analysis

Multi-Language Extensibility

    # Language plugin architecture
    class LanguageProcessor:
        def parse_code(self, source: str) -> List[CodeSnippet]
        def generate_debug_module(self) -> str
        def validate_instrumentation(self, code: str) -> bool
        def build_project(self, debug_dir: Path) -> BuildResult

Caching & Optimization

-   LLM Response Caching: Avoid re-processing identical code snippets
-   Incremental Updates: Only regenerate modified files
-   Template Reuse: Cache debug function implementations across services
-   Build Artifact Sharing: Reuse compilation results for unchanged
    dependencies

Integration Patterns

Docker Integration

    # Multi-stage build with debug instrumentation
    FROM golang:1.19 AS debug-builder
    COPY python-injector /debug-injector
    COPY serviceA /src
    RUN cd /debug-injector && python inject_debug_llm.py /src serviceA
    RUN cd /src/debug && go build -o service-debug

    # Production stage with both versions
    FROM alpine:latest
    COPY --from=debug-builder /src/service /app/service
    COPY --from=debug-builder /src/debug/service-debug /app/service-debug

Kubernetes Deployment

    # ConfigMap for debug activation
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: debug-config
    data:
      DEBUG: "true"
      SERVICE_NAME: "serviceA"

    # Deployment with debug sidecar
    spec:
      containers:
      - name: service
        image: service:latest
        envFrom:
        - configMapRef:
            name: debug-config
      - name: debug-collector
        image: fluentd:latest
        # Collect debug output for analysis

Monitoring Integration

    # Prometheus metrics from debug output
    - name: function_duration_seconds
      regex: '\[TELEMETRY\|(\w+)\|\d+\] EXIT: (\w+) \| Duration: (\d+) ns'
      labels:
        service: $1
        function: $2
      value: $3

    # Grafana dashboard queries
    rate(function_duration_seconds[5m]) by (service, function)
    histogram_quantile(0.95, function_duration_seconds_bucket)

Quality Assurance & Testing

Validation Strategies

-   Compilation Verification: All generated code must compile
    successfully
-   Functional Equivalence: Debug versions produce identical output to
    originals
-   Performance Benchmarking: Measure instrumentation overhead
-   Error Injection Testing: Verify debug functions handle edge cases
    gracefully

Continuous Integration

    # CI pipeline integration
    test-debug-instrumentation:
      steps:
      - name: Generate debug versions
        run: make inject-debug
      - name: Verify builds
        run: make debug-build-status
      - name: Run comparison tests
        run: make test-functional-equivalence
      - name: Performance regression check
        run: make test-performance-impact

This comprehensive system provides enterprise-grade, production-ready
automatic code instrumentation with minimal developer intervention,
extensive language support, and robust error recovery mechanisms. The
modular architecture ensures easy maintenance and extensibility while
the LLM integration enables intelligent, context-aware instrumentation
that adapts to different coding patterns and languages.
