"""Command-line interface for the RoomSizer wallpaper calculator.

This module provides both interactive and non-interactive modes for calculating
wallpaper requirements. It handles user input, validates data, and displays results.

Exit Codes:
    0: Success or user cancellation
    1: Error during calculation or invalid input
"""

import argparse
import logging
import sys
from typing import Callable

from roomsizer.domain import (
    Room,
    Opening,
    OpeningKind,
    WastePolicy,
    Wallpaper,
)
from roomsizer.logging_conf import configure_logging

logger = logging.getLogger(__name__)

# Sanity limits for dimensions (to catch typos)
# Room dimensions
MIN_ROOM_WIDTH = 1.5  # meters
MAX_ROOM_WIDTH = 25.0  # meters
MIN_ROOM_LENGTH = 1.5  # meters
MAX_ROOM_LENGTH = 30.0  # meters
MIN_ROOM_HEIGHT = 2.0  # meters
MAX_ROOM_HEIGHT = 3.0  # meters

# Opening dimensions
MIN_WINDOW_WIDTH = 0.3  # meters
MAX_WINDOW_WIDTH = 5.0  # meters
MIN_WINDOW_HEIGHT = 0.3  # meters
MAX_WINDOW_HEIGHT = 3.0  # meters
MIN_DOOR_WIDTH = 0.6  # meters
MAX_DOOR_WIDTH = 3.0  # meters
MIN_DOOR_HEIGHT = 1.8  # meters
MAX_DOOR_HEIGHT = 3.0  # meters

# Wallpaper roll limits
MAX_ROLL_LENGTH = 50.0  # meters


class UserCancelled(Exception):
    """Raised when the user cancels an operation (Ctrl+C or Ctrl+D)."""
    pass


def read_positive_float(
    prompt: str,
    field_name: str = "value",
    allow_zero: bool = False,
    min_value: float | None = None,
    max_value: float | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> float:
    """Read a positive floating-point number from the user.

    Args:
        prompt: The prompt to display to the user.
        field_name: Name of the field for error messages.
        allow_zero: Whether to allow zero as a valid value.
        min_value: Minimum expected value (for sanity checking).
        max_value: Maximum expected value (for sanity checking).
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Returns:
        A positive float value from the user.

    Raises:
        UserCancelled: If the user interrupts input.
    """
    last_out_of_bounds_value: float | None = None

    while True:
        try:
            raw_input = input_func(prompt).strip()
            # Support both comma and dot as decimal separator
            normalized_input = raw_input.replace(',', '.')
            value = float(normalized_input)

            if allow_zero and value == 0:
                return value
            if value <= 0:
                output_func(
                    f"Error: {field_name} must be positive. Please try again.",
                    file=sys.stderr
                )
                continue

            # Check minimum bounds
            if min_value is not None and value < min_value:
                # If user entered the same out-of-bounds value again, accept it as confirmed
                if last_out_of_bounds_value is not None and abs(value - last_out_of_bounds_value) < 0.001:
                    return value

                last_out_of_bounds_value = value
                output_func(
                    f"Warning: {field_name} ({value:.2f}) seems unusually small. "
                    f"Minimum expected: {min_value:.2f}",
                    file=sys.stderr
                )
                output_func(
                    "Please re-enter if this was a typo, or enter the same value again to confirm.",
                    file=sys.stderr
                )
                continue

            # Check maximum bounds
            if max_value is not None and value > max_value:
                # If user entered the same out-of-bounds value again, accept it as confirmed
                if last_out_of_bounds_value is not None and abs(value - last_out_of_bounds_value) < 0.001:
                    return value

                last_out_of_bounds_value = value
                output_func(
                    f"Warning: {field_name} ({value:.2f}) seems unusually large. "
                    f"Maximum expected: {max_value:.2f}",
                    file=sys.stderr
                )
                output_func(
                    "Please re-enter if this was a typo, or enter the same value again to confirm.",
                    file=sys.stderr
                )
                continue

            # Value is within bounds, accept it
            return value
        except ValueError:
            output_func(
                f"Error: Invalid input for {field_name}. Please enter a number.",
                file=sys.stderr
            )
        except (KeyboardInterrupt, EOFError):
            raise UserCancelled()


def read_non_negative_int(
    prompt: str,
    field_name: str = "value",
    max_value: int | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> int:
    """Read a non-negative integer from the user.

    Args:
        prompt: The prompt to display to the user.
        field_name: Name of the field for error messages.
        max_value: Maximum allowed value (for sanity checking).
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Returns:
        A non-negative integer from the user.

    Raises:
        UserCancelled: If the user interrupts input.
    """
    while True:
        try:
            value = int(input_func(prompt).strip())
            if value < 0:
                output_func(
                    f"Error: {field_name} cannot be negative. Please try again.",
                    file=sys.stderr
                )
                continue
            if max_value is not None and value > max_value:
                output_func(
                    f"Warning: {field_name} ({value}) seems unusually large. "
                    f"Maximum expected: {max_value}",
                    file=sys.stderr
                )
                output_func(
                    "Please re-enter if this was a typo, or continue if correct.",
                    file=sys.stderr
                )
                continue
            return value
        except ValueError:
            output_func(
                f"Error: Invalid input for {field_name}. Please enter a whole number.",
                file=sys.stderr
            )
        except (KeyboardInterrupt, EOFError):
            raise UserCancelled()


def read_opening_dimension(
    prompt: str,
    field_name: str,
    room_limit: float,
    room_dimension_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> float:
    """Read an opening dimension with room-aware validation priority.

    Room dimension checks are performed FIRST, before min/max validation.
    This ensures that if a dimension exceeds both the room limit and min/max bounds,
    the room limit warning is shown first.

    Args:
        prompt: The prompt to display to the user.
        field_name: Name of the field for error messages (e.g., "window width").
        room_limit: Maximum allowed value based on room dimensions.
        room_dimension_name: Name of the room dimension (e.g., "room height").
        min_value: Minimum expected value (for sanity checking).
        max_value: Maximum expected value (for sanity checking).
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Returns:
        A positive float value that doesn't exceed room limits.

    Raises:
        UserCancelled: If the user interrupts input.
    """
    last_out_of_bounds_value: float | None = None

    while True:
        try:
            raw_input = input_func(prompt).strip()
            # Support both comma and dot as decimal separator
            normalized_input = raw_input.replace(',', '.')
            value = float(normalized_input)

            if value <= 0:
                output_func(
                    f"Error: {field_name} must be positive. Please try again.",
                    file=sys.stderr
                )
                continue

            # PRIORITY CHECK: Room dimension limit (checked FIRST)
            if value > room_limit:
                output_func(
                    f"  Warning: {field_name.capitalize()} ({value:.2f} m) exceeds {room_dimension_name} ({room_limit:.2f} m).",
                    file=sys.stderr
                )
                output_func("  Please try again.", file=sys.stderr)
                continue

            # Check minimum bounds
            if min_value is not None and value < min_value:
                # If user entered the same out-of-bounds value again, accept it as confirmed
                if last_out_of_bounds_value is not None and abs(value - last_out_of_bounds_value) < 0.001:
                    return value

                last_out_of_bounds_value = value
                output_func(
                    f"Warning: {field_name} ({value:.2f}) seems unusually small. "
                    f"Minimum expected: {min_value:.2f}",
                    file=sys.stderr
                )
                output_func(
                    "Please re-enter if this was a typo, or enter the same value again to confirm.",
                    file=sys.stderr
                )
                continue

            # Check maximum bounds
            if max_value is not None and value > max_value:
                # If user entered the same out-of-bounds value again, accept it as confirmed
                if last_out_of_bounds_value is not None and abs(value - last_out_of_bounds_value) < 0.001:
                    return value

                last_out_of_bounds_value = value
                output_func(
                    f"Warning: {field_name} ({value:.2f}) seems unusually large. "
                    f"Maximum expected: {max_value:.2f}",
                    file=sys.stderr
                )
                output_func(
                    "Please re-enter if this was a typo, or enter the same value again to confirm.",
                    file=sys.stderr
                )
                continue

            # Value is within all bounds, accept it
            return value
        except ValueError:
            output_func(
                f"Error: Invalid input for {field_name}. Please enter a number.",
                file=sys.stderr
            )
        except (KeyboardInterrupt, EOFError):
            raise UserCancelled()


def read_yes_no(
    prompt: str,
    default: bool = False,
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> bool:
    """Read a yes/no answer from the user.

    Args:
        prompt: The prompt to display to the user.
        default: The default value if user presses Enter.
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Returns:
        True for yes, False for no.

    Raises:
        UserCancelled: If the user interrupts input.
    """
    default_str = "Y/n" if default else "y/N"
    full_prompt = f"{prompt} [{default_str}]: "

    while True:
        try:
            answer = input_func(full_prompt).strip().lower()
            if not answer:
                return default
            if answer in ('y', 'yes'):
                return True
            if answer in ('n', 'no'):
                return False
            output_func("Error: Please answer 'y' or 'n'.", file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            raise UserCancelled()


def get_room_dimensions(
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> Room:
    """Prompt user for room dimensions and create a Room object.

    Args:
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Returns:
        A Room object with user-specified dimensions.

    Raises:
        UserCancelled: If the user interrupts input.
    """
    output_func("\n=== Room Dimensions ===")
    output_func("Please enter the dimensions of your room in meters.")

    while True:
        try:
            width = read_positive_float(
                "Room width (m): ",
                "room width",
                min_value=MIN_ROOM_WIDTH,
                max_value=MAX_ROOM_WIDTH,
                input_func=input_func,
                output_func=output_func,
            )
            length = read_positive_float(
                "Room length (m): ",
                "room length",
                min_value=MIN_ROOM_LENGTH,
                max_value=MAX_ROOM_LENGTH,
                input_func=input_func,
                output_func=output_func,
            )
            height = read_positive_float(
                "Room height (m): ",
                "room height",
                min_value=MIN_ROOM_HEIGHT,
                max_value=MAX_ROOM_HEIGHT,
                input_func=input_func,
                output_func=output_func,
            )

            room = Room(width, length, height)
            logger.info(
                "[CLI] Room created: %.2f m × %.2f m × %.2f m",
                width, length, height
            )
            return room

        except ValueError as e:
            output_func(f"Error: {e}", file=sys.stderr)
            output_func("Please re-enter the room dimensions.", file=sys.stderr)


def get_openings(
    room: Room,
    num_windows: int | None = None,
    num_doors: int | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> None:
    """Prompt user for openings (windows/doors) and add them to the room.

    Args:
        room: The room to add openings to.
        num_windows: Number of windows (if None, will prompt).
        num_doors: Number of doors (if None, will prompt).
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Raises:
        UserCancelled: If the user interrupts input.
    """
    output_func("\n=== Windows and Doors ===")
    output_func("Now let's add any windows and doors in the room.")

    # Get number of windows
    if num_windows is None:
        num_windows = read_non_negative_int(
            "Number of windows: ",
            "number of windows",
            max_value=50,
            input_func=input_func,
            output_func=output_func,
        )

    # Get window dimensions
    for i in range(num_windows):
        output_func(f"\nWindow {i + 1}:")
        while True:
            try:
                # Use room-aware dimension reading with priority checks
                max_wall_dimension = max(room.width, room.length)
                width = read_opening_dimension(
                    "  Width (m): ",
                    "window width",
                    room_limit=max_wall_dimension,
                    room_dimension_name="room width",
                    min_value=MIN_WINDOW_WIDTH,
                    max_value=MAX_WINDOW_WIDTH,
                    input_func=input_func,
                    output_func=output_func,
                )
                height = read_opening_dimension(
                    "  Height (m): ",
                    "window height",
                    room_limit=room.height,
                    room_dimension_name="room height",
                    min_value=MIN_WINDOW_HEIGHT,
                    max_value=MAX_WINDOW_HEIGHT,
                    input_func=input_func,
                    output_func=output_func,
                )

                opening = Opening(width, height, OpeningKind.WINDOW)
                room.add_opening(opening)
                logger.info("[CLI] Added window %d: %.2f m × %.2f m", i + 1, width, height)
                break
            except ValueError as e:
                output_func(f"  Error: {e}", file=sys.stderr)
                output_func("  Please re-enter the window dimensions.", file=sys.stderr)

    # Get number of doors
    if num_doors is None:
        num_doors = read_non_negative_int(
            "Number of doors: ",
            "number of doors",
            max_value=20,
            input_func=input_func,
            output_func=output_func,
        )

    # Get door dimensions
    for i in range(num_doors):
        output_func(f"\nDoor {i + 1}:")
        while True:
            try:
                # Use room-aware dimension reading with priority checks
                max_wall_dimension = max(room.width, room.length)
                width = read_opening_dimension(
                    "  Width (m): ",
                    "door width",
                    room_limit=max_wall_dimension,
                    room_dimension_name="room width",
                    min_value=MIN_DOOR_WIDTH,
                    max_value=MAX_DOOR_WIDTH,
                    input_func=input_func,
                    output_func=output_func,
                )
                height = read_opening_dimension(
                    "  Height (m): ",
                    "door height",
                    room_limit=room.height,
                    room_dimension_name="room height",
                    min_value=MIN_DOOR_HEIGHT,
                    max_value=MAX_DOOR_HEIGHT,
                    input_func=input_func,
                    output_func=output_func,
                )

                opening = Opening(width, height, OpeningKind.DOOR)
                room.add_opening(opening)
                logger.info("[CLI] Added door %d: %.2f m × %.2f m", i + 1, width, height)
                break
            except ValueError as e:
                output_func(f"  Error: {e}", file=sys.stderr)
                output_func("  Please re-enter the door dimensions.", file=sys.stderr)

    # Display summary
    wall_area = room.wall_area()
    net_area = room.net_wall_area()
    openings_area = wall_area - net_area

    output_func(f"\n--- Room Summary ---")
    output_func(f"Total wall area: {wall_area:.2f} m²")
    output_func(f"Openings area: {openings_area:.2f} m²")
    output_func(f"Net area to cover: {net_area:.2f} m²")


def get_wallpaper_specs(
    room: Room,
    roll_width: float | None = None,
    roll_length: float | None = None,
    drop_allowance: float | None = None,
    extra_factor: float | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> Wallpaper:
    """Prompt user for wallpaper specifications and create calculator.

    Args:
        room: The room to calculate wallpaper for.
        roll_width: Roll width (if None, will prompt).
        roll_length: Roll length (if None, will prompt).
        drop_allowance: Drop allowance (if None, will prompt).
        extra_factor: Extra factor (if None, will prompt).
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Returns:
        A Wallpaper calculator configured with user specifications.

    Raises:
        UserCancelled: If the user interrupts input.
    """
    output_func("\n=== Wallpaper Specifications ===")
    output_func("Please enter the specifications of the wallpaper rolls.")

    # Get roll dimensions if not provided
    if roll_width is None or roll_length is None:
        while True:
            try:
                if roll_width is None:
                    roll_width = read_positive_float(
                        "Roll width (m): ",
                        "roll width",
                        max_value=5.0,
                        input_func=input_func,
                        output_func=output_func,
                    )
                if roll_length is None:
                    roll_length = read_positive_float(
                        "Roll length (m): ",
                        "roll length",
                        max_value=MAX_ROLL_LENGTH,
                        input_func=input_func,
                        output_func=output_func,
                    )

                logger.info(
                    "[CLI] Wallpaper specs: %.2f m × %.2f m",
                    roll_width, roll_length
                )
                break
            except ValueError as e:
                output_func(f"Error: {e}", file=sys.stderr)
                output_func("Please re-enter the wallpaper specifications.", file=sys.stderr)

    # Get waste policy if not provided
    policy: WastePolicy | None = None
    if drop_allowance is not None or extra_factor is not None:
        # Non-interactive mode with partial/full policy specified
        drop_allow = drop_allowance if drop_allowance is not None else 0.0
        extra_fact = extra_factor if extra_factor is not None else 1.0
        try:
            policy = WastePolicy(drop_allow, extra_fact)
            logger.info(
                "[CLI] WastePolicy: drop_allowance=%.2f m, extra_factor=%.2f",
                drop_allow, extra_fact
            )
        except ValueError as e:
            output_func(f"Error creating waste policy: {e}", file=sys.stderr)
            output_func("Using default policy (no extra allowance).", file=sys.stderr)
            policy = None
    else:
        # Interactive mode - ask user
        output_func("\n=== Waste Allowance (Optional) ===")
        use_allowance = read_yes_no(
            "Do you want to add extra allowance for pattern matching or waste?",
            default=False,
            input_func=input_func,
            output_func=output_func,
        )

        if use_allowance:
            output_func("\nPattern matching allowance:")
            output_func("(Extra length per strip for aligning patterns)")
            drop_allow = read_positive_float(
                "Drop allowance per strip (m) [or 0 for none]: ",
                "drop allowance",
                allow_zero=True,
                max_value=2.0,
                input_func=input_func,
                output_func=output_func,
            )

            output_func("\nGeneral waste factor:")
            output_func("(Multiplier for extra rolls, e.g., 1.1 = 10% extra)")
            while True:
                extra_fact = read_positive_float(
                    "Extra factor [1.0 for no extra]: ",
                    "extra factor",
                    max_value=2.0,
                    input_func=input_func,
                    output_func=output_func,
                )
                if extra_fact >= 1.0:
                    break
                output_func("Error: Extra factor must be at least 1.0", file=sys.stderr)

            try:
                policy = WastePolicy(drop_allow, extra_fact)
                logger.info(
                    "[CLI] WastePolicy: drop_allowance=%.2f m, extra_factor=%.2f",
                    drop_allow, extra_fact
                )
            except ValueError as e:
                output_func(f"Error creating waste policy: {e}", file=sys.stderr)
                output_func("Using default policy (no extra allowance).", file=sys.stderr)
                policy = None

    try:
        wallpaper = Wallpaper(roll_width, roll_length, room, policy)
        return wallpaper
    except ValueError as e:
        output_func(f"Error creating wallpaper calculator: {e}", file=sys.stderr)
        raise


def display_results(
    wallpaper: Wallpaper,
    output_func: Callable[..., None] = print,
) -> int:
    """Calculate and display the final results.

    Args:
        wallpaper: The configured wallpaper calculator.
        output_func: Function to write output (default: print).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    output_func("\n" + "=" * 50)
    output_func("CALCULATION RESULTS")
    output_func("=" * 50)

    try:
        rolls = wallpaper.rolls_needed()
        output_func(f"\nNumber of wallpaper rolls needed: {rolls}")
        logger.info("[CLI] Final result: %d rolls needed", rolls)

        output_func("\nNote: This is a theoretical calculation. Always consult with")
        output_func("a professional and purchase a few extra rolls for safety.")
        return 0

    except ValueError as e:
        output_func(f"\nError calculating rolls: {e}", file=sys.stderr)
        logger.error("[CLI] Calculation error: %s", e)
        return 1


def run_interactive_mode(
    input_func: Callable[[str], str] = input,
    output_func: Callable[..., None] = print,
) -> int:
    """Run the interactive CLI mode.

    Args:
        input_func: Function to read input (default: input).
        output_func: Function to write output (default: print).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Display welcome message
    output_func("=" * 50)
    output_func("WALLPAPER CALCULATOR")
    output_func("=" * 50)
    output_func("\nWelcome to the Wallpaper Calculator!")
    output_func("This tool will help you determine how many wallpaper rolls")
    output_func("you need for your room.\n")

    try:
        # Step 1: Get room dimensions
        room = get_room_dimensions(input_func, output_func)

        # Step 2: Get openings (windows/doors)
        get_openings(room, input_func=input_func, output_func=output_func)

        # Step 3: Get wallpaper specifications
        wallpaper = get_wallpaper_specs(room, input_func=input_func, output_func=output_func)

        # Step 4: Display results
        exit_code = display_results(wallpaper, output_func)

        output_func("\n" + "=" * 50)
        output_func("Thank you for using the Wallpaper Calculator!")
        output_func("=" * 50)

        return exit_code

    except UserCancelled:
        output_func("\n\nOperation cancelled by user.", file=sys.stderr)
        logger.info("[CLI] User cancelled operation")
        return 0
    except Exception as e:
        output_func(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        logger.exception("[CLI] Unexpected error")
        return 1


def run_non_interactive_mode(args: argparse.Namespace) -> int:
    """Run the non-interactive CLI mode with command-line arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        # Create room
        room = Room(args.width, args.length, args.height)
        logger.info(
            "[CLI] Room created (non-interactive): %.2f m × %.2f m × %.2f m",
            args.width, args.length, args.height
        )

        # Add windows
        for i in range(args.windows):
            # In non-interactive mode, assume default window size
            # This is a limitation; ideally would need window dimensions as args
            print(
                f"Warning: Non-interactive mode uses default window size (1.2m × 1.5m)",
                file=sys.stderr
            )
            opening = Opening(1.2, 1.5, OpeningKind.WINDOW)
            room.add_opening(opening)

        # Add doors
        for i in range(args.doors):
            # In non-interactive mode, assume default door size
            print(
                f"Warning: Non-interactive mode uses default door size (0.9m × 2.0m)",
                file=sys.stderr
            )
            opening = Opening(0.9, 2.0, OpeningKind.DOOR)
            room.add_opening(opening)

        # Create waste policy if specified
        policy: WastePolicy | None = None
        if args.drop_allowance > 0 or args.extra_factor > 1.0:
            policy = WastePolicy(args.drop_allowance, args.extra_factor)
            logger.info(
                "[CLI] WastePolicy (non-interactive): drop_allowance=%.2f m, extra_factor=%.2f",
                args.drop_allowance, args.extra_factor
            )

        # Create wallpaper calculator
        wallpaper = Wallpaper(args.roll_width, args.roll_length, room, policy)

        # Calculate and display results
        rolls = wallpaper.rolls_needed()
        print(f"{rolls}")  # Simple output for scripting
        logger.info("[CLI] Final result (non-interactive): %d rolls needed", rolls)

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.error("[CLI] Error in non-interactive mode: %s", e)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        logger.exception("[CLI] Unexpected error in non-interactive mode")
        return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Calculate the number of wallpaper rolls needed for a room.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python -m roomsizer.cli

  Non-interactive mode:
    python -m roomsizer.cli --width 5 --length 4 --height 2.7 \\
                            --roll-width 0.53 --roll-length 10.05 \\
                            --windows 2 --doors 1

  With waste allowance:
    python -m roomsizer.cli --width 5 --length 4 --height 2.7 \\
                            --roll-width 0.53 --roll-length 10.05 \\
                            --drop-allowance 0.1 --extra-factor 1.1

Exit Codes:
  0: Success or user cancellation
  1: Error during calculation or invalid input
        """
    )

    parser.add_argument(
        "--width",
        type=float,
        help="Room width in meters"
    )
    parser.add_argument(
        "--length",
        type=float,
        help="Room length in meters"
    )
    parser.add_argument(
        "--height",
        type=float,
        help="Room height in meters"
    )
    parser.add_argument(
        "--roll-width",
        type=float,
        help="Wallpaper roll width in meters"
    )
    parser.add_argument(
        "--roll-length",
        type=float,
        help="Wallpaper roll length in meters"
    )
    parser.add_argument(
        "--windows",
        type=int,
        default=0,
        help="Number of windows (default: 0)"
    )
    parser.add_argument(
        "--doors",
        type=int,
        default=0,
        help="Number of doors (default: 0)"
    )
    parser.add_argument(
        "--drop-allowance",
        type=float,
        default=0.0,
        help="Drop allowance per strip in meters (default: 0.0)"
    )
    parser.add_argument(
        "--extra-factor",
        type=float,
        default=1.0,
        help="Extra waste factor multiplier (default: 1.0)"
    )

    return parser


def main() -> None:
    """Main entry point for the CLI application."""
    # Configure logging
    log_config = configure_logging()

    if log_config["reconfigured"]:
        logger.info("[CLI] Logging configured: %s", log_config)

    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Determine mode based on arguments
    required_for_non_interactive = [
        args.width, args.length, args.height,
        args.roll_width, args.roll_length
    ]

    if all(arg is not None for arg in required_for_non_interactive):
        # Non-interactive mode
        exit_code = run_non_interactive_mode(args)
    elif any(arg is not None for arg in required_for_non_interactive):
        # Partial arguments provided - error
        print(
            "Error: When using non-interactive mode, you must provide all of: "
            "--width, --length, --height, --roll-width, --roll-length",
            file=sys.stderr
        )
        sys.exit(1)
    else:
        # Interactive mode
        exit_code = run_interactive_mode()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
