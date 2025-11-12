"""Domain models for the RoomSizer wallpaper calculator.

This module contains the concrete implementations of the core business logic
for calculating wallpaper needs, including room dimensions, openings
(windows/doors), and waste policies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any
import logging
import math

from roomsizer.ports import (
    AbstractOpening,
    AbstractRoom,
    AbstractWastePolicy,
    AbstractRollsCalculator,
)

logger = logging.getLogger(__name__)

__all__ = [
    "OpeningKind",
    "Opening",
    "Room",
    "WastePolicy",
    "StripBasedRollsCalculator",
    "Wallpaper",
]


class OpeningKind(Enum):
    """Type of opening in a room wall."""

    WINDOW = "window"
    DOOR = "door"


@dataclass(frozen=True)
class Opening(AbstractOpening):
    """Represents an opening (window or door) in a room wall.

    Attributes:
        width: Width of the opening in meters.
        height: Height of the opening in meters.
        kind: Type of opening (WINDOW or DOOR).
    """

    width: float
    height: float
    kind: OpeningKind

    def __post_init__(self) -> None:
        """Validate opening dimensions."""
        if self.width <= 0:
            raise ValueError(f"Opening width must be positive, got {self.width:.2f} m")
        if self.height <= 0:
            raise ValueError(
                f"Opening height must be positive, got {self.height:.2f} m"
            )

    def area(self) -> float:
        """Calculate the area of the opening.

        Returns:
            Area in square meters.
        """
        return self.width * self.height

    def to_dict(self) -> dict[str, Any]:
        """Convert opening to dictionary for serialization.

        Returns:
            Dictionary representation with width, height, and kind.
        """
        return {
            "width": self.width,
            "height": self.height,
            "kind": self.kind.value,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Opening(width={self.width:.2f}m, height={self.height:.2f}m, "
            f"kind={self.kind.value})"
        )


class Room(AbstractRoom):
    """Represents a rectangular room with walls and openings.

    The room is defined by its width, length, and height. Openings (windows
    and doors) can be added to account for areas that don't need wallpaper.
    """

    __slots__ = ("_width", "_length", "_height", "_openings")

    def __init__(self, width: float, length: float, height: float) -> None:
        """Initialize a room with given dimensions.

        Args:
            width: Width of the room in meters.
            length: Length of the room in meters.
            height: Height of the room in meters.

        Raises:
            ValueError: If any dimension is not positive.
        """
        if width <= 0:
            raise ValueError(f"Room width must be positive, got {width:.2f} m")
        if length <= 0:
            raise ValueError(f"Room length must be positive, got {length:.2f} m")
        if height <= 0:
            raise ValueError(f"Room height must be positive, got {height:.2f} m")

        self._width = width
        self._length = length
        self._height = height
        self._openings: list[AbstractOpening] = []

        logger.debug(
            "[Room] Created: width=%.2f m, length=%.2f m, height=%.2f m",
            width, length, height
        )

    @property
    def width(self) -> float:
        """Get room width in meters."""
        return self._width

    @property
    def length(self) -> float:
        """Get room length in meters."""
        return self._length

    @property
    def height(self) -> float:
        """Get room height in meters."""
        return self._height

    @property
    def openings(self) -> tuple[AbstractOpening, ...]:
        """Get read-only tuple of all openings in the room."""
        return tuple(self._openings)

    def add_opening(self, opening: AbstractOpening) -> None:
        """Add an opening (window or door) to the room.

        Args:
            opening: The opening to add.

        Raises:
            ValueError: If the opening has non-positive area or invalid dimensions.
        """
        if opening.area() <= 0:
            raise ValueError(
                f"Opening must have positive area, got {opening.area():.2f} m²"
            )

        # Validate opening dimensions are plausible for this room
        if opening.height > self._height:
            raise ValueError(
                f"Opening height ({opening.height:.2f} m) cannot exceed "
                f"room height ({self._height:.2f} m)"
            )

        max_wall_dimension = max(self._width, self._length)
        if opening.width > max_wall_dimension:
            raise ValueError(
                f"Opening width ({opening.width:.2f} m) exceeds "
                f"maximum wall dimension ({max_wall_dimension:.2f} m)"
            )

        self._openings.append(opening)
        logger.debug(
            "[Room] Added %s: %.2f m × %.2f m (area=%.2f m²)",
            opening.kind.value, opening.width, opening.height, opening.area()
        )

    def wall_area(self) -> float:
        """Calculate total wall area of the room.

        Returns:
            Total wall area in square meters (all four walls).
        """
        area = 2 * self._height * (self._width + self._length)
        logger.debug("[Room] Wall area: %.2f m²", area)
        return area

    def net_wall_area(self) -> float:
        """Calculate net wall area after subtracting openings.

        Returns:
            Net wall area in square meters.

        Raises:
            ValueError: If total opening area is >= wall area.
        """
        total_wall = self.wall_area()
        total_openings = sum(opening.area() for opening in self._openings)

        if total_openings >= total_wall:
            raise ValueError(
                f"Total opening area ({total_openings:.2f} m²) must be less than "
                f"wall area ({total_wall:.2f} m²)"
            )

        net_area = total_wall - total_openings
        logger.debug(
            "[Room] Net wall area: %.2f m² (wall=%.2f m² - openings=%.2f m²)",
            net_area, total_wall, total_openings
        )
        return net_area

    def perimeter(self) -> float:
        """Calculate the perimeter of the room.

        Returns:
            Perimeter in meters (sum of all wall lengths).
        """
        perimeter = 2 * (self._width + self._length)
        logger.debug("[Room] Perimeter: %.2f m", perimeter)
        return perimeter

    def clear_openings(self) -> None:
        """Remove all openings from the room."""
        count = len(self._openings)
        self._openings.clear()
        logger.debug("[Room] Cleared %d openings", count)

    def remove_opening(self, opening: AbstractOpening) -> None:
        """Remove a specific opening from the room.

        Args:
            opening: The opening to remove.

        Raises:
            ValueError: If the opening is not in the room.
        """
        try:
            self._openings.remove(opening)
            logger.debug("[Room] Removed %s", opening.kind.value)
        except ValueError:
            raise ValueError("Opening not found in room")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Room(width={self._width:.2f}m, length={self._length:.2f}m, "
            f"height={self._height:.2f}m, openings={len(self._openings)})"
        )


@dataclass(frozen=True)
class WastePolicy(AbstractWastePolicy):
    """Strategy for handling wallpaper waste and allowances.

    This immutable value object encapsulates the policy for extra material
    needed due to:
    - Pattern matching (drop allowance per strip)
    - General waste and reserves (extra factor)

    Attributes:
        drop_allowance: Extra meters to add per strip for pattern matching.
        extra_factor: Multiplier for total rolls (e.g., 1.1 = 10% extra).
    """

    drop_allowance: float = 0.0
    extra_factor: float = 1.0

    def __post_init__(self) -> None:
        """Validate waste policy parameters."""
        if self.drop_allowance < 0:
            raise ValueError(
                f"Drop allowance cannot be negative, got {self.drop_allowance:.2f} m"
            )
        if self.extra_factor < 1.0:
            raise ValueError(
                f"Extra factor must be >= 1.0, got {self.extra_factor:.2f}"
            )

        logger.debug(
            "[WastePolicy] Created: drop_allowance=%.2f m, extra_factor=%.2f",
            self.drop_allowance, self.extra_factor
        )

    @classmethod
    def default(cls) -> "WastePolicy":
        """Create a default waste policy with no extra allowances.

        Returns:
            WastePolicy with zero drop allowance and factor of 1.0.
        """
        return cls(0.0, 1.0)

    def to_dict(self) -> dict[str, Any]:
        """Convert waste policy to dictionary for serialization.

        Returns:
            Dictionary representation with drop_allowance and extra_factor.
        """
        return {
            "drop_allowance": self.drop_allowance,
            "extra_factor": self.extra_factor,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"WastePolicy(drop_allowance={self.drop_allowance:.2f}m, "
            f"extra_factor={self.extra_factor:.2f})"
        )


class StripBasedRollsCalculator(AbstractRollsCalculator):
    """Strip-based wallpaper roll calculator for a room.

    This calculator implements the correct strip-based algorithm that:
    1. Calculates strips needed based on room perimeter
    2. Accounts for strips saved by openings
    3. Determines how many strips per roll
    4. Calculates final roll count with waste factor

    This approach accurately models how wallpaper is applied: as vertical
    strips cut from rolls, placed around the room's perimeter.
    """

    __slots__ = ("roll_width", "roll_length", "room", "policy")

    def __init__(
        self,
        roll_width: float,
        roll_length: float,
        room: AbstractRoom,
        policy: AbstractWastePolicy | None = None,
    ) -> None:
        """Initialize strip-based rolls calculator.

        Args:
            roll_width: Width of one wallpaper roll in meters.
            roll_length: Length of one wallpaper roll in meters.
            room: The room to calculate for.
            policy: Waste policy to use (default: no waste).

        Raises:
            ValueError: If roll dimensions are not positive.
        """
        if roll_width <= 0:
            raise ValueError(f"Roll width must be positive, got {roll_width:.2f} m")
        if roll_length <= 0:
            raise ValueError(f"Roll length must be positive, got {roll_length:.2f} m")

        self.roll_width = roll_width
        self.roll_length = roll_length
        self.room = room
        self.policy = policy if policy is not None else WastePolicy.default()

        logger.debug(
            "[StripBasedRollsCalculator] Created: roll=%.2f m × %.2f m, policy=%s",
            roll_width, roll_length, self.policy
        )

    def _strip_height(self) -> float:
        """Calculate the height needed for each strip.

        Returns:
            Strip height in meters (room height + drop allowance).
        """
        height = self.room.height + self.policy.drop_allowance
        logger.debug(
            "[StripBasedRollsCalculator] Strip height: %.2f m (room=%.2f m + allowance=%.2f m)",
            height, self.room.height, self.policy.drop_allowance
        )
        return height

    def _strips_per_roll(self, strip_height: float) -> int:
        """Calculate how many strips can be cut from one roll.

        Args:
            strip_height: Height of each strip in meters.

        Returns:
            Number of strips per roll (integer).

        Raises:
            ValueError: If roll is too short for even one strip.
        """
        strips = math.floor(self.roll_length / strip_height)

        logger.debug(
            "[StripBasedRollsCalculator] Strips per roll: %d (roll_length=%.2f m / strip_height=%.2f m)",
            strips, self.roll_length, strip_height
        )

        if strips <= 0:
            raise ValueError(
                f"Roll too short for at least one strip: "
                f"roll_length={self.roll_length:.2f} m, "
                f"strip_height={strip_height:.2f} m"
            )

        return strips

    def _strips_needed_for_room(self) -> int:
        """Calculate base number of strips needed for room perimeter.

        Returns:
            Number of strips needed based on perimeter.
        """
        perimeter = self.room.perimeter()
        strips = math.ceil(perimeter / self.roll_width)

        logger.debug(
            "[StripBasedRollsCalculator] Base strips needed: %d (perimeter=%.2f m / roll_width=%.2f m)",
            strips, perimeter, self.roll_width
        )

        return strips

    def _strips_saved_by_openings(self, strip_height: float) -> int:
        """Calculate how many strips are saved by openings.

        For each opening, calculate how many full strips it spans horizontally
        and how many strip-heights it spans vertically. The product gives the
        number of strips that can be saved.

        Args:
            strip_height: Height of each strip in meters.

        Returns:
            Number of strips saved by openings.
        """
        total_saved = 0

        for opening in self.room.openings:
            # How many full strips does this opening span horizontally?
            strips_wide = math.floor(opening.width / self.roll_width)

            # How many strip-heights does it span vertically?
            strips_tall = math.ceil(opening.height / strip_height)

            # Total strips saved by this opening
            saved = strips_wide * strips_tall
            total_saved += saved

            logger.debug(
                "[StripBasedRollsCalculator] Opening %s (%.2f m × %.2f m) saves %d strips (%d wide × %d tall)",
                opening.kind.value, opening.width, opening.height, saved, strips_wide, strips_tall
            )

        logger.debug(
            "[StripBasedRollsCalculator] Total strips saved by openings: %d",
            total_saved
        )
        return total_saved

    def rolls_needed(self) -> int:
        """Calculate the number of wallpaper rolls needed.

        Algorithm:
        1. Calculate strip height (room height + drop allowance)
        2. Calculate strips per roll (floor of roll_length / strip_height)
        3. Calculate base strips needed (ceil of perimeter / roll_width)
        4. Calculate strips saved by openings
        5. Adjust strips needed (max of 0 and base - saved)
        6. Apply extra factor and calculate rolls (ceil)

        Returns:
            Number of rolls needed (integer, rounded up).

        Raises:
            ValueError: If roll is too short for even one strip.
        """
        # Step 1: Calculate strip height (cache for reuse)
        strip_height = self._strip_height()

        # Step 2: Calculate strips per roll
        strips_per_roll = self._strips_per_roll(strip_height)

        # Step 3: Calculate base strips needed for perimeter
        base_strips = self._strips_needed_for_room()

        # Step 4: Calculate strips saved by openings
        saved_strips = self._strips_saved_by_openings(strip_height)

        # Step 5: Adjust for openings (can't be negative)
        net_strips = max(0, base_strips - saved_strips)
        logger.debug(
            "[StripBasedRollsCalculator] Net strips needed: %d (base=%d - saved=%d)",
            net_strips, base_strips, saved_strips
        )

        # Step 6: Apply waste factor and calculate rolls
        strips_with_factor = net_strips * self.policy.extra_factor
        rolls = math.ceil(strips_with_factor / strips_per_roll)

        logger.debug(
            "[StripBasedRollsCalculator] Rolls needed: %d (strips=%d × factor=%.2f = %.2f, / %d strips per roll)",
            rolls, net_strips, self.policy.extra_factor, strips_with_factor, strips_per_roll
        )

        return rolls

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"StripBasedRollsCalculator(roll={self.roll_width:.2f}m × "
            f"{self.roll_length:.2f}m, policy={self.policy})"
        )


class Wallpaper:
    """Facade for wallpaper roll calculation.

    This class provides a clean interface for calculating wallpaper needs,
    delegating to a calculator strategy (strip-based by default).
    """

    def __init__(
        self,
        roll_width: float,
        roll_length: float,
        room: AbstractRoom,
        policy: AbstractWastePolicy | None = None,
        calculator: AbstractRollsCalculator | None = None,
    ) -> None:
        """Initialize wallpaper calculator.

        Args:
            roll_width: Width of one wallpaper roll in meters.
            roll_length: Length of one wallpaper roll in meters.
            room: The room to calculate for.
            policy: Waste policy to use (default: no waste).
            calculator: Custom calculator strategy (default: strip-based).
        """
        if calculator is not None:
            self._calculator = calculator
        else:
            self._calculator = StripBasedRollsCalculator(
                roll_width, roll_length, room, policy
            )

        logger.debug(
            "[Wallpaper] Created with calculator: %s",
            type(self._calculator).__name__
        )

    @property
    def calculator(self) -> AbstractRollsCalculator:
        """Get the current calculator strategy.

        Returns:
            The calculator being used.
        """
        return self._calculator

    def set_calculator(self, calculator: AbstractRollsCalculator) -> None:
        """Set a new calculator strategy.

        Args:
            calculator: The new calculator to use.
        """
        old_type = type(self._calculator).__name__
        self._calculator = calculator
        logger.debug(
            "[Wallpaper] Calculator changed: %s -> %s",
            old_type, type(calculator).__name__
        )

    def rolls_needed(self) -> int:
        """Calculate the number of wallpaper rolls needed.

        Returns:
            Number of rolls needed (integer, rounded up).

        Raises:
            ValueError: If calculation is not possible.
        """
        return self._calculator.rolls_needed()
