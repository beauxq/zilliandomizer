from typing import Tuple

from zilliandomizer.items import RESCUE

"""
some rom data documentation:


codes for type of data in item data (index 0):
0A keyword
26 normal item
2A rescue (Apple/Champ)
0D door to main computer
2B hallway to shoot open
2E unknown in final boss room  $2E $78 $90    $00 $00 $00 $00 $1B
3D unknown in final boss room  $3D $08 $F8/08 $00 $00 $00 $00 $00


item ids:
00-03 keywords
04 empty
05 card
06 red card
07 floppy
08 bread
09 opo
0A gun
0B scope
0C something glitched (do I need any custom items? ;)

00 Apple
01 Champ
 (this item ID with the 2A code (1st byte of data structure) determines which char is rescued)
 (sprite doesn't matter, Y coord can be the extra 8 pixels up or not)

00 main computer and stuff in final boss room


The byte after item id is the sprite of the location (canister or rescue)
02 blue area gun1 canister
04 blue area gun2 canister
06 blue area gun3 canister
08 red gun1 canister
0A red gun2 canister
0C red gun3 canister
0E paperclip gun1
10 paperclip gun2
12 paperclip gun3
14 Apple
16 Champ
LSB is set to display it already opened (only display, canister is still closed - opening it increments the image)


room item data structure:
    first byte is number of items (canisters and rescues) in the room
    then that many copies of this data structure:
        C Y X R M I S G
        C - code for type of data (see list above)
        Y - Y coordinate of canister in room (normal canister levels are 18, 38, 58, 78, 98)
            Apple is at 10, Champ is at 50 (because sprite is 8 pixels taller?)
        X - X coordinate of canister in room
            (10 - E0 normally - don't know if any are not multiples of x10 - main computer door is 18)
        R - room code? different even number for each room that has canisters - 94 is hallways that can be shot open
        M - mask for this item (keep track of open/got - ascending in this array (rescues use one also))
        I - item code (see list above)
        S - Sprite (see list above)
        G - gun required to open (Apple 01, Champ 00 - guessing it doesn't matter, but...)
    then after the list of items is complete, 2 more bytes, unknown purpose
"""

ItemData = Tuple[int, int, int, int, int, int, int, int]
""" C Y X R M I S G (see above) """


def make_loc_name(room_no: int, item: ItemData) -> str:
    row = room_no // 8
    room_location = f"r{row if row > 9 else ('0' + str(row))}c{room_no % 8}"
    # adjust height of rescues so they match with other items
    y = item[1] + 8 if item[0] == RESCUE else item[1]
    name = f"{room_location}y{hex(y)[-2:]}x{hex(item[2])[-2:]}"
    return name
