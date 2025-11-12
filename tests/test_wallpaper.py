"""Tests for the Wallpaper calculator classes."""

import pytest
import math

from roomsizer.domain import (
    Room,
    Opening,
    OpeningKind,
    WastePolicy,
    StripBasedRollsCalculator,
    Wallpaper,
)


class TestWastePolicy:
    """Tests for the WastePolicy class."""

    def test_waste_policy_default(self):
        """Test default waste policy creation."""
        policy = WastePolicy.default()
        assert policy.drop_allowance == 0.0
        assert policy.extra_factor == 1.0

    def test_waste_policy_custom(self):
        """Test custom waste policy creation."""
        policy = WastePolicy(0.1, 1.1)
        assert policy.drop_allowance == 0.1
        assert policy.extra_factor == 1.1

    def test_waste_policy_negative_drop_allowance_raises(self):
        """Test that negative drop allowance raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            WastePolicy(-0.1, 1.0)

    def test_waste_policy_extra_factor_less_than_one_raises(self):
        """Test that extra factor < 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="must be >= 1.0"):
            WastePolicy(0.0, 0.9)

    def test_waste_policy_immutability(self):
        """Test that WastePolicy is immutable (frozen dataclass)."""
        policy = WastePolicy(0.1, 1.1)
        with pytest.raises(AttributeError):
            policy.drop_allowance = 0.2

    def test_waste_policy_to_dict(self):
        """Test serialization to dictionary."""
        policy = WastePolicy(0.1, 1.1)
        data = policy.to_dict()
        assert data == {
            "drop_allowance": 0.1,
            "extra_factor": 1.1
        }


class TestStripBasedRollsCalculator:
    """Tests for the StripBasedRollsCalculator class."""

    def test_rolls_needed_basic_no_waste(self):
        """Test basic rolls calculation with no waste policy.

        Room: 5m × 4m × 2.7m
        Perimeter: 18m
        Roll: 0.53m wide × 10.05m long
        Strip height: 2.7m
        Strips per roll: floor(10.05 / 2.7) = 3
        Strips needed: ceil(18 / 0.53) = 34
        Rolls: ceil(34 / 3) = 12
        """
        room = Room(5.0, 4.0, 2.7)
        policy = WastePolicy.default()
        calc = StripBasedRollsCalculator(0.53, 10.05, room, policy)

        rolls = calc.rolls_needed()
        assert rolls == 12

    def test_rolls_needed_with_openings(self):
        """Test rolls calculation with openings that save strips.

        Room: 5m × 4m × 2.7m
        Window: 1.2m × 1.5m
        Door: 0.9m × 2.0m
        Roll: 0.53m wide × 10.05m long
        Strip height: 2.7m

        Strips per roll: floor(10.05 / 2.7) = 3
        Base strips: ceil(18 / 0.53) = 34

        Window saves: floor(1.2 / 0.53) × ceil(1.5 / 2.7) = 2 × 1 = 2 strips
        Door saves: floor(0.9 / 0.53) × ceil(2.0 / 2.7) = 1 × 1 = 1 strip
        Total saved: 3 strips

        Net strips: 34 - 3 = 31
        Rolls: ceil(31 / 3) = 11
        """
        room = Room(5.0, 4.0, 2.7)
        room.add_opening(Opening(1.2, 1.5, OpeningKind.WINDOW))
        room.add_opening(Opening(0.9, 2.0, OpeningKind.DOOR))

        policy = WastePolicy.default()
        calc = StripBasedRollsCalculator(0.53, 10.05, room, policy)

        rolls = calc.rolls_needed()
        assert rolls == 11

    def test_rolls_needed_with_drop_allowance(self):
        """Test that drop allowance increases strip height and rolls needed.

        Room: 5m × 4m × 2.7m
        Roll: 0.53m wide × 10.05m long
        Drop allowance: 0.1m
        Strip height: 2.7 + 0.1 = 2.8m

        Strips per roll: floor(10.05 / 2.8) = 3
        Strips needed: ceil(18 / 0.53) = 34
        Rolls: ceil(34 / 3) = 12

        (Same result in this case, but strip height is different)
        """
        room = Room(5.0, 4.0, 2.7)
        policy = WastePolicy(0.1, 1.0)
        calc = StripBasedRollsCalculator(0.53, 10.05, room, policy)

        # Verify strip height calculation
        strip_height = calc._strip_height()
        assert strip_height == pytest.approx(2.8, rel=1e-9)

        rolls = calc.rolls_needed()
        # With higher strip height, might get fewer strips per roll
        assert rolls >= 12

    def test_rolls_needed_with_extra_factor(self):
        """Test that extra factor increases rolls needed.

        Room: 5m × 4m × 2.7m
        Roll: 0.53m wide × 10.05m long
        Extra factor: 1.1 (10% extra)

        Base calculation: 12 rolls (from test_rolls_needed_basic_no_waste)
        With 10% extra: strips needed × 1.1, then divide by strips_per_roll
        34 strips × 1.1 = 37.4 strips
        Rolls: ceil(37.4 / 3) = 13
        """
        room = Room(5.0, 4.0, 2.7)
        policy = WastePolicy(0.0, 1.1)
        calc = StripBasedRollsCalculator(0.53, 10.05, room, policy)

        rolls = calc.rolls_needed()
        assert rolls == 13

    def test_rolls_needed_with_both_waste_factors(self):
        """Test rolls calculation with both drop allowance and extra factor.

        Room: 5m × 4m × 2.7m
        Roll: 0.53m wide × 10.05m long
        Drop allowance: 0.15m
        Extra factor: 1.15

        Strip height: 2.7 + 0.15 = 2.85m
        Strips per roll: floor(10.05 / 2.85) = 3
        Strips needed: ceil(18 / 0.53) = 34
        With extra factor: ceil((34 × 1.15) / 3) = ceil(39.1 / 3) = ceil(13.03) = 14
        """
        room = Room(5.0, 4.0, 2.7)
        policy = WastePolicy(0.15, 1.15)
        calc = StripBasedRollsCalculator(0.53, 10.05, room, policy)

        rolls = calc.rolls_needed()
        assert rolls == 14

    def test_roll_too_short_raises(self):
        """Test that roll length < strip height raises ValueError.

        Room height: 2.7m
        Roll length: 2.0m (too short)
        Strip height: 2.7m
        Strips per roll: floor(2.0 / 2.7) = 0 → should raise
        """
        room = Room(5.0, 4.0, 2.7)
        policy = WastePolicy.default()
        calc = StripBasedRollsCalculator(0.53, 2.0, room, policy)

        with pytest.raises(ValueError, match="Roll too short"):
            calc.rolls_needed()

    def test_roll_too_short_with_allowance_raises(self):
        """Test that roll too short even with allowance raises ValueError.

        Room height: 2.7m
        Drop allowance: 0.5m
        Roll length: 3.0m
        Strip height: 2.7 + 0.5 = 3.2m
        Strips per roll: floor(3.0 / 3.2) = 0 → should raise
        """
        room = Room(5.0, 4.0, 2.7)
        policy = WastePolicy(0.5, 1.0)
        calc = StripBasedRollsCalculator(0.53, 3.0, room, policy)

        with pytest.raises(ValueError, match="Roll too short"):
            calc.rolls_needed()

    def test_negative_roll_width_raises(self):
        """Test that negative roll width raises ValueError."""
        room = Room(5.0, 4.0, 2.7)
        with pytest.raises(ValueError, match="Roll width must be positive"):
            StripBasedRollsCalculator(-0.53, 10.05, room)

    def test_zero_roll_width_raises(self):
        """Test that zero roll width raises ValueError."""
        room = Room(5.0, 4.0, 2.7)
        with pytest.raises(ValueError, match="Roll width must be positive"):
            StripBasedRollsCalculator(0, 10.05, room)

    def test_negative_roll_length_raises(self):
        """Test that negative roll length raises ValueError."""
        room = Room(5.0, 4.0, 2.7)
        with pytest.raises(ValueError, match="Roll length must be positive"):
            StripBasedRollsCalculator(0.53, -10.05, room)

    def test_zero_roll_length_raises(self):
        """Test that zero roll length raises ValueError."""
        room = Room(5.0, 4.0, 2.7)
        with pytest.raises(ValueError, match="Roll length must be positive"):
            StripBasedRollsCalculator(0.53, 0, room)

    def test_strips_saved_calculation(self):
        """Test internal strips saved calculation.

        Room: 5m × 4m × 2.7m
        Window: 2.0m wide × 1.5m high
        Roll width: 0.5m
        Strip height: 2.7m

        Window saves: floor(2.0 / 0.5) × ceil(1.5 / 2.7) = 4 × 1 = 4 strips
        """
        room = Room(5.0, 4.0, 2.7)
        room.add_opening(Opening(2.0, 1.5, OpeningKind.WINDOW))

        calc = StripBasedRollsCalculator(0.5, 10.0, room)
        strip_height = calc._strip_height()
        saved = calc._strips_saved_by_openings(strip_height)

        assert saved == 4

    def test_minimal_room(self):
        """Test calculation for a very small room.

        Room: 2m × 2m × 2.5m
        Perimeter: 8m
        Roll: 0.5m wide × 10m long
        Strip height: 2.5m
        Strips per roll: floor(10 / 2.5) = 4
        Strips needed: ceil(8 / 0.5) = 16
        Rolls: ceil(16 / 4) = 4
        """
        room = Room(2.0, 2.0, 2.5)
        calc = StripBasedRollsCalculator(0.5, 10.0, room)

        rolls = calc.rolls_needed()
        assert rolls == 4

    def test_large_room(self):
        """Test calculation for a large room.

        Room: 10m × 8m × 3m
        Perimeter: 36m
        Roll: 0.53m wide × 10.05m long
        Strip height: 3m
        Strips per roll: floor(10.05 / 3) = 3
        Strips needed: ceil(36 / 0.53) = 68
        Rolls: ceil(68 / 3) = 23
        """
        room = Room(10.0, 8.0, 3.0)
        calc = StripBasedRollsCalculator(0.53, 10.05, room)

        rolls = calc.rolls_needed()
        assert rolls == 23


class TestWallpaper:
    """Tests for the Wallpaper facade class."""

    def test_wallpaper_uses_strip_calculator_by_default(self):
        """Test that Wallpaper uses StripBasedRollsCalculator by default."""
        room = Room(5.0, 4.0, 2.7)
        wallpaper = Wallpaper(0.53, 10.05, room)

        assert isinstance(wallpaper.calculator, StripBasedRollsCalculator)

    def test_wallpaper_rolls_needed(self):
        """Test that Wallpaper.rolls_needed() delegates to calculator."""
        room = Room(5.0, 4.0, 2.7)
        wallpaper = Wallpaper(0.53, 10.05, room)

        rolls = wallpaper.rolls_needed()
        assert rolls == 12  # Same as strip calculator

    def test_wallpaper_with_custom_calculator(self):
        """Test Wallpaper with a custom calculator strategy."""
        from roomsizer.ports import AbstractRollsCalculator

        class MockCalculator(AbstractRollsCalculator):
            def rolls_needed(self) -> int:
                return 42

        room = Room(5.0, 4.0, 2.7)
        mock_calc = MockCalculator()
        wallpaper = Wallpaper(0.53, 10.05, room, calculator=mock_calc)

        assert wallpaper.rolls_needed() == 42

    def test_wallpaper_set_calculator(self):
        """Test changing calculator strategy at runtime."""
        from roomsizer.ports import AbstractRollsCalculator

        class MockCalculator(AbstractRollsCalculator):
            def rolls_needed(self) -> int:
                return 99

        room = Room(5.0, 4.0, 2.7)
        wallpaper = Wallpaper(0.53, 10.05, room)

        # Initial result
        assert wallpaper.rolls_needed() == 12

        # Change calculator
        mock_calc = MockCalculator()
        wallpaper.set_calculator(mock_calc)

        # New result
        assert wallpaper.rolls_needed() == 99

    def test_wallpaper_with_policy(self):
        """Test Wallpaper with waste policy."""
        room = Room(5.0, 4.0, 2.7)
        policy = WastePolicy(0.0, 1.1)
        wallpaper = Wallpaper(0.53, 10.05, room, policy)

        rolls = wallpaper.rolls_needed()
        assert rolls == 13  # With 10% extra
