import pytest
from atomic_atlas_core import Atlas, Event
from atomic_atlas_core.errors import ValidationError


def test_events_are_ordered():
    atlas = Atlas("x")
    atlas.apply_event(Event(1, "declared_transition"))
    atlas.apply_event(Event(2, "declared_transition"))
    assert [e.sequence for e in atlas.events] == [1, 2]


def test_event_gap_rejected():
    atlas = Atlas("x")
    with pytest.raises(ValidationError):
        atlas.apply_event(Event(2, "declared_transition"))
