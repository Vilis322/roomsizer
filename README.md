# RoomSizer - Wallpaper Calculator

A production-ready Python CLI application for calculating the number of wallpaper rolls needed for a room, accounting for windows, doors, and pattern matching requirements.

## Features

### Core Functionality
- **Accurate Strip-Based Calculation**: Implements the correct wallpaper algorithm that accounts for:
  - Vertical strips cut from rolls based on room height
  - Pattern matching allowance (drop allowance)
  - Room perimeter-based strip counting
  - Strip savings from windows and doors
  - Configurable waste factor for reserves

- **Comprehensive Validation**: Robust input validation ensuring:
  - All dimensions are positive
  - Opening dimensions are plausible for the room
  - Total opening area is less than wall area
  - Roll length is sufficient for at least one strip

- **Flexible Waste Policies**: Strategy pattern implementation for handling:
  - Pattern matching allowance (extra length per strip)
  - Global waste factor (percentage of extra rolls)

### User Interface
- **Interactive CLI Mode**: User-friendly prompts for room dimensions, openings, and wallpaper specifications
- **Non-Interactive Mode**: Command-line arguments for automation and scripting
- **Clear Error Messages**: English-only, informative error messages with retry logic
- **Input Sanitization**: Guards against typos with sanity checks on dimensions

### Architecture & Design
- **Hexagonal Architecture**: Clean separation of domain logic and infrastructure
- **Abstract Base Classes (Ports)**: Well-defined interfaces for all domain components
- **Strategy Pattern**: Pluggable waste policy and calculator strategies
- **Immutable Value Objects**: Thread-safe, frozen dataclasses for Opening and WastePolicy
- **Type Safety**: Full type hints throughout the codebase
- **Encapsulation**: Private fields with property accessors in domain models

### Code Quality
- **Comprehensive Test Suite**: 76 tests covering:
  - Happy paths and edge cases
  - Input validation and error handling
  - Domain logic accuracy
  - CLI integration smoke tests
- **Logging**: Dual-channel logging (console INFO, file DEBUG) with configurable levels
- **Documentation**: Google-style docstrings for all public APIs
- **Performance**: Lazy logging formatting and __slots__ optimization

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd roomsizer
```

2. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies (if any):
```bash
pip install -r requirements.txt  # If you add dependencies later
```

## Usage

### Interactive Mode

Run the calculator in interactive mode for a guided experience:

```bash
python -m roomsizer.cli
```

You'll be prompted to enter:
1. Room dimensions (width, length, height in meters)
2. Number and dimensions of windows
3. Number and dimensions of doors
4. Wallpaper roll specifications (width, length in meters)
5. Optional waste allowance settings

### Non-Interactive Mode

For automation or scripting, provide all parameters via command-line arguments:

```bash
python -m roomsizer.cli \
  --width 5.0 \
  --length 4.0 \
  --height 2.7 \
  --roll-width 0.53 \
  --roll-length 10.05 \
  --windows 2 \
  --doors 1 \
  --drop-allowance 0.1 \
  --extra-factor 1.1
```

**Note**: In non-interactive mode, default dimensions are used for windows (1.2m × 1.5m) and doors (0.9m × 2.0m).

### Example Calculation

For a room 5m × 4m × 2.7m with:
- 1 window (1.2m × 1.5m)
- 1 door (0.9m × 2.0m)
- Wallpaper rolls: 0.53m wide × 10.05m long
- No waste allowance

The calculator determines:
1. Room perimeter: 18m
2. Strip height: 2.7m
3. Strips per roll: 3
4. Base strips needed: 34
5. Strips saved by openings: 3
6. **Result: 11 rolls needed**

## Architecture

### Project Structure

```
roomsizer/
├── __init__.py          # Package initialization
├── ports.py             # Abstract base classes (interfaces)
├── domain.py            # Domain models and business logic
├── cli.py               # Command-line interface
└── logging_conf.py      # Logging configuration

tests/
├── __init__.py
├── test_room.py         # Room and Opening tests
├── test_wallpaper.py    # Calculator and WastePolicy tests
└── test_cli_smoke.py    # CLI integration tests

logs/
└── app.log              # Application log file (auto-created)
```

### Domain Model

- **Opening**: Immutable value object representing windows/doors
- **Room**: Mutable entity managing dimensions and openings
- **WastePolicy**: Immutable value object defining waste/allowance strategy
- **StripBasedRollsCalculator**: Implements the correct wallpaper calculation algorithm
- **Wallpaper**: Facade providing a simple interface to the calculator

### Key Design Patterns

1. **Ports and Adapters (Hexagonal Architecture)**: Domain logic is isolated from infrastructure
2. **Strategy Pattern**: Waste policies are pluggable strategies
3. **Facade Pattern**: Wallpaper class simplifies calculator usage
4. **Value Object Pattern**: Immutable Opening and WastePolicy ensure data integrity

## Testing

Run the complete test suite:

```bash
python -m pytest tests/ -v
```

Run with coverage report:

```bash
python -m pytest tests/ --cov=roomsizer --cov-report=term-missing
```

Run specific test file:

```bash
python -m pytest tests/test_room.py -v
```

### Test Coverage

- **Domain Logic**: 100% coverage of Room, Opening, WastePolicy, and Calculator classes
- **Input Validation**: All edge cases and error conditions tested
- **CLI**: Smoke tests verify end-to-end functionality
- **Total**: 76 tests, all passing

## Algorithm Details

### Correct Strip-Based Calculation

The calculator uses the industry-standard approach:

1. **Strip Height**: `room_height + drop_allowance`
2. **Strips Per Roll**: `floor(roll_length / strip_height)`
3. **Strips Needed**: `ceil(room_perimeter / roll_width)`
4. **Strips Saved**: Sum of strips saved by each opening:
   - Horizontal span: `floor(opening_width / roll_width)`
   - Vertical span: `ceil(opening_height / strip_height)`
   - Saved: `horizontal_span × vertical_span`
5. **Net Strips**: `max(0, strips_needed - strips_saved)`
6. **Final Rolls**: `ceil((net_strips × extra_factor) / strips_per_roll)`

This approach correctly models how wallpaper is actually applied as vertical strips around the perimeter.

## Configuration

### Logging

Configure logging via environment variables:

- `LOG_LEVEL_CONSOLE`: Console log level (default: INFO)
- `LOG_LEVEL_FILE`: File log level (default: DEBUG)
- `LOG_DIR`: Log directory (default: logs)
- `LOG_FILE`: Log file name (default: app.log)

Example:

```bash
export LOG_LEVEL_CONSOLE=DEBUG
export LOG_DIR=/var/log/roomsizer
python -m roomsizer.cli
```

## Definition of Done (DoD)

This project meets the following quality criteria:

- [x] **Correct Algorithm**: Implements strip-based wallpaper calculation with pattern matching
- [x] **Type Safety**: Full type hints with Python 3.10+ syntax (`str | None`)
- [x] **Documentation**: Google-style docstrings for all public APIs
- [x] **Testing**: Comprehensive test suite with 76 tests covering all scenarios
- [x] **Validation**: Robust input validation with clear error messages
- [x] **Logging**: Dual-channel logging (console + file) with configurable levels
- [x] **English-Only**: All user-facing text and documentation in English
- [x] **OOP Design**: Proper encapsulation, inheritance, and design patterns
- [x] **No Business Logic in CLI**: Clean separation of concerns
- [x] **Multiple Interfaces**: Both interactive and non-interactive CLI modes
- [x] **Production-Ready**: Error handling, logging, validation, and testability

## Exit Codes

- `0`: Success or user cancellation
- `1`: Error during calculation or invalid input

## Acknowledgments

Built with Python 3.10+, following Domain-Driven Design and Clean Architecture principles.
