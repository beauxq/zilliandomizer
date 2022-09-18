import abc
from dataclasses import dataclass
from typing import List


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
    ids: List[int]


class DeathEventToGame(EventToGame):
    pass
