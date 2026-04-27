# DEBUG: injected by python‑injector
#!/usr/bin/env python3
"""Debug function registry and code generation system."""

import pathlib
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)

class DebugStage(Enum):
    """Stages of debug instrumentation in order."""
    INITIALIZATION = "initialization"    # Setup debug globals, imports
    FUNCTION_ENTRY = "function_entry"   # Called at function start
    SUB_TASK = "sub_task"               # Called for significant operations
    DATA_FLOW = "data_flow"             # Called for data processing
    MEMORY_CHECK = "memory_check"       # Called for memory monitoring
    NETWORK_CALL = "network_call"       # Called for network operations
    ERROR_HANDLING = "error_handling"   # Called for error conditions
    FUNCTION_EXIT = "function_exit"     # Called at function end

@dataclass
class DebugFunction:
    """Represents a debug function with all its metadata."""
    name: str
    stage: DebugStage
    signature: str
    language: str
    parameters: List[str]
    returns: Optional[str]
    description: str
    usage_pattern: str
    implementation: str
    dependencies: List[str]  # Required imports/packages
    
class DebugFunctionRegistry:
    """Registry for debug functions by language."""
    
    def __init__(self):
        self.functions_by_language: Dict[str, List[DebugFunction]] = {}
        self.generated_templates: Dict[str, str] = {}
    
    def register_language_functions(self, language: str, service_name: str) -> List[DebugFunction]:
        """Register all debug functions for a specific language."""
        if language.lower() == 'go':
            return self._register_go_functions(service_name)
        elif language.lower() == 'python':
            return self._register_python_functions(service_name)
        elif language.lower() == 'java':
            return self._register_java_functions(service_name)
        else:
            return self._register_generic_functions(language, service_name)
    
    def _register_go_functions(self, service_name: str) -> List[DebugFunction]:
        """Register Go-specific debug functions."""
        functions = [
            DebugFunction(
                name="debug_init",
                stage=DebugStage.INITIALIZATION,
                signature="func init()",
                language="go",
                parameters=[],
                returns=None,
                description="Initialize debug system with environment variables and service name",
                usage_pattern="Automatically called at package initialization",
                implementation="",  # Will be generated
                dependencies=["fmt", "os", "strings", "sync", "time", "runtime"]
            ),
            
            DebugFunction(
                name="debug_enter",
                stage=DebugStage.FUNCTION_ENTRY,
                signature="func debug_enter(functionName string) time.Time",
                language="go",
                parameters=["functionName string"],
                returns="time.Time",
                description="Log function entry with timestamp and memory info",
                usage_pattern="startTime := debug_enter(\"functionName\")",
                implementation="",
                dependencies=["time", "runtime", "fmt"]
            ),
            
            DebugFunction(
                name="debug_exit",
                stage=DebugStage.FUNCTION_EXIT,
                signature="func debug_exit(functionName string, startTime time.Time)",
                language="go", 
                parameters=["functionName string", "startTime time.Time"],
                returns=None,
                description="Log function exit with duration and final memory state",
                usage_pattern="defer debug_exit(\"functionName\", startTime)",
                implementation="",
                dependencies=["time", "runtime", "fmt"]
            ),
            
            DebugFunction(
                name="debug_sub_task",
                stage=DebugStage.SUB_TASK,
                signature="func debug_sub_task(taskName string, fn func())",
                language="go",
                parameters=["taskName string", "fn func()"],
                returns=None,
                description="Execute and time a sub-task within a function",
                usage_pattern="debug_sub_task(\"parsing\", func() { /* code */ })",
                implementation="",
                dependencies=["time", "fmt"]
            ),
            
            DebugFunction(
                name="debug_data_flow",
                stage=DebugStage.DATA_FLOW,
                signature="func debug_data_flow(direction, dataType string, dataSize int64, destination string)",
                language="go",
                parameters=["direction string", "dataType string", "dataSize int64", "destination string"],
                returns=None,
                description="Log data movement with size and destination info",
                usage_pattern="debug_data_flow(\"INPUT\", \"json\", int64(len(data)), \"service\")",
                implementation="",
                dependencies=["fmt", "time"]
            ),
            
            DebugFunction(
                name="debug_memory_check",
                stage=DebugStage.MEMORY_CHECK,
                signature="func debug_memory_check(checkpoint string) int64",
                language="go",
                parameters=["checkpoint string"],
                returns="int64",
                description="Check and log current memory usage at a specific checkpoint",
                usage_pattern="memUsed := debug_memory_check(\"after_allocation\")",
                implementation="",
                dependencies=["runtime", "fmt", "time"]
            ),
            
            DebugFunction(
                name="debug_network_call",
                stage=DebugStage.NETWORK_CALL,
                signature="func debug_network_call(method, url string, requestSize, responseSize int64, duration time.Duration, statusCode int)",
                language="go",
                parameters=["method string", "url string", "requestSize int64", "responseSize int64", "duration time.Duration", "statusCode int"],
                returns=None,
                description="Log network call details with timing and size info",
                usage_pattern="debug_network_call(\"GET\", url, reqSize, respSize, duration, status)",
                implementation="",
                dependencies=["time", "fmt"]
            ),
            
            DebugFunction(
                name="debug_error",
                stage=DebugStage.ERROR_HANDLING,
                signature="func debug_error(location, errorMsg string)",
                language="go",
                parameters=["location string", "errorMsg string"],
                returns=None,
                description="Log error conditions with location context",
                usage_pattern="debug_error(\"functionName\", err.Error())",
                implementation="",
                dependencies=["fmt", "time"]
            )
        ]
        
        self.functions_by_language['go'] = functions
        return functions
    
    def _register_python_functions(self, service_name: str) -> List[DebugFunction]:
        """Register Python-specific debug functions."""
        functions = [
            DebugFunction(
                name="debug_enter",
                stage=DebugStage.FUNCTION_ENTRY,
                signature="def debug_enter(function_name: str) -> float",
                language="python",
                parameters=["function_name: str"],
                returns="float",
                description="Log function entry with timestamp",
                usage_pattern="start_time = debug_enter('function_name')",
                implementation="",
                dependencies=["time", "os", "sys"]
            ),
            
            DebugFunction(
                name="debug_exit",
                stage=DebugStage.FUNCTION_EXIT,
                signature="def debug_exit(function_name: str, start_time: float) -> None",
                language="python",
                parameters=["function_name: str", "start_time: float"],
                returns="None",
                description="Log function exit with duration",
                usage_pattern="debug_exit('function_name', start_time)",
                implementation="",
                dependencies=["time"]
            )
        ]
        
        self.functions_by_language['python'] = functions
        return functions
    
    def _register_java_functions(self, service_name: str) -> List[DebugFunction]:
        """Register Java-specific debug functions."""
        # Similar implementation for Java
        functions = []
        self.functions_by_language['java'] = functions
        return functions
    
    def _register_generic_functions(self, language: str, service_name: str) -> List[DebugFunction]:
        """Register generic debug functions for unknown languages."""
        functions = []
        self.functions_by_language[language] = functions
        return functions
    
    def get_functions_by_stage(self, language: str, stage: DebugStage) -> List[DebugFunction]:
        """Get all functions for a specific debug stage."""
        if language not in self.functions_by_language:
            return []
        
        return [f for f in self.functions_by_language[language] if f.stage == stage]
    
    def get_function_by_name(self, language: str, name: str) -> Optional[DebugFunction]:
        """Get a specific debug function by name."""
        if language not in self.functions_by_language:
            return None
        
        for func in self.functions_by_language[language]:
            if func.name == name:
                return func
        return None
    
    def get_all_functions(self, language: str) -> List[DebugFunction]:
        """Get all debug functions for a language."""
        return self.functions_by_language.get(language, [])
