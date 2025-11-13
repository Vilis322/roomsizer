.PHONY: help run test create-venv delete-venv install-requirements

# Variables
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest

# Default target
help:
	@echo "Available commands:"
	@echo "  make help                 - Show this help message"
	@echo "  make create-venv          - Create virtual environment if it doesn't exist"
	@echo "  make delete-venv          - Delete virtual environment if it exists"
	@echo "  make install-requirements - Install dependencies from requirements.txt"
	@echo "  make test                 - Run all tests with pytest"
	@echo "  make run                  - Run the wallpaper calculator application"
	@echo ""
	@echo "Quick start:"
	@echo "  make create-venv && make install-requirements && make run"

create-venv:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment already exists at $(VENV_DIR)"; \
	else \
		echo "Creating virtual environment..."; \
		python -m venv $(VENV_DIR); \
		echo "Virtual environment created successfully at $(VENV_DIR)"; \
	fi

delete-venv:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Deleting virtual environment..."; \
		rm -rf $(VENV_DIR); \
		echo "Virtual environment deleted successfully"; \
	else \
		echo "venv is not exist"; \
	fi

install-requirements:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Error: Virtual environment not found. Run 'make create-venv' first."; \
		exit 1; \
	fi
	@echo "Installing requirements..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "Requirements installed successfully"

test:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Error: Virtual environment not found. Run 'make create-venv' first."; \
		exit 1; \
	fi
	@if [ ! -f "$(PYTEST)" ]; then \
		echo "Error: pytest not found. Run 'make install-requirements' first."; \
		exit 1; \
	fi
	@echo "Running tests..."
	@$(PYTEST) tests/ -v

run:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Error: Virtual environment not found. Run 'make create-venv' first."; \
		exit 1; \
	fi
	@echo "Starting RoomSizer Wallpaper Calculator..."
	@echo "========================================"
	@$(PYTHON) -m roomsizer.cli
