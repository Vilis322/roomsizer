"""Smoke tests for the CLI interface."""

import io
from typing import List

import pytest

from roomsizer.cli import (
    read_positive_float,
    read_non_negative_int,
    read_yes_no,
    get_room_dimensions,
    UserCancelled,
)
from roomsizer.domain import Room


class MockInput:
    """Mock input function for testing."""

    def __init__(self, responses: List[str]):
        """Initialize with a list of responses.

        Args:
            responses: List of strings to return on successive calls.
        """
        self.responses = responses
        self.index = 0

    def __call__(self, prompt: str) -> str:
        """Return the next response.

        Args:
            prompt: The input prompt (ignored in mock).

        Returns:
            Next response from the list.

        Raises:
            IndexError: If no more responses available.
        """
        if self.index >= len(self.responses):
            raise EOFError("No more mock responses")
        response = self.responses[self.index]
        self.index += 1
        return response


class TestReadPositiveFloat:
    """Tests for read_positive_float helper."""

    def test_read_valid_positive_float(self):
        """Test reading a valid positive float."""
        mock_input = MockInput(["5.5"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5.5

    def test_read_positive_float_rejects_negative(self):
        """Test that negative values are rejected and re-prompted."""
        mock_input = MockInput(["-5.0", "5.0"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5.0
        assert "must be positive" in output.getvalue()

    def test_read_positive_float_rejects_zero(self):
        """Test that zero is rejected when allow_zero=False."""
        mock_input = MockInput(["0", "5.0"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            allow_zero=False,
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5.0
        assert "must be positive" in output.getvalue()

    def test_read_positive_float_allows_zero_when_specified(self):
        """Test that zero is allowed when allow_zero=True."""
        mock_input = MockInput(["0"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            allow_zero=True,
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 0.0

    def test_read_positive_float_rejects_invalid_input(self):
        """Test that non-numeric input is rejected."""
        mock_input = MockInput(["abc", "5.0"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5.0
        assert "Invalid input" in output.getvalue()

    def test_read_positive_float_eof_raises_user_cancelled(self):
        """Test that EOFError raises UserCancelled."""
        mock_input = MockInput([])  # Will raise EOFError

        with pytest.raises(UserCancelled):
            read_positive_float(
                "Enter value: ",
                "test value",
                input_func=mock_input,
                output_func=print,
            )

    def test_read_positive_float_keyboard_interrupt_raises_user_cancelled(self):
        """Test that KeyboardInterrupt raises UserCancelled."""
        def raise_interrupt(prompt):
            raise KeyboardInterrupt()

        with pytest.raises(UserCancelled):
            read_positive_float(
                "Enter value: ",
                "test value",
                input_func=raise_interrupt,
                output_func=print,
            )

    def test_read_positive_float_comma_decimal_separator(self):
        """Test that comma is accepted as decimal separator (Case 4)."""
        mock_input = MockInput(["0,5"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 0.5

    def test_read_positive_float_max_value_warning(self):
        """Test that exceeding max_value shows warning."""
        mock_input = MockInput(["200", "5.0"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            max_value=100.0,
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5.0
        assert "unusually large" in output.getvalue()

    def test_read_positive_float_min_value_warning(self):
        """Test that value below min_value shows warning."""
        mock_input = MockInput(["1.0", "2.5"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            min_value=2.0,
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 2.5
        assert "unusually small" in output.getvalue()

    def test_read_positive_float_max_value_confirmation(self):
        """Test that re-entering same large value accepts it (Case 6)."""
        mock_input = MockInput(["200", "200"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            max_value=100.0,
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 200.0
        assert "unusually large" in output.getvalue()

    def test_read_positive_float_min_value_confirmation(self):
        """Test that re-entering same small value accepts it (Case 6)."""
        mock_input = MockInput(["1.0", "1.0"])
        output = io.StringIO()

        result = read_positive_float(
            "Enter value: ",
            "test value",
            min_value=2.0,
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 1.0
        assert "unusually small" in output.getvalue()


class TestReadNonNegativeInt:
    """Tests for read_non_negative_int helper."""

    def test_read_valid_non_negative_int(self):
        """Test reading a valid non-negative integer."""
        mock_input = MockInput(["5"])
        output = io.StringIO()

        result = read_non_negative_int(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5

    def test_read_non_negative_int_allows_zero(self):
        """Test that zero is allowed."""
        mock_input = MockInput(["0"])
        output = io.StringIO()

        result = read_non_negative_int(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 0

    def test_read_non_negative_int_rejects_negative(self):
        """Test that negative values are rejected."""
        mock_input = MockInput(["-5", "5"])
        output = io.StringIO()

        result = read_non_negative_int(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5
        assert "cannot be negative" in output.getvalue()

    def test_read_non_negative_int_rejects_float(self):
        """Test that float values are rejected."""
        mock_input = MockInput(["5.5", "5"])
        output = io.StringIO()

        result = read_non_negative_int(
            "Enter value: ",
            "test value",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result == 5
        assert "whole number" in output.getvalue()


class TestReadYesNo:
    """Tests for read_yes_no helper."""

    def test_read_yes(self):
        """Test reading 'yes'."""
        mock_input = MockInput(["yes"])
        result = read_yes_no(
            "Continue?",
            input_func=mock_input,
            output_func=print,
        )
        assert result is True

    def test_read_y(self):
        """Test reading 'y'."""
        mock_input = MockInput(["y"])
        result = read_yes_no(
            "Continue?",
            input_func=mock_input,
            output_func=print,
        )
        assert result is True

    def test_read_no(self):
        """Test reading 'no'."""
        mock_input = MockInput(["no"])
        result = read_yes_no(
            "Continue?",
            input_func=mock_input,
            output_func=print,
        )
        assert result is False

    def test_read_n(self):
        """Test reading 'n'."""
        mock_input = MockInput(["n"])
        result = read_yes_no(
            "Continue?",
            input_func=mock_input,
            output_func=print,
        )
        assert result is False

    def test_read_yes_no_case_insensitive(self):
        """Test that input is case-insensitive."""
        mock_input = MockInput(["YES"])
        result = read_yes_no(
            "Continue?",
            input_func=mock_input,
            output_func=print,
        )
        assert result is True

    def test_read_yes_no_default_true(self):
        """Test that empty input returns default (True)."""
        mock_input = MockInput([""])
        result = read_yes_no(
            "Continue?",
            default=True,
            input_func=mock_input,
            output_func=print,
        )
        assert result is True

    def test_read_yes_no_default_false(self):
        """Test that empty input returns default (False)."""
        mock_input = MockInput([""])
        result = read_yes_no(
            "Continue?",
            default=False,
            input_func=mock_input,
            output_func=print,
        )
        assert result is False

    def test_read_yes_no_rejects_invalid(self):
        """Test that invalid input is rejected."""
        mock_input = MockInput(["maybe", "yes"])
        output = io.StringIO()

        result = read_yes_no(
            "Continue?",
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert result is True
        assert "answer 'y' or 'n'" in output.getvalue()


class TestGetRoomDimensions:
    """Tests for get_room_dimensions function."""

    def test_get_room_dimensions_valid_input(self):
        """Test getting room dimensions with valid input."""
        mock_input = MockInput(["5.0", "4.0", "2.7"])
        output = io.StringIO()

        room = get_room_dimensions(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert isinstance(room, Room)
        assert room.width == 5.0
        assert room.length == 4.0
        assert room.height == 2.7

    def test_get_room_dimensions_retries_on_invalid(self):
        """Test that invalid dimensions trigger retry."""
        # First attempt: negative width, then valid dimensions
        mock_input = MockInput(["-5.0", "5.0", "4.0", "2.7"])
        output = io.StringIO()

        room = get_room_dimensions(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert room.width == 5.0
        assert "must be positive" in output.getvalue()

    def test_get_room_dimensions_user_cancelled(self):
        """Test that user cancellation propagates."""
        mock_input = MockInput([])  # Will raise EOFError

        with pytest.raises(UserCancelled):
            get_room_dimensions(
                input_func=mock_input,
                output_func=print,
            )


class TestCLIIntegration:
    """Integration smoke tests for the full CLI flow."""

    def test_cli_runs_with_sample_inputs(self):
        """Test that CLI runs end-to-end with sample inputs."""
        # Simulate full interactive session:
        # Room: 5m × 4m × 2.7m
        # Windows: 1 (1.2m × 1.5m)
        # Doors: 1 (0.9m × 2.0m)
        # Roll: 0.53m × 10.05m
        # No waste allowance
        responses = [
            "5.0",      # room width
            "4.0",      # room length
            "2.7",      # room height
            "1",        # number of windows
            "1.2",      # window 1 width
            "1.5",      # window 1 height
            "1",        # number of doors
            "0.9",      # door 1 width
            "2.0",      # door 1 height
            "0.53",     # roll width
            "10.05",    # roll length
            "n",        # no waste allowance
        ]

        mock_input = MockInput(responses)
        output = io.StringIO()

        from roomsizer.cli import run_interactive_mode

        exit_code = run_interactive_mode(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        output_text = output.getvalue()

        # Verify successful execution
        assert exit_code == 0

        # Verify key output elements
        assert "WALLPAPER CALCULATOR" in output_text
        assert "Room Dimensions" in output_text
        assert "Windows and Doors" in output_text
        assert "CALCULATION RESULTS" in output_text
        assert "rolls needed" in output_text.lower()

    def test_cli_handles_user_cancellation(self):
        """Test that CLI handles user cancellation gracefully."""
        # User cancels after entering room width
        responses = ["5.0"]
        mock_input = MockInput(responses)
        output = io.StringIO()

        from roomsizer.cli import run_interactive_mode

        exit_code = run_interactive_mode(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        # Should return 0 for cancellation (not an error)
        assert exit_code == 0

    def test_cli_accepts_comma_decimal_in_window(self):
        """Test Case 4: Comma decimal separator works for windows."""
        responses = [
            "5.0",      # room width
            "4.0",      # room length
            "2.7",      # room height
            "1",        # number of windows
            "0,5",      # window width with comma (Case 4)
            "1,5",      # window height with comma
            "0",        # number of doors
            "0.53",     # roll width
            "10.05",    # roll length
            "n",        # no waste allowance
        ]

        mock_input = MockInput(responses)
        output = io.StringIO()

        from roomsizer.cli import run_interactive_mode

        exit_code = run_interactive_mode(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        assert exit_code == 0

    def test_cli_warns_on_small_room_dimensions(self):
        """Test Case 2: Small room dimensions trigger warning."""
        responses = [
            "1",        # room width - too small
            "1",        # confirm same value
            "2",        # room length - too small
            "2",        # confirm same value
            "2",        # room height - valid
            "0",        # number of windows
            "0",        # number of doors
            "0.53",     # roll width
            "10.05",    # roll length
            "n",        # no waste allowance
        ]

        mock_input = MockInput(responses)
        output = io.StringIO()

        from roomsizer.cli import run_interactive_mode

        exit_code = run_interactive_mode(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        output_text = output.getvalue()
        assert exit_code == 0
        assert "unusually small" in output_text

    def test_cli_warns_on_large_room_height(self):
        """Test Case 3: Large room height (>3m) triggers warning."""
        responses = [
            "5.0",      # room width
            "4.0",      # room length
            "5.0",      # room height - too large (Case 3)
            "5.0",      # confirm same value
            "0",        # number of windows
            "0",        # number of doors
            "0.53",     # roll width
            "10.05",    # roll length
            "n",        # no waste allowance
        ]

        mock_input = MockInput(responses)
        output = io.StringIO()

        from roomsizer.cli import run_interactive_mode

        exit_code = run_interactive_mode(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        output_text = output.getvalue()
        assert exit_code == 0
        assert "unusually large" in output_text

    def test_cli_warns_on_small_door_dimensions(self):
        """Test Case 5: Small door dimensions trigger warning."""
        responses = [
            "5.0",      # room width
            "4.0",      # room length
            "2.7",      # room height
            "0",        # number of windows
            "1",        # number of doors
            "0.5",      # door width - too small (Case 5)
            "0.5",      # confirm same value
            "0.3",      # door height - too small
            "0.3",      # confirm same value
            "0.53",     # roll width
            "10.05",    # roll length
            "n",        # no waste allowance
        ]

        mock_input = MockInput(responses)
        output = io.StringIO()

        from roomsizer.cli import run_interactive_mode

        exit_code = run_interactive_mode(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        output_text = output.getvalue()
        assert exit_code == 0
        assert "unusually small" in output_text

    def test_cli_confirmation_on_repeated_value(self):
        """Test Case 6: Re-entering same out-of-bounds value accepts it."""
        responses = [
            "200",      # room width - too large
            "200",      # confirm by entering same value
            "200",      # room length - too large
            "200",      # confirm by entering same value
            "2.5",      # room height - valid
            "0",        # number of windows
            "0",        # number of doors
            "0.53",     # roll width
            "10.05",    # roll length
            "n",        # no waste allowance
        ]

        mock_input = MockInput(responses)
        output = io.StringIO()

        from roomsizer.cli import run_interactive_mode

        exit_code = run_interactive_mode(
            input_func=mock_input,
            output_func=lambda *args, **kwargs: output.write(str(args[0]) + "\n"),
        )

        output_text = output.getvalue()
        assert exit_code == 0
        # Should show warning but eventually accept
        assert "unusually large" in output_text
        assert "Room created" in output_text or "Room Dimensions" in output_text
