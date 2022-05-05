from zilliandomizer.alarm_data import alarm_data


def test_sets() -> None:
    """
    It would be easy to accidentally put a string
    as the iterable for the set constructor,
    instead of a list of strings.

    This is to make sure that doesn't happen.
    """
    for room in alarm_data.values():
        ids = {alarm.id for alarm in room}
        for alarm in room:
            assert len(alarm.id) > 1
            for other in alarm.disables:
                assert len(other) > 1
                assert other in ids
            for other in alarm.lessens:
                assert len(other) > 1
                assert other in ids

# TODO: make sure all alarms that use the same block have each other in their `disables`
# TODO: make sure each alarm isn't disabling or lessening itself (This isn't a problem, but it indicates a mistake.)
