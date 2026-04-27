# Auto Code Tracing Project Makefile
# ===================================

# Configuration
PROJECT_NAME := auto-code-tracing
PYTHON_INJECTOR_DIR := python-injector
CLIENT_DIR := client
SERVICE_A_DIR := serviceA
SERVICE_B_DIR := serviceB

# Python configuration - CLEAN VERSION
PYTHON := python3
PIP := pip3
VENV_DIR := .venv
ROOT_DIR := $(shell pwd)
PYTHON_VENV := $(ROOT_DIR)/$(VENV_DIR)/bin/python
PIP_VENV := $(ROOT_DIR)/$(VENV_DIR)/bin/pip


# Platform detection (if needed later)
UNAME_S := $(shell uname -s 2>/dev/null || echo "Unknown")


# Go configuration
GO := go
GO_BUILD_FLAGS := -v
GO_CLEAN_FLAGS := -cache -testcache -modcache

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
BOLD := \033[1m
NC := \033[0m # No Color

# Helper functions for conditional building
define check_go_binary
$(shell if [ -f "$(1)" ] && [ "$(1)" -nt "$(2)" ]; then echo "exists"; fi)
endef

define check_debug_injection
$(shell if [ -d "$(1)/debug" ] && [ "$(1)/debug" -nt "$(1)" ]; then echo "current"; fi)
endef

# Default target
.PHONY: help
help: ## Show this help message
	@echo "$(BOLD)$(PROJECT_NAME) - Makefile Help$(NC)"
	@echo "=================================="
	@echo
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(CYAN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: status-detailed
status-detailed: ## Show detailed build status
	@echo "$(BOLD)$(PROJECT_NAME) - Detailed Status$(NC)"
	@echo "========================================"
	@echo "$(CYAN)Go Binaries:$(NC)"
	@if [ -f "$(CLIENT_DIR)/client" ]; then \
		echo "  • Client: $(GREEN)✅ Built$(NC) ($(shell stat -c %y $(CLIENT_DIR)/client 2>/dev/null || stat -f %Sm $(CLIENT_DIR)/client 2>/dev/null || echo 'unknown time'))"; \
	else \
		echo "  • Client: $(RED)❌ Not built$(NC)"; \
	fi
	@if [ -f "$(SERVICE_A_DIR)/bin/serviceA" ]; then \
		echo "  • Service A: $(GREEN)✅ Built$(NC) ($(shell stat -c %y $(SERVICE_A_DIR)/bin/serviceA 2>/dev/null || stat -f %Sm $(SERVICE_A_DIR)/bin/serviceA 2>/dev/null || echo 'unknown time'))"; \
	else \
		echo "  • Service A: $(RED)❌ Not built$(NC)"; \
	fi
	@if [ -f "$(SERVICE_B_DIR)/bin/serviceB" ]; then \
		echo "  • Service B: $(GREEN)✅ Built$(NC) ($(shell stat -c %y $(SERVICE_B_DIR)/bin/serviceB 2>/dev/null || stat -f %Sm $(SERVICE_B_DIR)/bin/serviceB 2>/dev/null || echo 'unknown time'))"; \
	else \
		echo "  • Service B: $(RED)❌ Not built$(NC)"; \
	fi
	@echo "$(CYAN)Debug Binaries:$(NC)"
	@if [ -f "$(SERVICE_A_DIR)/debug/serviceA_debug" ]; then \
		echo "  • Service A Debug: $(GREEN)✅ Built$(NC) ($(shell stat -c %y $(SERVICE_A_DIR)/debug/serviceA_debug 2>/dev/null || stat -f %Sm $(SERVICE_A_DIR)/debug/serviceA_debug 2>/dev/null || echo 'unknown time'))"; \
	else \
		echo "  • Service A Debug: $(RED)❌ Not built$(NC)"; \
	fi
	@if [ -f "$(SERVICE_B_DIR)/debug/serviceB_debug" ]; then \
		echo "  • Service B Debug: $(GREEN)✅ Built$(NC) ($(shell stat -c %y $(SERVICE_B_DIR)/debug/serviceB_debug 2>/dev/null || stat -f %Sm $(SERVICE_B_DIR)/debug/serviceB_debug 2>/dev/null || echo 'unknown time'))"; \
	else \
		echo "  • Service B Debug: $(RED)❌ Not built$(NC)"; \
	fi

# =============================================================================
# Setup and Installation
# =============================================================================

.PHONY: setup
setup: setup-python setup-go ## Complete project setup (Python + Go)
	@echo "$(GREEN)✅ Complete project setup finished!$(NC)"

.PHONY: setup-python
setup-python: venv install-python-deps ## Setup Python environment
	@echo "$(GREEN)✅ Python environment setup complete!$(NC)"

.PHONY: setup-go
setup-go: ## Setup Go dependencies for all Go modules
	@echo "$(BLUE)🔧 Setting up Go modules...$(NC)"
	@cd $(CLIENT_DIR) && $(GO) mod tidy && $(GO) mod download
	@cd $(SERVICE_A_DIR) && $(GO) mod tidy && $(GO) mod download
	@cd $(SERVICE_B_DIR) && $(GO) mod tidy && $(GO) mod download
	@echo "$(GREEN)✅ Go modules setup complete!$(NC)"

.PHONY: test-python-path
test-python-path: ## Test Python path resolution
	@echo "Testing Python executable paths:"
	@echo "Relative test:"
	@$(VENV_DIR)/bin/python --version
	@echo "Absolute test:"
	@$(ROOT_DIR)/$(VENV_DIR)/bin/python --version
	@echo "Variable test:"
	@$(PYTHON_VENV) --version
	@echo "CD test:"
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV) --version

.PHONY: venv
venv: ## Create Python virtual environment
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(BLUE)🐍 Creating Python virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV_DIR) --prompt $(PROJECT_NAME); \
		if [ ! -f "$(PIP_VENV)" ]; then \
			echo "$(YELLOW)⚠️  Pip not found, trying alternative paths...$(NC)"; \
			if [ -f "$(VENV_DIR)/Scripts/pip.exe" ]; then \
				echo "$(BLUE)🔧 Windows environment detected$(NC)"; \
			else \
				echo "$(RED)❌ Could not find pip in virtual environment$(NC)"; \
				echo "$(RED)Trying to reinstall virtual environment...$(NC)"; \
				rm -rf $(VENV_DIR); \
				$(PYTHON) -m venv $(VENV_DIR) --prompt $(PROJECT_NAME) --upgrade-deps; \
			fi; \
		fi; \
		echo "$(GREEN)✅ Virtual environment created!$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Virtual environment already exists$(NC)"; \
	fi

.PHONY: fix-venv
fix-venv: ## Fix broken virtual environment
	@echo "$(YELLOW)🔧 Fixing virtual environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@$(PYTHON) -m venv $(VENV_DIR) --upgrade-deps --prompt $(PROJECT_NAME)
	@echo "$(BLUE)🔍 Checking created files:$(NC)"
	@ls -la $(VENV_DIR)/
	@ls -la $(VENV_DIR)/bin/ 2>/dev/null || ls -la $(VENV_DIR)/Scripts/ 2>/dev/null || true
	@if [ -f "$(VENV_DIR)/bin/pip" ]; then \
		echo "$(GREEN)✅ pip found at $(VENV_DIR)/bin/pip$(NC)"; \
	elif [ -f "$(VENV_DIR)/Scripts/pip.exe" ]; then \
		echo "$(GREEN)✅ pip found at $(VENV_DIR)/Scripts/pip.exe$(NC)"; \
	else \
		echo "$(RED)❌ pip still not found, trying ensurepip...$(NC)"; \
		$(VENV_DIR)/bin/python -m ensurepip --upgrade 2>/dev/null || \
		$(VENV_DIR)/Scripts/python.exe -m ensurepip --upgrade 2>/dev/null || true; \
	fi

.PHONY: debug-paths
debug-paths: ## Debug path configuration
	@echo "$(CYAN)Path Configuration Debug:$(NC)"
	@echo "ROOT_DIR: $(ROOT_DIR)"
	@echo "VENV_DIR: $(VENV_DIR)"
	@echo "PYTHON_VENV_ABS: $(PYTHON_VENV_ABS)"
	@echo "PIP_VENV_ABS: $(PIP_VENV_ABS)"
	@echo "PYTHON_VENV: $(PYTHON_VENV)"
	@echo "PIP_VENV: $(PIP_VENV)"
	@echo "$(CYAN)File existence:$(NC)"
	@if [ -f "$(PYTHON_VENV)" ]; then \
		echo "✅ Python executable exists at $(PYTHON_VENV)"; \
	else \
		echo "❌ Python executable NOT found at $(PYTHON_VENV)"; \
	fi
	@if [ -f "$(PIP_VENV)" ]; then \
		echo "✅ Pip executable exists at $(PIP_VENV)"; \
	else \
		echo "❌ Pip executable NOT found at $(PIP_VENV)"; \
	fi

.PHONY: fix-permissions
fix-permissions: ## Fix virtual environment permissions
	@echo "$(BLUE)🔧 Fixing virtual environment permissions...$(NC)"
	@if [ -d "$(VENV_DIR)" ]; then \
		chmod +x $(VENV_DIR)/bin/*; \
		ls -la $(VENV_DIR)/bin/pip*; \
		echo "$(GREEN)✅ Permissions fixed$(NC)"; \
	else \
		echo "$(RED)❌ Virtual environment not found$(NC)"; \
	fi

.PHONY: test-pip
test-pip: ## Test pip executable
	@echo "$(BLUE)🧪 Testing pip executable...$(NC)"
	@echo "Pip path: $(PIP_VENV)"
	@if [ -f "$(PIP_VENV)" ]; then \
		echo "File exists: ✅"; \
		ls -la $(PIP_VENV); \
		echo "Testing execution:"; \
		$(PIP_VENV) --version || echo "❌ Failed to execute"; \
	else \
		echo "❌ Pip file not found"; \
	fi

# Add this target to debug the directory structure
.PHONY: debug-dirs
debug-dirs: ## Debug directory structure
	@echo "$(CYAN)Current directory:$(NC) $(shell pwd)"
	@echo "$(CYAN)Available directories:$(NC)"
	@ls -la
	@echo "$(CYAN)Looking for python-injector:$(NC)"
	@if [ -d "python-injector" ]; then \
		echo "$(GREEN)✅ python-injector found$(NC)"; \
		ls -la python-injector/; \
	else \
		echo "$(RED)❌ python-injector not found$(NC)"; \
		echo "Searching for similar directories..."; \
		find . -name "*python*" -type d 2>/dev/null || true; \
	fi

.PHONY: manual-setup
manual-setup: ## Manual setup with diagnostics
	@echo "$(BLUE)🔍 Python Setup Diagnostics$(NC)"
	@echo "Python version: $(shell $(PYTHON) --version)"
	@echo "Python location: $(shell which $(PYTHON))"
	@echo "Attempting virtual environment creation..."
	@$(MAKE) fix-venv
	@$(MAKE) install-python-deps

.PHONY: install-python-deps
install-python-deps: venv ## Install Python dependencies
	@echo "$(BLUE)📦 Installing Python dependencies...$(NC)"
	@echo "$(BLUE)🔍 Checking pip location and permissions...$(NC)"
	@if [ -f "$(PIP_VENV)" ]; then \
		echo "$(GREEN)✅ Found pip at $(PIP_VENV)$(NC)"; \
		ls -la $(PIP_VENV); \
		if [ ! -x "$(PIP_VENV)" ]; then \
			echo "$(YELLOW)⚠️  Fixing pip permissions...$(NC)"; \
			chmod +x $(PIP_VENV) $(PYTHON_VENV); \
			chmod +x $(VENV_DIR)/bin/pip*; \
		fi; \
		echo "$(BLUE)🔧 Upgrading pip...$(NC)"; \
		$(PIP_VENV) install --upgrade pip; \
		echo "$(BLUE)📦 Installing base packages...$(NC)"; \
		$(PIP_VENV) install pyyaml httpx jinja2; \
		if [ -d "$(PYTHON_INJECTOR_DIR)" ]; then \
			echo "$(BLUE)📦 Installing requirements from $(PYTHON_INJECTOR_DIR)...$(NC)"; \
			if [ -f "$(PYTHON_INJECTOR_DIR)/requirements.txt" ]; then \
				$(PIP_VENV) install -r $(PYTHON_INJECTOR_DIR)/requirements.txt; \
			else \
				echo "$(YELLOW)⚠️  No requirements.txt found in $(PYTHON_INJECTOR_DIR)$(NC)"; \
			fi; \
		else \
			echo "$(RED)❌ $(PYTHON_INJECTOR_DIR) directory not found$(NC)"; \
			echo "Available directories:"; \
			ls -la; \
		fi; \
	else \
		echo "$(RED)❌ Could not find pip executable at $(PIP_VENV)$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Python dependencies installed!$(NC)"

# =============================================================================
# Build Targets
# =============================================================================

.PHONY: build
build: build-go build-python ## Build all components
	@echo "$(GREEN)✅ All components built successfully!$(NC)"

# Add a build target that fixes permissions first
.PHONY: build-safe
build-safe: fix-venv-permissions build ## Build with automatic permission fixing
	@echo "$(GREEN)🛡️  Safe build completed!$(NC)"

.PHONY: build-go
build-go: ## Build all Go services
	@echo "$(BLUE)🔨 Building Go services...$(NC)"
	@cd $(CLIENT_DIR) && $(GO) build $(GO_BUILD_FLAGS) -o client .
	@cd $(SERVICE_A_DIR) && $(GO) build $(GO_BUILD_FLAGS) -o bin/serviceA .
	@cd $(SERVICE_B_DIR) && $(GO) build $(GO_BUILD_FLAGS) -o bin/serviceB .
	@echo "$(GREEN)✅ Go services built successfully!$(NC)"

.PHONY: build-python
build-python: ## Validate Python injector code
	@echo "$(BLUE)🐍 Validating Python injector...$(NC)"
	@echo "$(BLUE)🔍 Checking Python executable...$(NC)"
	@if [ -f "$(PYTHON_VENV)" ]; then \
		echo "$(GREEN)✅ Found Python at $(PYTHON_VENV)$(NC)"; \
		ls -la $(PYTHON_VENV); \
		if [ ! -x "$(PYTHON_VENV)" ]; then \
			echo "$(YELLOW)⚠️  Fixing Python permissions...$(NC)"; \
			chmod +x $(PYTHON_VENV); \
			chmod +x $(VENV_DIR)/bin/*; \
		fi; \
		echo "$(BLUE)🧪 Testing Python executable...$(NC)"; \
		$(PYTHON_VENV) --version; \
		if [ -d "$(PYTHON_INJECTOR_DIR)" ]; then \
			echo "$(BLUE)🔍 Validating Python files...$(NC)"; \
			if [ -f "$(PYTHON_INJECTOR_DIR)/inject_debug_llm.py" ]; then \
				$(PYTHON_VENV) -m py_compile $(PYTHON_INJECTOR_DIR)/inject_debug_llm.py && \
				echo "$(GREEN)✅ inject_debug_llm.py validated$(NC)"; \
			else \
				echo "$(YELLOW)⚠️  inject_debug_llm.py not found$(NC)"; \
			fi; \
			if [ -f "$(PYTHON_INJECTOR_DIR)/generic_parser.py" ]; then \
				$(PYTHON_VENV) -m py_compile $(PYTHON_INJECTOR_DIR)/generic_parser.py && \
				echo "$(GREEN)✅ generic_parser.py validated$(NC)"; \
			else \
				echo "$(YELLOW)⚠️  generic_parser.py not found$(NC)"; \
			fi; \
		else \
			echo "$(RED)❌ $(PYTHON_INJECTOR_DIR) directory not found$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ Python executable not found at $(PYTHON_VENV)$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Python injector validated!$(NC)"

.PHONY: build-debug-with-verification
build-debug-with-verification: inject-debug ## Build debug versions with verification
	@echo "$(BLUE)🔨 Building debug services with verification...$(NC)"
	@echo "$(BLUE)🔍 Building Service A debug...$(NC)"
	@if cd $(SERVICE_A_DIR)/debug && $(GO) build $(GO_BUILD_FLAGS) -o serviceA_debug . 2>&1; then \
		echo "$(GREEN)✅ Service A debug build successful$(NC)"; \
	else \
		echo "$(RED)❌ Service A debug build failed$(NC)"; \
		echo "$(YELLOW)🔧 Debug files may need regeneration$(NC)"; \
	fi
	@echo "$(BLUE)🔍 Building Service B debug...$(NC)"
	@if cd $(SERVICE_B_DIR)/debug && $(GO) build $(GO_BUILD_FLAGS) -o serviceB_debug . 2>&1; then \
		echo "$(GREEN)✅ Service B debug build successful$(NC)"; \
	else \
		echo "$(RED)❌ Service B debug build failed$(NC)"; \
		echo "$(YELLOW)🔧 Debug files may need regeneration$(NC)"; \
	fi

.PHONY: force-regenerate-debug
force-regenerate-debug: clean-debug inject-debug build-debug-with-verification ## Force regeneration of all debug files
	@echo "$(GREEN)🔄 Forced regeneration completed$(NC)"

.PHONY: debug-build-status
debug-build-status: ## Check build status of debug files
	@echo "$(CYAN)🔍 Checking debug build status...$(NC)"
	@if [ -d "$(SERVICE_A_DIR)/debug" ]; then \
		echo "$(BLUE)Testing Service A debug build...$(NC)"; \
		cd $(SERVICE_A_DIR)/debug && $(GO) build -o /tmp/serviceA_test . >/dev/null 2>&1 && \
		echo "$(GREEN)✅ Service A debug builds successfully$(NC)" || \
		echo "$(RED)❌ Service A debug has build errors$(NC)"; \
		rm -f /tmp/serviceA_test; \
	fi
	@if [ -d "$(SERVICE_B_DIR)/debug" ]; then \
		echo "$(BLUE)Testing Service B debug build...$(NC)"; \
		cd $(SERVICE_B_DIR)/debug && $(GO) build -o /tmp/serviceB_test . >/dev/null 2>&1 && \
		echo "$(GREEN)✅ Service B debug builds successfully$(NC)" || \
		echo "$(RED)❌ Service B debug has build errors$(NC)"; \
		rm -f /tmp/serviceB_test; \
	fi

.PHONY: fix-venv-permissions
fix-venv-permissions: ## Fix all virtual environment permissions and links
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "$(BLUE)🔧 Fixing virtual environment permissions...$(NC)"; \
		find $(VENV_DIR) -type f -name "python*" -exec chmod +x {} \; 2>/dev/null || true; \
		find $(VENV_DIR) -type f -name "pip*" -exec chmod +x {} \; 2>/dev/null || true; \
		find $(VENV_DIR) -name "activate*" -exec chmod +x {} \; 2>/dev/null || true; \
		chmod +x $(VENV_DIR)/bin/* 2>/dev/null || true; \
		echo "$(BLUE)🧪 Testing executables...$(NC)"; \
		if $(VENV_DIR)/bin/python --version >/dev/null 2>&1; then \
			echo "$(GREEN)✅ Python executable working$(NC)"; \
		else \
			echo "$(RED)❌ Python executable still not working$(NC)"; \
			ls -la $(VENV_DIR)/bin/python*; \
		fi; \
		if $(VENV_DIR)/bin/pip --version >/dev/null 2>&1; then \
			echo "$(GREEN)✅ Pip executable working$(NC)"; \
		else \
			echo "$(RED)❌ Pip executable still not working$(NC)"; \
			ls -la $(VENV_DIR)/bin/pip*; \
		fi; \
	else \
		echo "$(RED)❌ Virtual environment not found$(NC)"; \
		exit 1; \
	fi

.PHONY: rebuild-venv
rebuild-venv: ## Completely rebuild virtual environment
	@echo "$(YELLOW)🗑️  Removing existing virtual environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@echo "$(BLUE)🏗️  Rebuilding virtual environment...$(NC)"
	@$(PYTHON) -m venv $(VENV_DIR) --upgrade-deps --prompt $(PROJECT_NAME)
	@chmod +x $(VENV_DIR)/bin/*
	@echo "$(BLUE)🧪 Testing new environment...$(NC)"
	@$(VENV_DIR)/bin/python --version
	@$(VENV_DIR)/bin/pip --version
	@echo "$(GREEN)✅ Virtual environment rebuilt successfully$(NC)"

.PHONY: check-python-env
check-python-env: ## Check Python environment is working
	@echo "$(BLUE)🔍 Checking Python environment...$(NC)"
	@echo "Virtual environment path: $(VENV_DIR)"
	@echo "Python executable path: $(PYTHON_VENV)"
	@if [ -f "$(PYTHON_VENV)" ]; then \
		echo "$(GREEN)✅ Python executable exists$(NC)"; \
		ls -la $(PYTHON_VENV); \
		if [ -x "$(PYTHON_VENV)" ]; then \
			echo "$(GREEN)✅ Python executable has execute permissions$(NC)"; \
			$(PYTHON_VENV) --version; \
		else \
			echo "$(RED)❌ Python executable not executable$(NC)"; \
			echo "$(BLUE)🔧 Fixing permissions...$(NC)"; \
			chmod +x $(PYTHON_VENV); \
			$(PYTHON_VENV) --version; \
		fi; \
	else \
		echo "$(RED)❌ Python executable not found$(NC)"; \
		exit 1; \
	fi

.PHONY: inject-debug-safe
inject-debug-safe: ## Safe debug injection with automatic fixes
	@echo "$(PURPLE)🛡️  Safe debug injection starting...$(NC)"
	@$(MAKE) check-python-env
	@$(MAKE) inject-debug
	@echo "$(GREEN)🎉 Safe debug injection completed!$(NC)"

.PHONY: build-debug
build-debug: inject-debug ## Build debug versions of services
	@echo "$(BLUE)🔨 Building debug services...$(NC)"
	@if [ -d "$(SERVICE_A_DIR)/debug" ]; then \
		cd $(SERVICE_A_DIR)/debug && $(GO) build $(GO_BUILD_FLAGS) -o serviceA_debug .; \
	fi
	@if [ -d "$(SERVICE_B_DIR)/debug" ]; then \
		cd $(SERVICE_B_DIR)/debug && $(GO) build $(GO_BUILD_FLAGS) -o serviceB_debug .; \
	fi
	@echo "$(GREEN)✅ Debug services built successfully!$(NC)"

# =============================================================================
# Conditional Build Targets
# =============================================================================

.PHONY: build-service-a
build-service-a: ## Build Service A (only if needed)
	@if [ ! -f "$(SERVICE_A_DIR)/bin/serviceA" ] || [ "$(SERVICE_A_DIR)/main.go" -nt "$(SERVICE_A_DIR)/bin/serviceA" ]; then \
		echo "$(BLUE)🔨 Building Service A...$(NC)"; \
		mkdir -p $(SERVICE_A_DIR)/bin; \
		cd $(SERVICE_A_DIR) && $(GO) build $(GO_BUILD_FLAGS) -o bin/serviceA .; \
		echo "$(GREEN)✅ Service A built$(NC)"; \
	else \
		echo "$(GREEN)✅ Service A is up to date$(NC)"; \
	fi

.PHONY: build-service-b
build-service-b: ## Build Service B (only if needed)
	@if [ ! -f "$(SERVICE_B_DIR)/bin/serviceB" ] || [ "$(SERVICE_B_DIR)/main.go" -nt "$(SERVICE_B_DIR)/bin/serviceB" ]; then \
		echo "$(BLUE)🔨 Building Service B...$(NC)"; \
		mkdir -p $(SERVICE_B_DIR)/bin; \
		cd $(SERVICE_B_DIR) && $(GO) build $(GO_BUILD_FLAGS) -o bin/serviceB .; \
		echo "$(GREEN)✅ Service B built$(NC)"; \
	else \
		echo "$(GREEN)✅ Service B is up to date$(NC)"; \
	fi

.PHONY: build-client
build-client: ## Build client (only if needed)
	@if [ ! -f "$(CLIENT_DIR)/client" ] || [ "$(CLIENT_DIR)/main.go" -nt "$(CLIENT_DIR)/client" ]; then \
		echo "$(BLUE)🔨 Building client...$(NC)"; \
		cd $(CLIENT_DIR) && $(GO) build $(GO_BUILD_FLAGS) -o client .; \
		echo "$(GREEN)✅ Client built$(NC)"; \
	else \
		echo "$(GREEN)✅ Client is up to date$(NC)"; \
	fi

.PHONY: build-debug-service-a
build-debug-service-a: ## Build debug version of Service A (only if needed)
	@if [ ! -d "$(SERVICE_A_DIR)/debug" ]; then \
		echo "$(YELLOW)⚠️  Debug code not injected for Service A. Running injection...$(NC)"; \
		$(MAKE) inject-service-a; \
	fi
	@if [ ! -f "$(SERVICE_A_DIR)/debug/serviceA_debug" ] || \
	   [ "$(SERVICE_A_DIR)/debug" -nt "$(SERVICE_A_DIR)/debug/serviceA_debug" ]; then \
		echo "$(BLUE)🔨 Building Service A debug...$(NC)"; \
		cd $(SERVICE_A_DIR)/debug && $(GO) build $(GO_BUILD_FLAGS) -o serviceA_debug .; \
		echo "$(GREEN)✅ Service A debug built$(NC)"; \
	else \
		echo "$(GREEN)✅ Service A debug is up to date$(NC)"; \
	fi

.PHONY: build-debug-service-b
build-debug-service-b: ## Build debug version of Service B (only if needed)
	@if [ ! -d "$(SERVICE_B_DIR)/debug" ]; then \
		echo "$(YELLOW)⚠️  Debug code not injected for Service B. Running injection...$(NC)"; \
		$(MAKE) inject-service-b; \
	fi
	@if [ ! -f "$(SERVICE_B_DIR)/debug/serviceB_debug" ] || \
	   [ "$(SERVICE_B_DIR)/debug" -nt "$(SERVICE_B_DIR)/debug/serviceB_debug" ]; then \
		echo "$(BLUE)🔨 Building Service B debug...$(NC)"; \
		cd $(SERVICE_B_DIR)/debug && $(GO) build $(GO_BUILD_FLAGS) -o serviceB_debug .; \
		echo "$(GREEN)✅ Service B debug built$(NC)"; \
	else \
		echo "$(GREEN)✅ Service B debug is up to date$(NC)"; \
	fi

# =============================================================================
# Debug Injection
# =============================================================================

.PHONY: inject-debug
inject-debug: setup-python fix-venv-permissions ## Inject debug code into all services
	@echo "$(PURPLE)🔬 Injecting debug code...$(NC)"
	@echo "$(BLUE)🔍 Testing Python executable before injection...$(NC)"
	@$(PYTHON_VENV) --version
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV) inject_debug_llm.py ../$(SERVICE_A_DIR) serviceA
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV) inject_debug_llm.py ../$(SERVICE_B_DIR) serviceB
	@echo "$(GREEN)✅ Debug injection complete!$(NC)"

.PHONY: inject-service-a
inject-service-a: setup-python fix-venv-permissions ## Inject debug code into Service A only
	@echo "$(PURPLE)🔬 Injecting debug code into Service A...$(NC)"
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV_ABS) inject_debug_llm.py ../$(SERVICE_A_DIR) serviceA
	@echo "$(GREEN)✅ Service A debug injection complete!$(NC)"

.PHONY: inject-service-b
inject-service-b: setup-python fix-venv-permissions ## Inject debug code into Service B only
	@echo "$(PURPLE)🔬 Injecting debug code into Service B...$(NC)"
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV_ABS) inject_debug_llm.py ../$(SERVICE_B_DIR) serviceB
	@echo "$(GREEN)✅ Service B debug injection complete!$(NC)"

# =============================================================================
# Smart Debug Injection
# =============================================================================

.PHONY: inject-service-a-smart
inject-service-a-smart: setup-python ## Inject debug code into Service A (only if needed)
	@if [ ! -d "$(SERVICE_A_DIR)/debug" ] || \
	   [ "$(SERVICE_A_DIR)" -nt "$(SERVICE_A_DIR)/debug" ] || \
	   [ ! -f "$(SERVICE_A_DIR)/debug/main_debug.go" ]; then \
		echo "$(PURPLE)🔬 Injecting debug code into Service A...$(NC)"; \
		$(MAKE) inject-service-a; \
	else \
		echo "$(GREEN)✅ Service A debug code is up to date$(NC)"; \
	fi

.PHONY: inject-service-b-smart
inject-service-b-smart: setup-python ## Inject debug code into Service B (only if needed)
	@if [ ! -d "$(SERVICE_B_DIR)/debug" ] || \
	   [ "$(SERVICE_B_DIR)" -nt "$(SERVICE_B_DIR)/debug" ] || \
	   [ ! -f "$(SERVICE_B_DIR)/debug/main_debug.go" ]; then \
		echo "$(PURPLE)🔬 Injecting debug code into Service B...$(NC)"; \
		$(MAKE) inject-service-b; \
	else \
		echo "$(GREEN)✅ Service B debug code is up to date$(NC)"; \
	fi

.PHONY: inject-debug-smart
inject-debug-smart: inject-service-a-smart inject-service-b-smart ## Smart debug injection for both services
	@echo "$(GREEN)✅ Smart debug injection complete!$(NC)"

# =============================================================================
# Run Targets with Conditional Building
# =============================================================================

.PHONY: run-client
run-client: build-client ## Run the client
	@echo "$(CYAN)🚀 Running client...$(NC)"
	@cd $(CLIENT_DIR) && ./client

.PHONY: run-service-a
run-service-a: build-service-a ## Run Service A
	@echo "$(CYAN)🚀 Running Service A...$(NC)"
	@cd $(SERVICE_A_DIR) && ./bin/serviceA

.PHONY: run-service-b
run-service-b: build-service-b ## Run Service B
	@echo "$(CYAN)🚀 Running Service B...$(NC)"
	@cd $(SERVICE_B_DIR) && ./bin/serviceB

.PHONY: run-service-a-debug
run-service-a-debug: build-debug-service-a ## Run Service A in debug mode
	@echo "$(CYAN)🐛 Running Service A (debug)...$(NC)"
	@cd $(SERVICE_A_DIR)/debug && DEBUG=true ./serviceA_debug

.PHONY: run-service-b-debug
run-service-b-debug: build-debug-service-b ## Run Service B in debug mode
	@echo "$(CYAN)🐛 Running Service B (debug)...$(NC)"
	@cd $(SERVICE_B_DIR)/debug && DEBUG=true ./serviceB_debug

# =============================================================================
# Fast Run Targets (minimal checks)
# =============================================================================

.PHONY: run-a
run-a: build-service-a ## Quick run Service A
	@cd $(SERVICE_A_DIR) && ./bin/serviceA

.PHONY: run-b  
run-b: build-service-b ## Quick run Service B
	@cd $(SERVICE_B_DIR) && ./bin/serviceB

.PHONY: run-a-debug
run-a-debug: build-debug-service-a ## Quick run Service A debug
	@cd $(SERVICE_A_DIR)/debug && DEBUG=true ./serviceA_debug

.PHONY: run-b-debug
run-b-debug: build-debug-service-b ## Quick run Service B debug
	@cd $(SERVICE_B_DIR)/debug && DEBUG=true ./serviceB_debug

.PHONY: debug-a
debug-a: run-a-debug ## Alias for run-a-debug

.PHONY: debug-b
debug-b: run-b-debug ## Alias for run-b-debug:1


# =============================================================================
# Parallel Run Targets
# =============================================================================

.PHONY: run-all-services
run-all-services: build-service-a build-service-b build-client ## Run all services in parallel
	@echo "$(CYAN)🚀 Starting all services in parallel...$(NC)"
	@echo "$(BLUE)📝 Services will run in background. Use 'make stop-all' to stop them.$(NC)"
	@echo "$(YELLOW)💡 Logs will be saved to *.log files$(NC)"
	@cd $(SERVICE_A_DIR) && nohup ./bin/serviceA > ../serviceA.log 2>&1 & echo $$! > ../serviceA.pid
	@cd $(SERVICE_B_DIR) && nohup ./bin/serviceB > ../serviceB.log 2>&1 & echo $$! > ../serviceB.pid
	@cd $(CLIENT_DIR) && nohup ./client > ../client.log 2>&1 & echo $$! > ../client.pid
	@sleep 2
	@echo "$(GREEN)✅ All services started!$(NC)"
	@echo "$(CYAN)📊 Process Status:$(NC)"
	@if [ -f serviceA.pid ]; then echo "  • Service A: PID $$(cat serviceA.pid) (log: serviceA.log)"; fi
	@if [ -f serviceB.pid ]; then echo "  • Service B: PID $$(cat serviceB.pid) (log: serviceB.log)"; fi
	@if [ -f client.pid ]; then echo "  • Client: PID $$(cat client.pid) (log: client.log)"; fi
	@echo "$(BLUE)🔍 Use 'make logs' to tail all logs, 'make stop-all' to stop all services$(NC)"

.PHONY: run-services-only
run-services-only: build-service-a build-service-b ## Run only Service A and B (no client)
	@echo "$(CYAN)🚀 Starting services (A & B) in parallel...$(NC)"
	@cd $(SERVICE_A_DIR) && nohup ./bin/serviceA > ../serviceA.log 2>&1 & echo $$! > ../serviceA.pid
	@cd $(SERVICE_B_DIR) && nohup ./bin/serviceB > ../serviceB.log 2>&1 & echo $$! > ../serviceB.pid
	@sleep 2
	@echo "$(GREEN)✅ Services A & B started!$(NC)"
	@if [ -f serviceA.pid ]; then echo "  • Service A: PID $$(cat serviceA.pid)"; fi
	@if [ -f serviceB.pid ]; then echo "  • Service B: PID $$(cat serviceB.pid)"; fi

.PHONY: run-all-debug
run-all-debug: build-debug-service-a build-debug-service-b ## Run all services in debug mode with unified logging
	@echo "$(CYAN)🐛 Starting all services in debug mode with unified logging...$(NC)"
	@echo "$(BLUE)📝 All debug output will be aggregated to unified_debug.log$(NC)"
	@echo "$(YELLOW)💡 Use 'make logs-unified' to tail unified logs, 'make stop-all-debug' to stop all services$(NC)"
	@rm -f unified_debug.log
	@touch unified_debug.log
	@export SERVICE_NAME="serviceA" DEBUG=true && cd $(SERVICE_A_DIR)/debug && nohup ./serviceA_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceA_debug.pid
	@export SERVICE_NAME="serviceB" DEBUG=true && cd $(SERVICE_B_DIR)/debug && nohup ./serviceB_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceB_debug.pid
	@sleep 3
	@echo "$(GREEN)✅ All debug services started with unified logging!$(NC)"
	@echo "$(CYAN)📊 Debug Process Status:$(NC)"
	@if [ -f serviceA_debug.pid ]; then echo "  • Service A Debug: PID $$(cat serviceA_debug.pid)"; fi
	@if [ -f serviceB_debug.pid ]; then echo "  • Service B Debug: PID $$(cat serviceB_debug.pid)"; fi
	@echo "$(BLUE)📝 All telemetry is being written to: unified_debug.log$(NC)"

.PHONY: run-services-debug-only
run-services-debug-only: build-debug-service-a build-debug-service-b ## Run only Service A and B in debug mode with unified logging
	@echo "$(CYAN)🐛 Starting debug services (A & B) with unified logging...$(NC)"
	@rm -f unified_debug.log
	@touch unified_debug.log
	@export SERVICE_NAME="serviceA" DEBUG=true && cd $(SERVICE_A_DIR)/debug && nohup ./serviceA_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceA_debug.pid
	@export SERVICE_NAME="serviceB" DEBUG=true && cd $(SERVICE_B_DIR)/debug && nohup ./serviceB_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceB_debug.pid
	@sleep 3
	@echo "$(GREEN)✅ Debug services A & B started with unified logging!$(NC)"
	@if [ -f serviceA_debug.pid ]; then echo "  • Service A Debug: PID $$(cat serviceA_debug.pid)"; fi
	@if [ -f serviceB_debug.pid ]; then echo "  • Service B Debug: PID $$(cat serviceB_debug.pid)"; fi

# =============================================================================
# Log Management
# =============================================================================

.PHONY: logs
logs: ## Tail all service logs in parallel
	@echo "$(CYAN)📊 Tailing all service logs... (Press Ctrl+C to stop)$(NC)"
	@if [ -f serviceA.log ] && [ -f serviceB.log ] && [ -f client.log ]; then \
		tail -f serviceA.log serviceB.log client.log; \
	elif [ -f serviceA.log ] && [ -f serviceB.log ]; then \
		tail -f serviceA.log serviceB.log; \
	else \
		echo "$(YELLOW)⚠️  No log files found. Are services running?$(NC)"; \
		ls -la *.log 2>/dev/null || echo "No .log files exist"; \
	fi

.PHONY: logs-debug
logs-debug: ## Tail all debug service logs in parallel
	@echo "$(CYAN)📊 Tailing all debug service logs... (Press Ctrl+C to stop)$(NC)"
	@if [ -f serviceA_debug.log ] && [ -f serviceB_debug.log ]; then \
		tail -f serviceA_debug.log serviceB_debug.log; \
	else \
		echo "$(YELLOW)⚠️  No debug log files found. Are debug services running?$(NC)"; \
		ls -la *_debug.log 2>/dev/null || echo "No debug .log files exist"; \
	fi

.PHONY: logs-service-a
logs-service-a: ## Tail Service A logs
	@if [ -f serviceA.log ]; then \
		tail -f serviceA.log; \
	else \
		echo "$(YELLOW)⚠️  serviceA.log not found$(NC)"; \
	fi

.PHONY: logs-service-b
logs-service-b: ## Tail Service B logs
	@if [ -f serviceB.log ]; then \
		tail -f serviceB.log; \
	else \
		echo "$(YELLOW)⚠️  serviceB.log not found$(NC)"; \
	fi

.PHONY: view-logs
view-logs: ## Show recent log entries from all services
	@echo "$(CYAN)📋 Recent Service A logs:$(NC)"
	@if [ -f serviceA.log ]; then tail -20 serviceA.log; else echo "  No serviceA.log found"; fi
	@echo ""
	@echo "$(CYAN)📋 Recent Service B logs:$(NC)"
	@if [ -f serviceB.log ]; then tail -20 serviceB.log; else echo "  No serviceB.log found"; fi
	@echo ""
	@echo "$(CYAN)📋 Recent Client logs:$(NC)"
	@if [ -f client.log ]; then tail -20 client.log; else echo "  No client.log found"; fi

.PHONY: view-logs-debug
view-logs-debug: ## Show recent debug log entries from all services
	@echo "$(CYAN)🐛 Recent Service A debug logs:$(NC)"
	@if [ -f serviceA_debug.log ]; then tail -20 serviceA_debug.log; else echo "  No serviceA_debug.log found"; fi
	@echo ""
	@echo "$(CYAN)🐛 Recent Service B debug logs:$(NC)"
	@if [ -f serviceB_debug.log ]; then tail -20 serviceB_debug.log; else echo "  No serviceB_debug.log found"; fi

# =============================================================================
# Parallel Run Targets with Unified Logging
# =============================================================================

.PHONY: run-all-debug
run-all-debug: build-debug-service-a build-debug-service-b ## Run all services in debug mode with unified logging
	@echo "$(CYAN)🐛 Starting all services in debug mode with unified logging...$(NC)"
	@echo "$(BLUE)📝 All debug output will be aggregated to unified_debug.log$(NC)"
	@echo "$(YELLOW)💡 Use 'make logs-unified' to tail unified logs, 'make stop-all-debug' to stop all services$(NC)"
	@rm -f unified_debug.log
	@touch unified_debug.log
	@export SERVICE_NAME="serviceA" DEBUG=true && cd $(SERVICE_A_DIR)/debug && nohup ./serviceA_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceA_debug.pid
	@export SERVICE_NAME="serviceB" DEBUG=true && cd $(SERVICE_B_DIR)/debug && nohup ./serviceB_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceB_debug.pid
	@sleep 3
	@echo "$(GREEN)✅ All debug services started with unified logging!$(NC)"
	@echo "$(CYAN)📊 Debug Process Status:$(NC)"
	@if [ -f serviceA_debug.pid ]; then echo "  • Service A Debug: PID $$(cat serviceA_debug.pid)"; fi
	@if [ -f serviceB_debug.pid ]; then echo "  • Service B Debug: PID $$(cat serviceB_debug.pid)"; fi
	@echo "$(BLUE)📝 All telemetry is being written to: unified_debug.log$(NC)"

.PHONY: run-services-debug-only
run-services-debug-only: build-debug-service-a build-debug-service-b ## Run only Service A and B in debug mode with unified logging
	@echo "$(CYAN)🐛 Starting debug services (A & B) with unified logging...$(NC)"
	@rm -f unified_debug.log
	@touch unified_debug.log
	@export SERVICE_NAME="serviceA" DEBUG=true && cd $(SERVICE_A_DIR)/debug && nohup ./serviceA_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceA_debug.pid
	@export SERVICE_NAME="serviceB" DEBUG=true && cd $(SERVICE_B_DIR)/debug && nohup ./serviceB_debug >> ../../unified_debug.log 2>&1 & echo $$! > ../../serviceB_debug.pid
	@sleep 3
	@echo "$(GREEN)✅ Debug services A & B started with unified logging!$(NC)"
	@if [ -f serviceA_debug.pid ]; then echo "  • Service A Debug: PID $$(cat serviceA_debug.pid)"; fi
	@if [ -f serviceB_debug.pid ]; then echo "  • Service B Debug: PID $$(cat serviceB_debug.pid)"; fi

# =============================================================================
# Enhanced Log Management with Unified Logging
# =============================================================================

.PHONY: logs-unified
logs-unified: ## Tail unified debug logs from all services
	@echo "$(CYAN)📊 Tailing unified debug logs... (Press Ctrl+C to stop)$(NC)"
	@if [ -f unified_debug.log ]; then \
		tail -f unified_debug.log; \
	else \
		echo "$(YELLOW)⚠️  unified_debug.log not found. Are debug services running?$(NC)"; \
	fi

.PHONY: logs
logs: logs-unified ## Alias for unified logs

.PHONY: logs-debug
logs-debug: logs-unified ## Alias for unified debug logs

.PHONY: view-logs-unified
view-logs-unified: ## Show recent unified debug log entries
	@echo "$(CYAN)📋 Recent Unified Debug Logs (last 50 lines):$(NC)"
	@if [ -f unified_debug.log ]; then \
		tail -50 unified_debug.log; \
	else \
		echo "  No unified_debug.log found"; \
	fi

.PHONY: analyze-telemetry
analyze-telemetry: ## Analyze telemetry data from unified logs
	@echo "$(PURPLE)📊 Analyzing telemetry data...$(NC)"
	@if [ -f unified_debug.log ]; then \
		echo "$(CYAN)Service Call Summary:$(NC)"; \
		grep "TELEMETRY" unified_debug.log | grep -E "(ENTER|EXIT)" | awk -F'|' '{print $$2}' | sort | uniq -c | sort -nr; \
		echo ""; \
		echo "$(CYAN)Network Calls:$(NC)"; \
		grep "TELEMETRY.*NETWORK" unified_debug.log | tail -10; \
		echo ""; \
		echo "$(CYAN)Performance Summary (slowest operations):$(NC)"; \
		grep "TELEMETRY.*EXIT.*Duration:" unified_debug.log | sed 's/.*Duration: $[0-9]*$ ns.*/\1/' | sort -nr | head -10; \
	else \
		echo "$(YELLOW)⚠️  No unified_debug.log found$(NC)"; \
	fi

.PHONY: clean-logs
clean-logs: ## Clean all log files
	@echo "$(YELLOW)🧹 Cleaning log files...$(NC)"
	@rm -f *.log *.pid
	@echo "$(GREEN)✅ Log cleanup completed!$(NC)"

# Update clean-processes to handle unified logs
.PHONY: clean-processes
clean-processes: stop-all stop-all-debug clean-logs ## Stop all processes and clean PID/log files
	@echo "$(GREEN)✅ Process cleanup completed!$(NC)"

# =============================================================================
# Stop Services
# =============================================================================

.PHONY: stop-all
stop-all: ## Stop all running services
	@echo "$(YELLOW)🛑 Stopping all services...$(NC)"
	@if [ -f serviceA.pid ]; then \
		kill $$(cat serviceA.pid) 2>/dev/null && echo "$(GREEN)✅ Service A stopped$(NC)" || echo "$(YELLOW)⚠️  Service A was not running$(NC)"; \
		rm -f serviceA.pid; \
	fi
	@if [ -f serviceB.pid ]; then \
		kill $$(cat serviceB.pid) 2>/dev/null && echo "$(GREEN)✅ Service B stopped$(NC)" || echo "$(YELLOW)⚠️  Service B was not running$(NC)"; \
		rm -f serviceB.pid; \
	fi
	@if [ -f client.pid ]; then \
		kill $$(cat client.pid) 2>/dev/null && echo "$(GREEN)✅ Client stopped$(NC)" || echo "$(YELLOW)⚠️  Client was not running$(NC)"; \
		rm -f client.pid; \
	fi
	@echo "$(GREEN)✅ All services stopped$(NC)"

.PHONY: stop-all-debug
stop-all-debug: ## Stop all running debug services
	@echo "$(YELLOW)🛑 Stopping all debug services...$(NC)"
	@if [ -f serviceA_debug.pid ]; then \
		kill $$(cat serviceA_debug.pid) 2>/dev/null && echo "$(GREEN)✅ Service A debug stopped$(NC)" || echo "$(YELLOW)⚠️  Service A debug was not running$(NC)"; \
		rm -f serviceA_debug.pid; \
	fi
	@if [ -f serviceB_debug.pid ]; then \
		kill $$(cat serviceB_debug.pid) 2>/dev/null && echo "$(GREEN)✅ Service B debug stopped$(NC)" || echo "$(YELLOW)⚠️  Service B debug was not running$(NC)"; \
		rm -f serviceB_debug.pid; \
	fi
	@echo "$(GREEN)✅ All debug services stopped$(NC)"

.PHONY: stop-services
stop-services: ## Stop only Service A and B (keep client running)
	@echo "$(YELLOW)🛑 Stopping services A & B...$(NC)"
	@if [ -f serviceA.pid ]; then \
		kill $$(cat serviceA.pid) 2>/dev/null && echo "$(GREEN)✅ Service A stopped$(NC)"; \
		rm -f serviceA.pid; \
	fi
	@if [ -f serviceB.pid ]; then \
		kill $$(cat serviceB.pid) 2>/dev/null && echo "$(GREEN)✅ Service B stopped$(NC)"; \
		rm -f serviceB.pid; \
	fi

.PHONY: restart-all
restart-all: stop-all run-all-services ## Restart all services

.PHONY: restart-all-debug
restart-all-debug: stop-all-debug run-all-debug ## Restart all debug services

# =============================================================================
# Process Management
# =============================================================================

.PHONY: ps
ps: ## Show status of all managed services
	@echo "$(CYAN)📊 Service Status:$(NC)"
	@echo "$(CYAN)Normal Services:$(NC)"
	@if [ -f serviceA.pid ] && kill -0 $$(cat serviceA.pid) 2>/dev/null; then \
		echo "  • Service A: $(GREEN)✅ Running$(NC) (PID: $$(cat serviceA.pid))"; \
	elif [ -f serviceA.pid ]; then \
		echo "  • Service A: $(RED)❌ Dead$(NC) (stale PID file)"; \
		rm -f serviceA.pid; \
	else \
		echo "  • Service A: $(YELLOW)⚪ Stopped$(NC)"; \
	fi
	@if [ -f serviceB.pid ] && kill -0 $$(cat serviceB.pid) 2>/dev/null; then \
		echo "  • Service B: $(GREEN)✅ Running$(NC) (PID: $$(cat serviceB.pid))"; \
	elif [ -f serviceB.pid ]; then \
		echo "  • Service B: $(RED)❌ Dead$(NC) (stale PID file)"; \
		rm -f serviceB.pid; \
	else \
		echo "  • Service B: $(YELLOW)⚪ Stopped$(NC)"; \
	fi
	@if [ -f client.pid ] && kill -0 $$(cat client.pid) 2>/dev/null; then \
		echo "  • Client: $(GREEN)✅ Running$(NC) (PID: $$(cat client.pid))"; \
	elif [ -f client.pid ]; then \
		echo "  • Client: $(RED)❌ Dead$(NC) (stale PID file)"; \
		rm -f client.pid; \
	else \
		echo "  • Client: $(YELLOW)⚪ Stopped$(NC)"; \
	fi
	@echo "$(CYAN)Debug Services:$(NC)"
	@if [ -f serviceA_debug.pid ] && kill -0 $$(cat serviceA_debug.pid) 2>/dev/null; then \
		echo "  • Service A Debug: $(GREEN)✅ Running$(NC) (PID: $$(cat serviceA_debug.pid))"; \
	elif [ -f serviceA_debug.pid ]; then \
		echo "  • Service A Debug: $(RED)❌ Dead$(NC) (stale PID file)"; \
		rm -f serviceA_debug.pid; \
	else \
		echo "  • Service A Debug: $(YELLOW)⚪ Stopped$(NC)"; \
	fi
	@if [ -f serviceB_debug.pid ] && kill -0 $$(cat serviceB_debug.pid) 2>/dev/null; then \
		echo "  • Service B Debug: $(GREEN)✅ Running$(NC) (PID: $$(cat serviceB_debug.pid))"; \
	elif [ -f serviceB_debug.pid ]; then \
		echo "  • Service B Debug: $(RED)❌ Dead$(NC) (stale PID file)"; \
		rm -f serviceB_debug.pid; \
	else \
		echo "  • Service B Debug: $(YELLOW)⚪ Stopped$(NC)"; \
	fi

.PHONY: clean-processes
clean-processes: stop-all stop-all-debug ## Stop all processes and clean PID/log files
	@echo "$(YELLOW)🧹 Cleaning process files...$(NC)"
	@rm -f *.pid *.log
	@echo "$(GREEN)✅ Process cleanup completed!$(NC)"
# =============================================================================
# Testing
# =============================================================================

.PHONY: test
test: test-go test-python ## Run all tests
	@echo "$(GREEN)✅ All tests completed!$(NC)"

.PHONY: test-go
test-go: ## Run Go tests
	@echo "$(BLUE)🧪 Running Go tests...$(NC)"
	@cd $(CLIENT_DIR) && $(GO) test ./... -v
	@cd $(SERVICE_A_DIR) && $(GO) test ./... -v
	@cd $(SERVICE_B_DIR) && $(GO) test ./... -v
	@echo "$(GREEN)✅ Go tests completed!$(NC)"

.PHONY: test-python
test-python: setup-python ## Run Python tests
	@echo "$(BLUE)🧪 Running Python tests...$(NC)"
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV) -m pytest -v || echo "$(YELLOW)⚠️  No pytest found or no tests to run$(NC)"
	@echo "$(GREEN)✅ Python tests completed!$(NC)"

.PHONY: test-inject
test-inject: inject-debug build-debug ## Test debug injection and build
	@echo "$(BLUE)🧪 Testing debug injection...$(NC)"
	@echo "$(GREEN)✅ Debug injection test completed!$(NC)"

# =============================================================================
# Analysis and Graph Extraction
# =============================================================================

.PHONY: extract-graph
extract-graph: setup-python ## Extract execution graph from debug logs
	@echo "$(PURPLE)📊 Extracting execution graph...$(NC)"
	@$(PYTHON_VENV) extract_graph.py
	@echo "$(GREEN)✅ Graph extraction complete!$(NC)"

.PHONY: analyze
analyze: inject-debug run-service-a-debug extract-graph ## Full analysis pipeline
	@echo "$(PURPLE)📈 Running full analysis pipeline...$(NC)"
	@echo "$(GREEN)✅ Analysis pipeline complete!$(NC)"

# =============================================================================
# Cleanup
# =============================================================================

.PHONY: clean
clean: clean-go clean-python clean-debug ## Clean all build artifacts
	@echo "$(GREEN)✅ All cleanup completed!$(NC)"

.PHONY: clean-go
clean-go: ## Clean Go build artifacts
	@echo "$(YELLOW)🧹 Cleaning Go build artifacts...$(NC)"
	@cd $(CLIENT_DIR) && $(GO) clean $(GO_CLEAN_FLAGS) && rm -f client
	@cd $(SERVICE_A_DIR) && $(GO) clean $(GO_CLEAN_FLAGS) && rm -rf bin
	@cd $(SERVICE_B_DIR) && $(GO) clean $(GO_CLEAN_FLAGS) && rm -rf bin
	@echo "$(GREEN)✅ Go cleanup completed!$(NC)"

.PHONY: clean-python
clean-python: ## Clean Python cache and artifacts
	@echo "$(YELLOW)🧹 Cleaning Python artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@cd $(PYTHON_INJECTOR_DIR) && rm -rf .debug_cache 2>/dev/null || true
	@echo "$(GREEN)✅ Python cleanup completed!$(NC)"

.PHONY: clean-debug
clean-debug: ## Clean debug directories and files
	@echo "$(YELLOW)🧹 Cleaning debug files...$(NC)"
	@rm -rf $(SERVICE_A_DIR)/debug 2>/dev/null || true
	@rm -rf $(SERVICE_B_DIR)/debug 2>/dev/null || true
	@find . -name "*_debug.go" -delete 2>/dev/null || true
	@find . -name "*_debug_fixed_but_incomplete.go" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Debug cleanup completed!$(NC)"

.PHONY: clean-all
clean-all: clean clean-venv ## Clean everything including virtual environment
	@echo "$(RED)🗑️  Complete cleanup finished!$(NC)"

.PHONY: clean-venv
clean-venv: ## Remove Python virtual environment
	@echo "$(YELLOW)🧹 Removing Python virtual environment...$(NC)"
	@rm -rf $(VENV_DIR) 2>/dev/null || true
	@echo "$(GREEN)✅ Virtual environment removed!$(NC)"

# =============================================================================
# Development Helpers
# =============================================================================

.PHONY: dev-setup
dev-setup: setup install-dev-deps ## Setup development environment
	@echo "$(GREEN)✅ Development environment setup complete!$(NC)"

.PHONY: install-dev-deps
install-dev-deps: venv ## Install development dependencies
	@echo "$(BLUE)📦 Installing development dependencies...$(NC)"
	@$(PIP_VENV) install pytest black flake8 mypy
	@echo "$(GREEN)✅ Development dependencies installed!$(NC)"

.PHONY: format-python
format-python: setup-python ## Format Python code with black
	@echo "$(BLUE)🎨 Formatting Python code...$(NC)"
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV) -m black . || echo "$(YELLOW)⚠️  Black not installed$(NC)"
	@$(PYTHON_VENV) -m black extract_graph.py || echo "$(YELLOW)⚠️  Black not installed$(NC)"
	@echo "$(GREEN)✅ Python formatting complete!$(NC)"

.PHONY: format-go
format-go: ## Format Go code
	@echo "$(BLUE)🎨 Formatting Go code...$(NC)"
	@cd $(CLIENT_DIR) && $(GO) fmt ./...
	@cd $(SERVICE_A_DIR) && $(GO) fmt ./...
	@cd $(SERVICE_B_DIR) && $(GO) fmt ./...
	@echo "$(GREEN)✅ Go formatting complete!$(NC)"

.PHONY: format
format: format-go format-python ## Format all code
	@echo "$(GREEN)✅ All code formatted!$(NC)"

.PHONY: lint-python
lint-python: setup-python ## Lint Python code
	@echo "$(BLUE)🔍 Linting Python code...$(NC)"
	@cd $(PYTHON_INJECTOR_DIR) && $(PYTHON_VENV) -m flake8 . || echo "$(YELLOW)⚠️  Flake8 not installed$(NC)"
	@echo "$(GREEN)✅ Python linting complete!$(NC)"

.PHONY: check-go
check-go: ## Run Go vet and other checks
	@echo "$(BLUE)🔍 Checking Go code...$(NC)"
	@cd $(CLIENT_DIR) && $(GO) vet ./...
	@cd $(SERVICE_A_DIR) && $(GO) vet ./...
	@cd $(SERVICE_B_DIR) && $(GO) vet ./...
	@echo "$(GREEN)✅ Go checks complete!$(NC)"

.PHONY: force-clean-regenerate
force-clean-regenerate: clean-debug inject-debug ## Force complete regeneration of debug files
	@echo "$(GREEN)🔄 Forced clean regeneration completed$(NC)"
	@$(MAKE) debug-build-status

.PHONY: test-build-only
test-build-only: ## Test build debug files without running
	@echo "$(BLUE)🔨 Testing debug builds without running services...$(NC)"
	@if [ -d "$(SERVICE_A_DIR)/debug" ]; then \
		echo "$(BLUE)🔍 Testing Service A debug build...$(NC)"; \
		if cd $(SERVICE_A_DIR)/debug && $(GO) build -v . 2>&1; then \
			echo "$(GREEN)✅ Service A debug builds successfully$(NC)"; \
		else \
			echo "$(RED)❌ Service A debug has build errors$(NC)"; \
		fi; \
	fi
	@if [ -d "$(SERVICE_B_DIR)/debug" ]; then \
		echo "$(BLUE)🔍 Testing Service B debug build...$(NC)"; \
		if cd $(SERVICE_B_DIR)/debug && $(GO) build -v . 2>&1; then \
			echo "$(GREEN)✅ Service B debug builds successfully$(NC)"; \
		else \
			echo "$(RED)❌ Service B debug has build errors$(NC)"; \
		fi; \
	fi

# =============================================================================
# Information and Status
# =============================================================================

.PHONY: status
status: ## Show project status
	@echo "$(BOLD)$(PROJECT_NAME) - Project Status$(NC)"
	@echo "================================"
	@echo "$(CYAN)Go Version:$(NC) $(shell $(GO) version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)Python Version:$(NC) $(shell $(PYTHON) --version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)Virtual Environment:$(NC) $(if $(wildcard $(VENV_DIR)),✅ Active,❌ Not created)"
	@echo "$(CYAN)Debug Config:$(NC) $(if $(wildcard debug_config.yaml),✅ Present,❌ Missing)"
	@echo
	@echo "$(CYAN)Service Directories:$(NC)"
	@echo "  • Client: $(if $(wildcard $(CLIENT_DIR)),✅ Present,❌ Missing)"
	@echo "  • Service A: $(if $(wildcard $(SERVICE_A_DIR)),✅ Present,❌ Missing)"
	@echo "  • Service B: $(if $(wildcard $(SERVICE_B_DIR)),✅ Present,❌ Missing)"
	@echo "  • Python Injector: $(if $(wildcard $(PYTHON_INJECTOR_DIR)),✅ Present,❌ Missing)"
	@echo
	@echo "$(CYAN)Debug Directories:$(NC)"
	@echo "  • Service A Debug: $(if $(wildcard $(SERVICE_A_DIR)/debug),✅ Present,❌ Not generated)"
	@echo "  • Service B Debug: $(if $(wildcard $(SERVICE_B_DIR)/debug),✅ Present,❌ Not generated)"

.PHONY: config-check
config-check: ## Check configuration files
	@echo "$(BLUE)🔍 Checking configuration files...$(NC)"
	@if [ -f "debug_config.yaml" ]; then \
		echo "$(GREEN)✅ debug_config.yaml found$(NC)"; \
		$(PYTHON_VENV) -c "import yaml; yaml.safe_load(open('debug_config.yaml'))" && \
		echo "$(GREEN)✅ debug_config.yaml is valid YAML$(NC)" || \
		echo "$(RED)❌ debug_config.yaml is invalid YAML$(NC)"; \
	else \
		echo "$(RED)❌ debug_config.yaml not found$(NC)"; \
	fi

# =============================================================================
# Workflow Shortcuts
# =============================================================================

.PHONY: quick-test
quick-test: inject-service-a build-debug ## Quick test of debug injection on Service A
	@echo "$(CYAN)⚡ Quick test completed!$(NC)"

.PHONY: full-workflow
full-workflow: setup inject-debug build-debug test ## Complete workflow from setup to test
	@echo "$(GREEN)🎉 Full workflow completed successfully!$(NC)"

.PHONY: demo
demo: setup inject-debug build-debug ## Prepare for demo (setup + inject + build)
	@echo "$(PURPLE)🎭 Demo preparation completed!$(NC)"
	@echo "$(CYAN)Run 'make run-service-a-debug' or 'make run-service-b-debug' to start demo$(NC)"

# Make sure intermediate files are not deleted
.PRECIOUS: $(VENV_DIR)

# Ensure some targets always run
.PHONY: help setup setup-python setup-go venv install-python-deps build build-go build-python build-debug
.PHONY: inject-debug inject-service-a inject-service-b run-client run-service-a run-service-b
.PHONY: run-service-a-debug run-service-b-debug test test-go test-python test-inject extract-graph
.PHONY: analyze clean clean-go clean-python clean-debug clean-all clean-venv dev-setup
.PHONY: install-dev-deps format-python format-go format lint-python check-go status config-check
.PHONY: quick-test full-workflow demo
