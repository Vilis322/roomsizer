# RoomSizer - Wallpaper Calculator

A Python CLI application for calculating the number of wallpaper rolls needed for a room, with support for windows, doors, and pattern matching requirements.

## Features

### Core Functionality
- **Strip-Based Calculation**: Implements wallpaper calculation using vertical strips:
  - Calculates strips needed based on room perimeter and roll width
  - Accounts for room height and roll length
  - Handles pattern matching allowance (drop allowance)
  - Deducts strips saved by windows and doors
  - Supports configurable waste factor for extra rolls

- **Input Validation**: Validates all inputs to ensure:
  - Dimensions are positive numbers
  - Opening dimensions don't exceed room dimensions
  - Wallpaper roll dimensions are valid
  - Roll length is sufficient for at least one strip

- **Waste Policies**: Configurable waste handling with:
  - Pattern matching allowance (extra length per strip for pattern alignment)
  - Global waste factor (percentage multiplier for extra rolls)

### User Interface
- **Interactive CLI Mode**: Step-by-step prompts guide users through:
  - Room dimensions (width, length, height)
  - Window specifications (count and dimensions)
  - Door specifications (count and dimensions)
  - Wallpaper roll specifications
  - Optional waste allowance settings

- **Non-Interactive Mode**: Command-line arguments for automation:
  - All parameters can be specified via flags
  - Default dimensions for windows and doors
  - Suitable for scripting and batch processing

- **Clear Error Messages**: Informative error messages in English with retry logic for invalid inputs

### Architecture & Design
- **Hexagonal Architecture**: Separation between domain logic (`domain.py`) and infrastructure (`cli.py`)
- **Abstract Base Classes**: Port interfaces defined in `ports.py` for extensibility
- **Strategy Pattern**: Pluggable `WastePolicy` implementation
- **Immutable Value Objects**: Frozen dataclasses for `Opening` and `WastePolicy`
- **Type Safety**: Type hints throughout the codebase
- **Encapsulation**: Private fields with property accessors in domain models

### Code Quality
- **Test Suite**: 91 tests covering:
  - Core calculation logic
  - Input validation and edge cases
  - Domain model behavior
  - CLI integration scenarios
- **Logging**: Dual-channel logging (console INFO, file DEBUG) with environment-based configuration
- **Documentation**: Docstrings for public APIs
- **Performance**: Optimized with `__slots__` for memory efficiency

## Installation

### Prerequisites
- Python 3.10 or higher

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd roomsizer
```

2. (Optional but recommended) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install testing dependencies (optional, only needed for running tests):
```bash
pip install -r requirements.txt
```

The application itself has no runtime dependencies beyond Python's standard library.

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

The test suite includes 91 tests covering:
- **Domain Logic**: Room, Opening, WastePolicy, and StripBasedRollsCalculator classes
- **Input Validation**: Edge cases and error conditions
- **CLI**: Smoke tests for end-to-end functionality

## Algorithm Details

### Strip-Based Calculation

The calculator implements the following logic:

1. **Strip Height**: `room_height + drop_allowance` (accounts for pattern matching)
2. **Strips Per Roll**: `floor(roll_length / strip_height)` (complete strips from each roll)
3. **Strips Needed**: `ceil(room_perimeter / roll_width)` (strips to cover room perimeter)
4. **Strips Saved**: For each opening (window/door):
   - Horizontal span: `floor(opening_width / roll_width)` (strips wide)
   - Vertical span: `ceil(opening_height / strip_height)` (strips tall)
   - Saved strips: `horizontal_span × vertical_span`
5. **Net Strips**: `max(0, strips_needed - total_strips_saved)`
6. **Final Rolls**: `ceil((net_strips × extra_factor) / strips_per_roll)`

The `extra_factor` allows adding a percentage of extra rolls (e.g., 1.1 for 10% extra) for waste and reserves.

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

## Exit Codes

- `0`: Success or user cancellation
- `1`: Error during calculation or invalid input

## Technical Details

- **Language**: Python 3.10+
- **Architecture**: Hexagonal Architecture (Ports and Adapters)
- **Design Patterns**: Strategy Pattern, Facade Pattern, Value Objects
- **Testing**: pytest
- **Dependencies**: Standard library only (no external runtime dependencies)
