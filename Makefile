# Makefile for WebApp Manager

# Variables
PYTHON := python3
PIP := pip3
VENV := venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
PIP_VENV := $(VENV_BIN)/pip
PACKAGE_NAME := webapp_manager
TESTS_DIR := tests
DOCS_DIR := docs

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.PHONY: help
help:
	@echo "$(BLUE)WebApp Manager - Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo "  $(GREEN)help$(NC)              - Show this help message"
	@echo "  $(GREEN)install$(NC)           - Install the package in development mode"
	@echo "  $(GREEN)install-dev$(NC)       - Install development dependencies"
	@echo "  $(GREEN)venv$(NC)              - Create virtual environment"
	@echo "  $(GREEN)clean$(NC)             - Clean build artifacts"
	@echo "  $(GREEN)test$(NC)              - Run tests"
	@echo "  $(GREEN)test-coverage$(NC)     - Run tests with coverage"
	@echo "  $(GREEN)lint$(NC)              - Run linting checks"
	@echo "  $(GREEN)format$(NC)            - Format code with black"
	@echo "  $(GREEN)build$(NC)             - Build distribution packages"
	@echo "  $(GREEN)docs$(NC)              - Generate documentation"
	@echo "  $(GREEN)serve-docs$(NC)        - Serve documentation locally"
	@echo "  $(GREEN)check$(NC)             - Run all checks (lint, test, format)"
	@echo "  $(GREEN)dev-setup$(NC)         - Complete development setup"
	@echo "  $(GREEN)uninstall$(NC)         - Uninstall the package"
	@echo "  $(GREEN)install-system-deps$(NC) - Install system dependencies"
	@echo "  $(GREEN)fix-nodejs$(NC)        - Fix Node.js conflicts"
	@echo "  $(GREEN)fix-line-endings$(NC)  - Fix Windows line endings"
	@echo "  $(GREEN)install-complete$(NC)  - Complete installation (recommended)"
	@echo "  $(GREEN)install-clean$(NC)     - Clean installation without pip"
	@echo "  $(GREEN)install-with-pip$(NC)  - Install with pip override"
	@echo "  $(GREEN)install-global$(NC)    - Install webapp-manager globally"
	@echo "  $(GREEN)run$(NC)               - Run locally without installation"
	@echo "  $(GREEN)create-alias$(NC)      - Create local alias"
	@echo "  $(GREEN)uninstall-global$(NC)  - Remove global installation"
	@echo "  $(GREEN)debug-install$(NC)     - Debug installation issues"
	@echo "  $(GREEN)test-install$(NC)      - Test installation works"
	@echo ""

# Create virtual environment
.PHONY: venv
venv:
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(PIP_VENV) install --upgrade pip setuptools wheel
	@echo "$(GREEN)Virtual environment created successfully!$(NC)"
	@echo "$(YELLOW)Activate with: source $(VENV)/bin/activate$(NC)"

# Install package in development mode
.PHONY: install
install:
	@echo "$(BLUE)Installing package in development mode...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)Package installed successfully!$(NC)"

# Install development dependencies
.PHONY: install-dev
install-dev:
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -e .[dev]
	@echo "$(GREEN)Development dependencies installed successfully!$(NC)"

# Clean build artifacts
.PHONY: clean
clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "$(GREEN)Clean completed!$(NC)"

# Run tests
.PHONY: test
test:
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR) -v
	@echo "$(GREEN)Tests completed!$(NC)"

# Run tests with coverage
.PHONY: test-coverage
test-coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR) --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

# Run linting checks
.PHONY: lint
lint:
	@echo "$(BLUE)Running linting checks...$(NC)"
	$(PYTHON) -m flake8 $(PACKAGE_NAME) $(TESTS_DIR) --count --select=E9,F63,F7,F82 --show-source --statistics
	$(PYTHON) -m flake8 $(PACKAGE_NAME) $(TESTS_DIR) --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "$(GREEN)Linting completed!$(NC)"

# Format code with black
.PHONY: format
format:
	@echo "$(BLUE)Formatting code with black...$(NC)"
	$(PYTHON) -m black $(PACKAGE_NAME) $(TESTS_DIR)
	@echo "$(GREEN)Code formatted successfully!$(NC)"

# Build distribution packages
.PHONY: build
build: clean
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)Build completed! Check dist/ directory$(NC)"

# Generate documentation
.PHONY: docs
docs:
	@echo "$(BLUE)Generating documentation...$(NC)"
	mkdir -p $(DOCS_DIR)
	@echo "# WebApp Manager Documentation" > $(DOCS_DIR)/README.md
	@echo "Version: 3.0.0" >> $(DOCS_DIR)/README.md
	@echo "## Package Structure" >> $(DOCS_DIR)/README.md
	@echo "- webapp_manager.core.manager - Main manager class" >> $(DOCS_DIR)/README.md
	@echo "- webapp_manager.services - Service modules" >> $(DOCS_DIR)/README.md
	@echo "- webapp_manager.cli - Command line interface" >> $(DOCS_DIR)/README.md
	@echo "- webapp_manager.utils - Utility functions" >> $(DOCS_DIR)/README.md
	@echo "- webapp_manager.models - Data models" >> $(DOCS_DIR)/README.md
	@echo "- webapp_manager.config - Configuration management" >> $(DOCS_DIR)/README.md
	@echo "$(GREEN)Documentation generated in $(DOCS_DIR)/$(NC)"

# Serve documentation locally
.PHONY: serve-docs
serve-docs:
	@echo "$(BLUE)Serving documentation locally...$(NC)"
	cd $(DOCS_DIR) && $(PYTHON) -m http.server 8000
	@echo "$(YELLOW)Documentation available at http://localhost:8000$(NC)"

# Run all checks
.PHONY: check
check: lint test format
	@echo "$(GREEN)All checks passed!$(NC)"

# Complete development setup
.PHONY: dev-setup
dev-setup: venv install-dev
	@echo "$(GREEN)Development setup completed!$(NC)"
	@echo "$(YELLOW)Don't forget to activate your virtual environment:$(NC)"
	@echo "  source $(VENV)/bin/activate"

# Uninstall package
.PHONY: uninstall
uninstall:
	@echo "$(BLUE)Uninstalling package...$(NC)"
	@if $(PIP) show $(PACKAGE_NAME) >/dev/null 2>&1; then \
		echo "$(BLUE)Removing package with pip...$(NC)"; \
		$(PIP) uninstall -y $(PACKAGE_NAME) 2>/dev/null || \
		$(PIP) uninstall -y $(PACKAGE_NAME) --break-system-packages 2>/dev/null || \
		echo "$(YELLOW)Could not uninstall with pip, continuing...$(NC)"; \
	fi
	@if [ -f /usr/local/bin/webapp-manager ]; then \
		echo "$(BLUE)Removing global installation...$(NC)"; \
		sudo rm -f /usr/local/bin/webapp-manager; \
		sudo rm -rf /opt/webapp-manager; \
	fi
	@echo "$(GREEN)Package uninstalled successfully!$(NC)"

# Install system dependencies (Ubuntu/Debian)
.PHONY: install-system-deps
install-system-deps:
	@echo "$(BLUE)Installing system dependencies...$(NC)"
	sudo apt-get update
	@echo "$(BLUE)Installing Python and nginx...$(NC)"
	sudo apt-get install -y python3 python3-pip python3-venv nginx python3-dialog
	@echo "$(BLUE)Installing Node.js and npm...$(NC)"
	@if command -v node >/dev/null 2>&1; then \
		echo "$(GREEN)Node.js already installed: $$(node --version)$(NC)"; \
	else \
		curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && \
		sudo apt-get install -y nodejs; \
	fi
	@echo "$(GREEN)System dependencies installed!$(NC)"

# Fix Node.js conflicts
.PHONY: fix-nodejs
fix-nodejs:
	@echo "$(BLUE)Fixing Node.js conflicts...$(NC)"
	@echo "$(YELLOW)Removing conflicting packages...$(NC)"
	sudo apt-get remove -y nodejs npm
	sudo apt-get autoremove -y
	@echo "$(BLUE)Installing Node.js from NodeSource...$(NC)"
	curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
	sudo apt-get install -y nodejs
	@echo "$(GREEN)Node.js conflicts resolved!$(NC)"
	@echo "$(GREEN)Node.js version: $$(node --version)$(NC)"
	@echo "$(GREEN)npm version: $$(npm --version)$(NC)"

# Fix line endings (Windows to Unix)
.PHONY: fix-line-endings
fix-line-endings:
	@echo "$(BLUE)Fixing line endings...$(NC)"
	sed -i 's/\r$$//' webapp-manager.py
	find webapp_manager/ -name "*.py" -exec sed -i 's/\r$$//' {} \;
	@echo "$(GREEN)Line endings fixed!$(NC)"

# Check if running as root (for system operations)
.PHONY: check-root
check-root:
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "$(RED)This operation requires root privileges$(NC)"; \
		exit 1; \
	fi

# Complete installation (recommended)
.PHONY: install-complete
install-complete: fix-line-endings install-global
	@echo "$(BLUE)Complete WebApp Manager installation...$(NC)"
	@echo "$(BLUE)Verifying installation...$(NC)"
	webapp-manager --help || echo "$(YELLOW)Installation completed but command may need path adjustment$(NC)"
	@echo "$(GREEN)Installation completed successfully!$(NC)"
	@echo ""
	@echo "$(YELLOW)⚠️  IMPORTANTE: Ejecuta el comando de configuración inicial:$(NC)"
	@echo "$(CYAN)   sudo webapp-manager setup$(NC)"
	@echo ""
	@echo "$(YELLOW)Este comando configurará:$(NC)"
	@echo "  • Páginas de mantenimiento en /apps/maintenance/"
	@echo "  • Verificación de conflictos con nginx default"
	@echo "  • Directorios y permisos necesarios"
	@echo ""
	@echo "$(YELLOW)Uso: webapp-manager --help$(NC)"

# Clean installation without pip (for externally-managed environments)
.PHONY: install-clean
install-clean: fix-line-endings install-global
	@echo "$(BLUE)Clean WebApp Manager installation (no pip)...$(NC)"
	@echo "$(BLUE)Verifying installation...$(NC)"
	webapp-manager --help || echo "$(YELLOW)Installation completed but command may need path adjustment$(NC)"
	@echo "$(GREEN)Clean installation completed successfully!$(NC)"
	@echo "$(YELLOW)Usage: webapp-manager --help$(NC)"

# Alternative installation with pip override
.PHONY: install-with-pip
install-with-pip: fix-line-endings
	@echo "$(BLUE)Installing with pip override...$(NC)"
	pip3 install -e . --break-system-packages
	sudo $(MAKE) install-global
	webapp-manager --help || echo "$(YELLOW)Installation completed but command may need path adjustment$(NC)"
	@echo "$(GREEN)Installation with pip completed!$(NC)"

# Run locally without installation
.PHONY: run
run:
	@echo "$(BLUE)Running webapp-manager locally...$(NC)"
	python3 webapp-manager.py $(ARGS)

# Create local alias for easy usage
.PHONY: create-alias
create-alias:
	@echo "$(BLUE)Creating local alias...$(NC)"
	@echo "alias webapp-manager='cd $(PWD) && python3 webapp-manager.py'" >> ~/.bashrc
	@echo "$(GREEN)Alias created! Run 'source ~/.bashrc' to activate$(NC)"
	@echo "$(YELLOW)Usage: webapp-manager --help$(NC)"

# Install webapp-manager globally
.PHONY: install-global
install-global: check-root
	@echo "$(BLUE)Installing webapp-manager globally...$(NC)"
	@if [ ! -f webapp-manager.py ]; then \
		echo "$(RED)Error: webapp-manager.py not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Validating Python syntax...$(NC)"
	@python3 -m py_compile webapp-manager.py || (echo "$(RED)Error: Invalid Python syntax$(NC)" && exit 1)
	@echo "$(BLUE)Creating installation directory...$(NC)"
	sudo mkdir -p /opt/webapp-manager
	sudo cp -r webapp_manager/ /opt/webapp-manager/
	sudo cp -r apps/ /opt/webapp-manager/ 2>/dev/null || echo "$(YELLOW)Warning: apps directory not found$(NC)"
	sudo cp webapp-manager.py /opt/webapp-manager/
	sudo cp setup.py /opt/webapp-manager/ 2>/dev/null || true
	sudo cp requirements.txt /opt/webapp-manager/ 2>/dev/null || true
	@echo "$(BLUE)Creating global executable...$(NC)"
	sudo rm -f /usr/local/bin/webapp-manager
	@echo '#!/bin/bash' > /tmp/webapp-manager-wrapper
	@echo 'cd /opt/webapp-manager' >> /tmp/webapp-manager-wrapper
	@echo 'exec python3 webapp-manager.py "$$@"' >> /tmp/webapp-manager-wrapper
	sudo cp /tmp/webapp-manager-wrapper /usr/local/bin/webapp-manager
	sudo chmod +x /usr/local/bin/webapp-manager
	rm -f /tmp/webapp-manager-wrapper
	@echo "$(GREEN)webapp-manager installed globally!$(NC)"

# Remove global installation
.PHONY: uninstall-global
uninstall-global: check-root
	@echo "$(BLUE)Removing global installation...$(NC)"
	sudo rm -f /usr/local/bin/webapp-manager
	sudo rm -rf /opt/webapp-manager
	@echo "$(GREEN)Global installation removed!$(NC)"

# Debug installation
.PHONY: debug-install
debug-install:
	@echo "$(BLUE)Debugging installation...$(NC)"
	@echo "$(YELLOW)Checking if webapp-manager is installed...$(NC)"
	@if [ -f /usr/local/bin/webapp-manager ]; then \
		echo "$(GREEN)Found: /usr/local/bin/webapp-manager$(NC)"; \
		echo "$(BLUE)Content:$(NC)"; \
		cat /usr/local/bin/webapp-manager; \
		echo ""; \
		echo "$(BLUE)Permissions:$(NC)"; \
		ls -la /usr/local/bin/webapp-manager; \
	else \
		echo "$(RED)Not found: /usr/local/bin/webapp-manager$(NC)"; \
	fi
	@echo "$(YELLOW)Checking installation directory...$(NC)"
	@if [ -d /opt/webapp-manager ]; then \
		echo "$(GREEN)Found: /opt/webapp-manager$(NC)"; \
		ls -la /opt/webapp-manager/; \
		echo "$(BLUE)Python file content (first 5 lines):$(NC)"; \
		head -5 /opt/webapp-manager/webapp-manager.py 2>/dev/null || echo "$(RED)Cannot read Python file$(NC)"; \
	else \
		echo "$(RED)Not found: /opt/webapp-manager$(NC)"; \
	fi
	@echo "$(YELLOW)Testing direct Python execution...$(NC)"
	python3 webapp-manager.py --help 2>/dev/null || echo "$(RED)Direct execution failed$(NC)"
	@echo "$(YELLOW)Testing Python syntax...$(NC)"
	python3 -m py_compile webapp-manager.py 2>/dev/null && echo "$(GREEN)Python syntax OK$(NC)" || echo "$(RED)Python syntax ERROR$(NC)"
	@echo "$(YELLOW)PATH check...$(NC)"
	which webapp-manager || echo "$(RED)webapp-manager not in PATH$(NC)"
	@echo "$(YELLOW)Testing version command...$(NC)"
	webapp-manager version 2>/dev/null || echo "$(RED)Version command failed$(NC)"

# Test installation thoroughly
.PHONY: test-install
test-install:
	@echo "$(BLUE)Testing webapp-manager installation...$(NC)"
	@echo "$(YELLOW)Step 1: Check if installed...$(NC)"
	@if [ -f /usr/local/bin/webapp-manager ] && [ -d /opt/webapp-manager ]; then \
		echo "$(GREEN)✓ Installation files found$(NC)"; \
	else \
		echo "$(RED)✗ Installation files missing$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Step 2: Check executable permissions...$(NC)"
	@if [ -x /usr/local/bin/webapp-manager ]; then \
		echo "$(GREEN)✓ Executable permissions OK$(NC)"; \
	else \
		echo "$(RED)✗ Executable permissions missing$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Step 3: Check Python file syntax...$(NC)"
	@if python3 -c "import py_compile; py_compile.compile('/opt/webapp-manager/webapp-manager.py')" 2>/dev/null; then \
		echo "$(GREEN)✓ Python syntax valid$(NC)"; \
	else \
		echo "$(RED)✗ Python syntax invalid$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Step 4: Test command availability...$(NC)"
	@if command -v webapp-manager >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Command available in PATH$(NC)"; \
	else \
		echo "$(RED)✗ Command not in PATH$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Step 5: Test version command...$(NC)"
	@if timeout 10 webapp-manager version >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Version command works$(NC)"; \
	else \
		echo "$(RED)✗ Version command failed$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🎉 Installation test passed!$(NC)"

# Development workflow
.PHONY: dev
dev: format lint test
	@echo "$(GREEN)Development workflow completed!$(NC)"

# CI/CD pipeline simulation
.PHONY: ci
ci: clean install-dev lint test-coverage build
	@echo "$(GREEN)CI pipeline completed successfully!$(NC)"
