import abc
from dataclasses import dataclass


class EventFromGame(abc.ABC):
    ...


class DeathEventFromGame(EventFromGame):
    pass


@dataclass
class AcquireLocationEventFromGame(EventFromGame):
    """ 0 for game win """
    id: int


class EventToGame(abc.ABC):
    ...


@dataclass
class ItemEventToGame(EventToGame):
    id: int


class DeathEventToGame(EventToGame):
    pass
