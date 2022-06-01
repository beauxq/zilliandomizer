current_scene_c11f = 0xc11f
"""
main game scene selector

0 MSB triggers loading it

1 MSB for done with loading this

---
- 00 reset
- 01 title screen
- 02 demo playing (load next char on trigger)
- 03 continue or retry?
- 04 base explosion timer ends
- 05 intro text
- 06 cutscene determined by _C183_
- 07 to inside ship (remembers location before trigger)
- 08 computer
- 09 pause screen
- 0a reset
- 0b gameplay (can move/jump/shoot)
- 0c main computer room
- 0d end credits (without loading vram)
- 0e curtain call
"""

current_char_c127 = 0xc127
current_hp_c143 = 0xc143
level_c145 = 0xc145
curr_scope_c149 = 0xc149

jj_status_c150 = 0xc150
jj_hp_c153 = 0xc153
jj_scope_c159 = 0xc159
champ_status_c160 = 0xc160
champ_hp_c163 = 0xc163
champ_scope_c169 = 0xc169
apple_status_c170 = 0xc170
apple_hp_c173 = 0xc173
apple_scope_c179 = 0xc179

cutscene_selector_c183 = 0xc183

game_started_flag_c300 = 0xc300
""" 129 after game started """

door_state_d600 = 0xd600
canister_state_d700 = 0xd700
""" 2 bytes per room, opened, acquired """

# moveable (TODO: make sure covered all references for moveable)
external_item_trigger_c2ea = 0xc2ea
""" 3 rescue_0, 4 rescue_1 """
guns_c2ec = 0xc2ec
opas_c2ee = 0xc2ee
max_level = 0xc2ed
