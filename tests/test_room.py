"""Tests for the Room class and Opening class."""

import pytest

from roomsizer.domain import Room, Opening, OpeningKind


class TestOpening:
    """Tests for the Opening class."""

    def test_opening_creation_valid(self):
        """Test creating a valid opening."""
        opening = Opening(1.2, 1.5, OpeningKind.WINDOW)
        assert opening.width == 1.2
        assert opening.height == 1.5
        assert opening.kind == OpeningKind.WINDOW

    def test_opening_area(self):
        """Test opening area calculation."""
        opening = Opening(1.2, 1.5, OpeningKind.WINDOW)
        assert opening.area() == pytest.approx(1.8, rel=1e-9)

    def test_opening_zero_width_raises(self):
        """Test that zero width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            Opening(0, 1.5, OpeningKind.WINDOW)

    def test_opening_negative_width_raises(self):
        """Test that negative width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            Opening(-1.0, 1.5, OpeningKind.WINDOW)

    def test_opening_zero_height_raises(self):
        """Test that zero height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            Opening(1.2, 0, OpeningKind.WINDOW)

    def test_opening_negative_height_raises(self):
        """Test that negative height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            Opening(1.2, -1.0, OpeningKind.WINDOW)

    def test_opening_immutability(self):
        """Test that Opening is immutable (frozen dataclass)."""
        opening = Opening(1.2, 1.5, OpeningKind.WINDOW)
        with pytest.raises(AttributeError):
            opening.width = 2.0

    def test_opening_to_dict(self):
        """Test serialization to dictionary."""
        opening = Opening(1.2, 1.5, OpeningKind.DOOR)
        data = opening.to_dict()
        assert data == {
            "width": 1.2,
            "height": 1.5,
            "kind": "door"
        }


class TestRoom:
    """Tests for the Room class."""

    def test_room_creation_valid(self):
        """Test creating a valid room."""
        room = Room(5.0, 4.0, 2.7)
        assert room.width == 5.0
        assert room.length == 4.0
        assert room.height == 2.7

    def test_room_wall_area_no_openings(self):
        """Test wall area calculation with no openings.

        Room(5, 4, 2.7) → wall_area = 2 * 2.7 * (5 + 4) = 48.6 m²
        """
        room = Room(5.0, 4.0, 2.7)
        expected_area = 2 * 2.7 * (5.0 + 4.0)
        assert room.wall_area() == pytest.approx(expected_area, rel=1e-9)
        assert room.wall_area() == pytest.approx(48.6, rel=1e-9)

    def test_room_net_area_equals_wall_when_no_openings(self):
        """Test that net area equals wall area when there are no openings."""
        room = Room(5.0, 4.0, 2.7)
        assert room.net_wall_area() == pytest.approx(room.wall_area(), rel=1e-9)

    def test_room_openings_subtract_area(self):
        """Test that openings subtract from wall area.

        Add one window (1.2 × 1.5) and one door (0.9 × 2.0).
        Net area should decrease by (1.2 * 1.5) + (0.9 * 2.0) = 1.8 + 1.8 = 3.6 m²
        """
        room = Room(5.0, 4.0, 2.7)
        wall_area = room.wall_area()

        window = Opening(1.2, 1.5, OpeningKind.WINDOW)
        door = Opening(0.9, 2.0, OpeningKind.DOOR)

        room.add_opening(window)
        room.add_opening(door)

        expected_net = wall_area - (1.2 * 1.5 + 0.9 * 2.0)
        assert room.net_wall_area() == pytest.approx(expected_net, rel=1e-9)
        assert room.net_wall_area() == pytest.approx(wall_area - 3.6, rel=1e-9)

    def test_room_perimeter(self):
        """Test room perimeter calculation."""
        room = Room(5.0, 4.0, 2.7)
        expected_perimeter = 2 * (5.0 + 4.0)
        assert room.perimeter() == pytest.approx(expected_perimeter, rel=1e-9)
        assert room.perimeter() == pytest.approx(18.0, rel=1e-9)

    def test_room_openings_property(self):
        """Test that openings property returns immutable tuple."""
        room = Room(5.0, 4.0, 2.7)
        window = Opening(1.2, 1.5, OpeningKind.WINDOW)
        room.add_opening(window)

        openings = room.openings
        assert isinstance(openings, tuple)
        assert len(openings) == 1
        assert openings[0] == window

    def test_room_zero_width_raises(self):
        """Test that zero width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            Room(0, 4.0, 2.7)

    def test_room_negative_width_raises(self):
        """Test that negative width raises ValueError."""
        with pytest.raises(ValueError, match="width must be positive"):
            Room(-1.0, 4.0, 2.7)

    def test_room_zero_length_raises(self):
        """Test that zero length raises ValueError."""
        with pytest.raises(ValueError, match="length must be positive"):
            Room(5.0, 0, 2.7)

    def test_room_negative_length_raises(self):
        """Test that negative length raises ValueError."""
        with pytest.raises(ValueError, match="length must be positive"):
            Room(5.0, -1.0, 2.7)

    def test_room_zero_height_raises(self):
        """Test that zero height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            Room(5.0, 4.0, 0)

    def test_room_negative_height_raises(self):
        """Test that negative height raises ValueError."""
        with pytest.raises(ValueError, match="height must be positive"):
            Room(5.0, 4.0, -1.0)

    def test_openings_sum_exceeds_wall_raises(self):
        """Test that total opening area >= wall area raises ValueError."""
        room = Room(2.0, 2.0, 2.0)
        # Wall area = 2 * 2 * (2 + 2) = 16 m²

        # Add multiple openings with combined area > wall area
        # 9 openings of 2m × 1m each = 18 m² > 16 m²
        for _ in range(9):
            room.add_opening(Opening(2.0, 1.0, OpeningKind.WINDOW))

        with pytest.raises(ValueError, match="must be less than wall area"):
            room.net_wall_area()

    def test_openings_sum_equals_wall_raises(self):
        """Test that total opening area == wall area raises ValueError."""
        room = Room(2.0, 2.0, 2.0)
        # Wall area = 2 * 2 * (2 + 2) = 16 m²

        # Add multiple openings with combined area == wall area
        # 8 openings of 2m × 1m each = 16 m²
        for _ in range(8):
            room.add_opening(Opening(2.0, 1.0, OpeningKind.WINDOW))

        with pytest.raises(ValueError, match="must be less than wall area"):
            room.net_wall_area()

    def test_opening_height_exceeds_room_height_raises(self):
        """Test that opening height > room height raises ValueError."""
        room = Room(5.0, 4.0, 2.7)
        tall_opening = Opening(1.0, 3.0, OpeningKind.DOOR)  # Taller than room

        with pytest.raises(ValueError, match="cannot exceed room height"):
            room.add_opening(tall_opening)

    def test_opening_width_exceeds_max_wall_raises(self):
        """Test that opening width > max wall dimension raises ValueError."""
        room = Room(5.0, 4.0, 2.7)  # Max wall dimension is 5.0
        wide_opening = Opening(6.0, 1.0, OpeningKind.WINDOW)

        with pytest.raises(ValueError, match="exceeds maximum wall dimension"):
            room.add_opening(wide_opening)

    def test_clear_openings(self):
        """Test clearing all openings from a room."""
        room = Room(5.0, 4.0, 2.7)
        room.add_opening(Opening(1.2, 1.5, OpeningKind.WINDOW))
        room.add_opening(Opening(0.9, 2.0, OpeningKind.DOOR))

        assert len(room.openings) == 2

        room.clear_openings()
        assert len(room.openings) == 0

    def test_remove_opening(self):
        """Test removing a specific opening."""
        room = Room(5.0, 4.0, 2.7)
        window = Opening(1.2, 1.5, OpeningKind.WINDOW)
        door = Opening(0.9, 2.0, OpeningKind.DOOR)

        room.add_opening(window)
        room.add_opening(door)

        assert len(room.openings) == 2

        room.remove_opening(window)
        assert len(room.openings) == 1
        assert door in room.openings
        assert window not in room.openings

    def test_remove_nonexistent_opening_raises(self):
        """Test that removing a non-existent opening raises ValueError."""
        room = Room(5.0, 4.0, 2.7)
        window = Opening(1.2, 1.5, OpeningKind.WINDOW)

        with pytest.raises(ValueError, match="not found in room"):
            room.remove_opening(window)
