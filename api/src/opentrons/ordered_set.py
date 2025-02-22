"""A set that preserves the order in which elements are added."""


from typing import Dict, Generic, Hashable, Iterable, Iterator, TypeVar, Union, overload
from typing_extensions import Literal


_SetElementT = TypeVar("_SetElementT", bound=Hashable)

_DefaultValueT = TypeVar("_DefaultValueT")


class _NOT_SPECIFIED:
    """Value not specified sentinel."""


# Implemented as a standalone class for clarity.
# If this proves insufficient, we can get many methods for free
# by subclassing collections.abc.MutableSet.
class OrderedSet(Generic[_SetElementT]):
    """A set that preserves the order in which elements are added.

    Args:
        source_iterable: An ordered iterable of initial elements.
    """

    def __init__(self, source_iterable: Iterable[_SetElementT] = tuple()) -> None:
        self._elements: Dict[_SetElementT, Literal[True]] = {}

        for element in source_iterable:
            self.add(element)

    def add(self, element: _SetElementT) -> None:
        """Add ``element`` to the set.

        If ``element`` is already in the set, it is not added again,
        and its existing position in the set is retained.
        """
        self._elements[element] = True

    def remove(self, element: _SetElementT) -> None:
        """Remove ``element`` from the set.

        Raises:
            KeyError: If ``element`` is not in the set.
        """
        del self._elements[element]

    def discard(self, element: _SetElementT) -> None:
        """Remove ``element`` from the set, if it is present."""
        try:
            self.remove(element)
        except KeyError:
            pass

    def clear(self) -> None:
        """Remove all elements from the set."""
        self._elements.clear()

    @overload
    def head(self) -> _SetElementT:
        ...

    @overload
    def head(
        self, default_value: _DefaultValueT
    ) -> Union[_SetElementT, _DefaultValueT]:
        ...

    def head(
        self, default_value: Union[_DefaultValueT, _NOT_SPECIFIED] = _NOT_SPECIFIED()
    ) -> Union[_SetElementT, _DefaultValueT]:
        """Get the head of the set.

        Args:
            default_value: A value to return if set is empty.

        Returns:
            The head of the set, or the default value, if specified.

        Raises:
            IndexError: set is empty and default was not specified.
        """
        try:
            return next(iter(self))
        except StopIteration as e:
            if isinstance(default_value, _NOT_SPECIFIED):
                raise IndexError("Set is empty") from e

        return default_value

    def __iter__(self) -> Iterator[_SetElementT]:
        """Enable iteration over all elements in the set.

        Elements are returned in the order they were added, oldest first.
        """
        return iter(self._elements)

    def __len__(self) -> int:
        """Return the number of unique elements added to the set."""
        return len(self._elements)

    def __eq__(self, other: object) -> bool:
        """Return whether this set is equal to another object.

        True if the other object is also an ordered set,
        and it contains the same elements in the same order.
        """
        if isinstance(other, OrderedSet):
            return list(self) == list(other)
        else:
            return False
