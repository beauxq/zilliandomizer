from collections import defaultdict
from typing import Dict, List
from zilliandomizer.map_gen.base_maker import Node
from zilliandomizer.map_gen.split_maker import find_cycles


def test_find_cycles() -> None:
    # an example I found during development
    """```
    -   O - O - @ - O   - - - - -
    |   |           |           |
    - - O - O - O   @ - O - O   -
    |                           |
    -   O - @ - O   O - O   O   -
    |       |           |   |   |
    - - O   O   O - O   @ - O - -
    |       |   |   |   |       |
    -   O - O - @   O   O   O - -
    |       |           |
    -   - - @   O - @ - O - O - -
    |   |                       |
    - - - - O - - - - - - - - - -
    ```"""

    possible_splits = {
        Node(y=0, x=3): Node(y=1, x=3),
        Node(y=1, x=4): Node(y=2, x=4),
        Node(y=2, x=2): Node(y=1, x=2),
        Node(y=3, x=5): Node(y=3, x=4),
        Node(y=4, x=3): Node(y=5, x=3),
        Node(y=5, x=2): Node(y=5, x=3),
        Node(y=5, x=4): Node(y=4, x=4),
    }
    dependencies: Dict[Node, List[Node]] = defaultdict(list, {
        Node(y=1, x=4): [Node(y=0, x=3), Node(y=3, x=5)],
        Node(y=2, x=2): [Node(y=5, x=2)],
        Node(y=3, x=5): [Node(y=5, x=2), Node(y=4, x=3)],
        Node(y=4, x=3): [Node(y=5, x=2), Node(y=5, x=4)],
        Node(y=5, x=2): [Node(y=5, x=4)],
        Node(y=5, x=4): [Node(y=5, x=2), Node(y=4, x=3)],
    })
    cycles = find_cycles(possible_splits, dependencies)
    assert cycles == {Node(y=4, x=3), Node(y=5, x=4), Node(y=5, x=2)}
