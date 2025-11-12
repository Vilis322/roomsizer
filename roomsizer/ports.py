"""Abstract base classes (ports) for the RoomSizer domain.

This module defines the interfaces (ports) that domain implementations must
conform to, following hexagonal architecture principles. These ABCs allow for
multiple implementations and improved testability.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from roomsizer.domain import OpeningKind

__all__ = [
    "AbstractOpening",
    "AbstractRoom",
    "AbstractWastePolicy",
    "AbstractRollsCalculator",
]


class AbstractOpening(ABC):
    """Interface for an opening (window or door) in a room wall.

    An opening represents a window or door that reduces the wall area
    requiring wallpaper coverage.

    Implementations must provide:
        width (float): Width of the opening in meters.
        height (float): Height of the opening in meters.
        kind (OpeningKind): Type of opening (WINDOW or DOOR).
    """

    @abstractmethod
    def area(self) -> float:
        """Calculate the area of the opening.

        Returns:
            Area in square meters.
        """
        pass


class AbstractRoom(ABC):
    """Interface for a room with walls and openings.

    A room is defined by its dimensions and can contain openings (windows/doors)
    that reduce the area requiring wallpaper. All measurements are in meters.

    Implementations must provide:
        width (float): Width of the room in meters.
        length (float): Length of the room in meters.
        height (float): Height of the room in meters.
    """

    @property
    @abstractmethod
    def openings(self) -> tuple[AbstractOpening, ...]:
        """Read-only tuple of all openings in the room.

        Returns:
            Immutable tuple of openings.
        """
        pass

    @abstractmethod
    def add_opening(self, opening: AbstractOpening) -> None:
        """Add an opening (window or door) to the room.

        Args:
            opening: The opening to add.

        Raises:
            ValueError: If the opening is invalid.
        """
        pass

    @abstractmethod
    def wall_area(self) -> float:
        """Calculate total wall area of the room.

        Returns:
            Total wall area in square meters (all four walls).
        """
        pass

    @abstractmethod
    def net_wall_area(self) -> float:
        """Calculate net wall area after subtracting openings.

        Returns:
            Net wall area in square meters.

        Raises:
            ValueError: If total opening area is >= wall area.
        """
        pass

    @abstractmethod
    def perimeter(self) -> float:
        """Calculate the perimeter of the room.

        Returns:
            Perimeter in meters (sum of all wall lengths).
        """
        pass


class AbstractWastePolicy(ABC):
    """Interface for wallpaper waste and allowance strategy.

    A waste policy defines how much extra material is needed for:
    - Pattern matching (drop allowance per strip)
    - General reserves and waste (extra factor multiplier)

    Implementations must provide:
        drop_allowance (float): Extra meters to add per strip for pattern matching.
        extra_factor (float): Multiplier for total rolls (e.g., 1.1 = 10% extra).
    """
    pass


class AbstractRollsCalculator(ABC):
    """Interface for calculating the number of wallpaper rolls needed.

    Different calculation strategies can implement this interface to provide
    alternative algorithms for roll calculation.
    """

    @abstractmethod
    def rolls_needed(self) -> int:
        """Calculate the number of wallpaper rolls needed.

        Returns:
            Number of rolls needed (integer, rounded up).

        Raises:
            ValueError: If calculation is not possible (e.g., roll too short).
        """
        pass
