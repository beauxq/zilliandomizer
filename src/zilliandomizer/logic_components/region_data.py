from typing import Dict
from zilliandomizer.logic_components.regions import Region
from zilliandomizer.logic_components.locations import Location, Req


def make_regions(locations: Dict[str, Location]) -> Region:
    """ return `start` region """
    Region.all.clear()

    start = Region("start")
    # TODO: after implement layout changes for jump, set jump requirements for these locations
    r02c7 = Region("r02c7", 23)
    r02c7.locations.append(locations["r02c7y18x30"])
    r02c7.locations.append(locations["r02c7y58x10"])
    r02c7.locations.append(locations["r02c7y58x20"])
    r02c7.locations.append(locations["r02c7y18xd0"])
    r02c7.locations.append(locations["r02c7y58xe0"])
    r02c7.locations.append(locations["r02c7y98xe0"])

    left_of_start = Region("left_of_start")
    r01c2 = Region("r01c2", 10)
    r01c2.locations.append(locations["r01c2y58x60"])
    r01c2.locations.append(locations["r01c2y58x20"])
    r01c2.locations.append(locations["r01c2y58x10"])
    r01c2.locations.append(locations["r01c2y18x60"])
    r01c2.locations.append(locations["r01c2y98xe0"])

    r02c0 = Region("r02c0")
    r02c0.locations.append(locations["r02c0y98x50"])
    r02c0.locations.append(locations["r02c0y58xd0"])
    r02c0.locations.append(locations["r02c0y58x10"])
    r02c0.locations.append(locations["r02c0y18xa0"])
    r02c0.locations.append(locations["r02c0y18x90"])

    r01c3 = Region("r01c3")
    r01c3.locations.append(locations["r01c3y98x10"])
    r01c3.locations.append(locations["r01c3y58x80"])
    r01c3.locations.append(locations["r01c3y78xb0"])
    r01c3.locations.append(locations["r01c3y38x40"])

    r01c5 = Region("r01c5")
    r01c5.locations.append(locations["r01c5y58x30"])
    r01c5.locations.append(locations["r01c5y58xe0"])
    r01c5.locations.append(locations["r01c5y18xb0"])
    r01c5.locations.append(locations["r01c5y58x20"])
    r01c5.locations.append(locations["r01c5y98xe0"])
    r01c5.locations.append(locations["r01c5y38x10"])

    r01c7 = Region("r01c7")
    r01c7.locations.append(locations["r01c7y98x70"])
    r01c7.locations.append(locations["r01c7y98x80"])
    r01c7.locations.append(locations["r01c7y98xd0"])

    r03c2 = Region("r03c2", 26)
    r03c2.locations.append(locations["r03c2y58xe0"])
    r03c2.locations.append(locations["r03c2y78xa0"])
    r03c2.locations.append(locations["r03c2y18xe0"])
    r03c2.locations.append(locations["r03c2y18x10"])
    r03c2.locations.append(locations["r03c2y18x40"])

    r03c3 = Region("r03c3", 27)
    r03c3.locations.append(locations["r03c3y18xd0"])
    r03c3.locations.append(locations["r03c3y38x10"])
    r03c3.locations.append(locations["r03c3y58x40"])
    r03c3.locations.append(locations["r03c3y18xb0"])
    r03c3.locations.append(locations["r03c3y18xa0"])

    r03c4 = Region("r03c4", 28)
    r03c4.locations.append(locations["r03c4y98x30"])
    r03c4.locations.append(locations["r03c4y58x10"])
    r03c4.locations.append(locations["r03c4y38x40"])
    r03c4.locations.append(locations["r03c4y98xc0"])
    r03c4.locations.append(locations["r03c4y38xb0"])

    r03c5 = Region("r03c5", 29)
    r03c5.locations.append(locations["r03c5y58x10"])
    r03c5.locations.append(locations["r03c5y98x60"])
    r03c5.locations.append(locations["r03c5y18xa0"])
    r03c5.locations.append(locations["r03c5y18xc0"])
    r03c5.locations.append(locations["r03c5y58xd0"])
    r03c5.locations.append(locations["r03c5y58xc0"])

    r04c1 = Region("r04c1", 33)
    r04c1.locations.append(locations["r04c1y80x20"])
    r04c1.locations.append(locations["r04c1y58xe0"])
    r04c1.locations.append(locations["r04c1y78x80"])
    r04c1.locations.append(locations["r04c1y78x70"])
    r04c1.locations.append(locations["r04c1y38x20"])
    r04c1.locations.append(locations["r04c1y18x58"])

    r04c2 = Region("r04c2", 34)
    r04c2.locations.append(locations["r04c2y18xc0"])
    r04c2.locations.append(locations["r04c2y98xe0"])
    r04c2.locations.append(locations["r04c2y18x10"])
    r04c2.locations.append(locations["r04c2y18xb0"])
    r04c2.locations.append(locations["r04c2y18xd0"])

    r04c4 = Region("r04c4", 36)
    r04c4.locations.append(locations["r04c4y58xe0"])
    r04c4.locations.append(locations["r04c4y98xe0"])
    r04c4.locations.append(locations["r04c4y18x20"])
    r04c4.locations.append(locations["r04c4y58x70"])
    r04c4.locations.append(locations["r04c4y18x10"])
    r04c4.locations.append(locations["r04c4y18x70"])

    r04c5 = Region("r04c5", 37)
    r04c5.locations.append(locations["r04c5y58x70"])
    r04c5.locations.append(locations["r04c5y18xe0"])
    r04c5.locations.append(locations["r04c5y18x70"])
    r04c5.locations.append(locations["r04c5y18xb0"])
    r04c5.locations.append(locations["r04c5y58x10"])
    r04c5.locations.append(locations["r04c5y98x10"])

    r05c1 = Region("r05c1", 41)
    r05c1.locations.append(locations["r05c1y58x10"])
    r05c1.locations.append(locations["r05c1y58xc0"])
    r05c1.locations.append(locations["r05c1y58x80"])
    r05c1.locations.append(locations["r05c1y98x70"])
    r05c1.locations.append(locations["r05c1y98x50"])

    r05c3 = Region("r05c3", 43)
    r05c3.locations.append(locations["r05c3y58xe0"])
    r05c3.locations.append(locations["r05c3y98x10"])
    r05c3.locations.append(locations["r05c3y18x10"])
    r05c3.locations.append(locations["r05c3y58x70"])
    r05c3.locations.append(locations["r05c3y58x10"])

    r05c4sw = Region("r05c4sw", 44)
    r05c4sw.locations.append(locations["r05c4y18xb0"])
    r05c4sw.locations.append(locations["r05c4y58x50"])
    r05c4sw.locations.append(locations["r05c4y18xa0"])
    r05c4sw.locations.append(locations["r05c4y58x30"])
    r05c4sw.locations.append(locations["r05c4y98x80"])

    r05c4ne = Region("r05c4ne")
    r05c4ne.locations.append(locations["r05c4y18xe0"])

    r05c5 = Region("r05c5")
    r05c5.locations.append(locations["r05c5y98x10"])
    r05c5.locations.append(locations["r05c5y58x10"])
    r05c5.locations.append(locations["r05c5y98xa0"])
    r05c5.locations.append(locations["r05c5y98x90"])
    r05c5.locations.append(locations["r05c5y98x80"])

    r05c7 = Region("r05c7", 47)
    r05c7.locations.append(locations["r05c7y18xd0"])
    r05c7.locations.append(locations["r05c7y18xc0"])
    r05c7.locations.append(locations["r05c7y18x10"])
    r05c7.locations.append(locations["r05c7y98xc0"])
    r05c7.locations.append(locations["r05c7y18x20"])
    r05c7.locations.append(locations["r05c7y18x30"])

    r06c1 = Region("r06c1", 49)
    r06c1.locations.append(locations["r06c1y98xa0"])
    r06c1.locations.append(locations["r06c1y18x10"])
    r06c1.locations.append(locations["r06c1y98x50"])
    r06c1.locations.append(locations["r06c1y98x80"])
    r06c1.locations.append(locations["r06c1y98x30"])

    r06c3 = Region("r06c3", 51)
    r06c3.locations.append(locations["r06c3y58x40"])
    r06c3.locations.append(locations["r06c3y58x20"])
    r06c3.locations.append(locations["r06c3y58x70"])
    r06c3.locations.append(locations["r06c3y18xb0"])
    r06c3.locations.append(locations["r06c3y18xa0"])

    r06c4 = Region("r06c4", 52)
    r06c4.locations.append(locations["r06c4y58xe0"])
    r06c4.locations.append(locations["r06c4y98x60"])
    r06c4.locations.append(locations["r06c4y18xe0"])
    r06c4.locations.append(locations["r06c4y18xd0"])
    r06c4.locations.append(locations["r06c4y58x10"])

    r06c6 = Region("r06c6", 54)
    r06c6.locations.append(locations["r06c6y58xe0"])
    r06c6.locations.append(locations["r06c6y18x10"])
    r06c6.locations.append(locations["r06c6y98x20"])
    r06c6.locations.append(locations["r06c6y18xe0"])
    r06c6.locations.append(locations["r06c6y58x10"])

    r06c7 = Region("r06c7", 55)
    r06c7.locations.append(locations["r06c7y98xa0"])
    r06c7.locations.append(locations["r06c7y98xc0"])
    r06c7.locations.append(locations["r06c7y58x10"])
    r06c7.locations.append(locations["r06c7y98xd0"])
    r06c7.locations.append(locations["r06c7y98xb0"])

    r07c1 = Region("r07c1", 57)
    r07c1.locations.append(locations["r07c1y18x10"])
    r07c1.locations.append(locations["r07c1y58x30"])
    r07c1.locations.append(locations["r07c1y18x90"])
    r07c1.locations.append(locations["r07c1y18x50"])
    r07c1.locations.append(locations["r07c1y58x40"])

    r07c3 = Region("r07c3", 59)
    r07c3.locations.append(locations["r07c3y58x60"])
    r07c3.locations.append(locations["r07c3y58x90"])
    r07c3.locations.append(locations["r07c3y98xd0"])
    r07c3.locations.append(locations["r07c3y58x80"])
    r07c3.locations.append(locations["r07c3y98x40"])
    r07c3.locations.append(locations["r07c3y98xc0"])

    r07c4 = Region("r07c4")
    r07c4.locations.append(locations["r07c4y18xe0"])
    r07c4.locations.append(locations["r07c4y18x10"])

    r07c5 = Region("r07c5", 61)
    r07c5.locations.append(locations["r07c5y98x80"])
    r07c5.locations.append(locations["r07c5y58xc0"])
    r07c5.locations.append(locations["r07c5y98x60"])
    r07c5.locations.append(locations["r07c5y18xe0"])
    r07c5.locations.append(locations["r07c5y98x40"])
    r07c5.locations.append(locations["r07c5y98x20"])

    r07c6 = Region("r07c6", 62)
    r07c6.locations.append(locations["r07c6y18x80"])
    r07c6.locations.append(locations["r07c6y98xa0"])
    r07c6.locations.append(locations["r07c6y18x10"])
    r07c6.locations.append(locations["r07c6y58xb0"])
    r07c6.locations.append(locations["r07c6y58x70"])
    r07c6.locations.append(locations["r07c6y58x30"])

    r07c7 = Region("r07c7", 63)
    r07c7.locations.append(locations["r07c7y18xd0"])
    r07c7.locations.append(locations["r07c7y18xc0"])
    r07c7.locations.append(locations["r07c7y18xe0"])
    r07c7.locations.append(locations["r07c7y18x10"])

    r08c3 = Region("r08c3", 67)
    r08c3.locations.append(locations["r08c3y18x10"])
    r08c3.locations.append(locations["r08c3y18xe0"])
    r08c3.locations.append(locations["r08c3y58xe0"])
    r08c3.locations.append(locations["r08c3y98x10"])
    r08c3.locations.append(locations["r08c3y18x70"])
    r08c3.locations.append(locations["r08c3y18x60"])

    r08c4ne = Region("r08c4ne", 68)
    r08c4ne.locations.append(locations["r08c4y18x40"])
    r08c4ne.locations.append(locations["r08c4y98xa0"])
    r08c4ne.locations.append(locations["r08c4y18x10"])
    r08c4ne.locations.append(locations["r08c4y18xe0"])
    r08c4ne.locations.append(locations["r08c4y58xe0"])

    r08c4sw = Region("r08c4sw")  # red scope room
    r08c4sw.locations.append(locations["r08c4y98x30"])

    r08c5 = Region("r08c5", 69)
    r08c5.locations.append(locations["r08c5y98x10"])
    r08c5.locations.append(locations["r08c5y98xc0"])
    r08c5.locations.append(locations["r08c5y98x30"])
    r08c5.locations.append(locations["r08c5y58x50"])
    r08c5.locations.append(locations["r08c5y58xa0"])
    r08c5.locations.append(locations["r08c5y98xe0"])

    r08c6 = Region("r08c6", 70)
    r08c6.locations.append(locations["r08c6y98x80"])
    r08c6.locations.append(locations["r08c6y58x80"])
    r08c6.locations.append(locations["r08c6y58x70"])
    r08c6.locations.append(locations["r08c6y98x70"])
    r08c6.locations.append(locations["r08c6y98x40"])
    r08c6.locations.append(locations["r08c6y18x10"])

    r08c7 = Region("r08c7", 71)
    r08c7.locations.append(locations["r08c7y18x50"])
    r08c7.locations.append(locations["r08c7y58x10"])
    r08c7.locations.append(locations["r08c7y18x70"])
    r08c7.locations.append(locations["r08c7y18x90"])
    r08c7.locations.append(locations["r08c7y98xe0"])

    r09c1 = Region("r09c1")
    r09c1.locations.append(locations["r09c1y98xc0"])
    r09c1.locations.append(locations["r09c1y98xe0"])
    r09c1.locations.append(locations["r09c1y58xe0"])

    r09c3 = Region("r09c3", 75)
    r09c3.locations.append(locations["r09c3y58x50"])
    r09c3.locations.append(locations["r09c3y58x40"])
    r09c3.locations.append(locations["r09c3y98x90"])
    r09c3.locations.append(locations["r09c3y18xe0"])
    r09c3.locations.append(locations["r09c3y98xa0"])

    r09c4 = Region("r09c4", 76)
    r09c4.locations.append(locations["r09c4y58x30"])
    r09c4.locations.append(locations["r09c4y18xe0"])
    r09c4.locations.append(locations["r09c4y58xa0"])
    r09c4.locations.append(locations["r09c4y58xe0"])
    r09c4.locations.append(locations["r09c4y58xd0"])

    r09c5 = Region("r09c5", 77)
    r09c5.locations.append(locations["r09c5y58x70"])
    r09c5.locations.append(locations["r09c5y58x20"])
    r09c5.locations.append(locations["r09c5y18x10"])
    r09c5.locations.append(locations["r09c5y58xa0"])
    r09c5.locations.append(locations["r09c5y58x50"])

    r09c7 = Region("r09c7")
    r09c7.locations.append(locations["r09c7y18xd0"])
    r09c7.locations.append(locations["r09c7y18xc0"])

    r10c1n = Region("r10c1n")
    r10c1n.locations.append(locations["r10c1y78xa0"])
    r10c1n.locations.append(locations["r10c1y58x70"])
    r10c1n.locations.append(locations["r10c1y58x40"])

    r10c1s = Region("r10c1s")
    r10c1s.locations.append(locations["r10c1y98x70"])

    r10c2 = Region("r10c2", 82)
    r10c2.locations.append(locations["r10c2y38x30"])
    r10c2.locations.append(locations["r10c2y58xe0"])
    r10c2.locations.append(locations["r10c2y98x80"])
    r10c2.locations.append(locations["r10c2y58x10"])
    r10c2.locations.append(locations["r10c2y58x70"])
    r10c2.locations.append(locations["r10c2y38xc0"])

    r10c3s = Region("r10c3s", 83)
    r10c3s.locations.append(locations["r10c3y98x50"])
    r10c3s.locations.append(locations["r10c3y98x70"])
    r10c3s.locations.append(locations["r10c3y98x90"])
    r10c3s.locations.append(locations["r10c3y58xe0"])
    r10c3s.locations.append(locations["r10c3y58x10"])

    r10c3n = Region("r10c3n")
    r10c3n.locations.append(locations["r10c3y18x20"])

    r10c4e = Region("r10c4e", 84)
    r10c4e.locations.append(locations["r10c4y18xa0"])
    r10c4e.locations.append(locations["r10c4y98x80"])
    r10c4e.locations.append(locations["r10c4y78xb0"])
    r10c4e.locations.append(locations["r10c4y58x80"])

    r10c4w = Region("r10c4w")
    r10c4w.locations.append(locations["r10c4y18x20"])
    r10c4w.locations.append(locations["r10c4y58x60"])

    r10c5 = Region("r10c5")  # main computer
    r10c5.locations.append(locations["r10c5y98x18"])  # could use "main" alias

    r11c1e = Region("r11c1e")
    r11c1e.locations.append(locations["r11c1y98xc0"])
    r11c1e.locations.append(locations["r11c1y98xe0"])
    r11c1e.locations.append(locations["r11c1y98xd0"])

    r11c1w = Region("r11c1w")
    r11c1w.locations.append(locations["r11c1y58x10"])
    r11c1w.locations.append(locations["r11c1y58x20"])

    r11c2 = Region("r11c2", 90)
    r11c2.locations.append(locations["r11c2y18x60"])
    r11c2.locations.append(locations["r11c2y18x50"])
    r11c2.locations.append(locations["r11c2y38x80"])
    r11c2.locations.append(locations["r11c2y58xb0"])
    r11c2.locations.append(locations["r11c2y38x90"])
    r11c2.locations.append(locations["r11c2y18x70"])

    r11c3 = Region("r11c3", 91)
    r11c3.locations.append(locations["r11c3y38x10"])
    r11c3.locations.append(locations["r11c3y98x80"])
    r11c3.locations.append(locations["r11c3y98x70"])
    r11c3.locations.append(locations["r11c3y98x60"])
    r11c3.locations.append(locations["r11c3y98xd0"])
    r11c3.locations.append(locations["r11c3y38x50"])

    r11c4 = Region("r11c4", 92)
    r11c4.locations.append(locations["r11c4y18x90"])
    r11c4.locations.append(locations["r11c4y18xa0"])
    r11c4.locations.append(locations["r11c4y98x80"])
    r11c4.locations.append(locations["r11c4y98xa0"])
    r11c4.locations.append(locations["r11c4y38x10"])
    r11c4.locations.append(locations["r11c4y58xe0"])

    r11c5w = Region("r11c5w", 93)
    r11c5w.locations.append(locations["r11c5y98x50"])
    r11c5w.locations.append(locations["r11c5y98x40"])
    r11c5w.locations.append(locations["r11c5y38x30"])
    r11c5w.locations.append(locations["r11c5y18x60"])

    r11c5e = Region("r11c5e")
    r11c5e.locations.append(locations["r11c5y58x50"])
    r11c5e.locations.append(locations["r11c5y58x60"])

    r11c6ne = Region("r11c6ne", 94)
    r11c6ne.locations.append(locations["r11c6y98xc0"])
    r11c6ne.locations.append(locations["r11c6y18xb0"])
    r11c6ne.locations.append(locations["r11c6y18x20"])
    r11c6ne.locations.append(locations["r11c6y18x90"])

    r11c6sw = Region("r11c6sw")
    r11c6sw.locations.append(locations["r11c6y98x50"])
    r11c6sw.locations.append(locations["r11c6y98x30"])

    r12c1 = Region("r12c1")
    r12c1.locations.append(locations["r12c1y18x10"])
    r12c1.locations.append(locations["r12c1y58xd0"])
    r12c1.locations.append(locations["r12c1y18x50"])
    r12c1.locations.append(locations["r12c1y18x30"])
    r12c1.locations.append(locations["r12c1y58xe0"])

    r12c2 = Region("r12c2", 98)
    r12c2.locations.append(locations["r12c2y38xb0"])
    r12c2.locations.append(locations["r12c2y18x10"])
    r12c2.locations.append(locations["r12c2y58x50"])
    r12c2.locations.append(locations["r12c2y18x30"])
    r12c2.locations.append(locations["r12c2y18x50"])

    r12c3 = Region("r12c3", 99)
    r12c3.locations.append(locations["r12c3y18x60"])
    r12c3.locations.append(locations["r12c3y18x80"])
    r12c3.locations.append(locations["r12c3y98xb0"])
    r12c3.locations.append(locations["r12c3y18x10"])
    r12c3.locations.append(locations["r12c3y18x70"])
    r12c3.locations.append(locations["r12c3y98xc0"])

    r12c4 = Region("r12c4", 100)
    r12c4.locations.append(locations["r12c4y18xa0"])
    r12c4.locations.append(locations["r12c4y98xe0"])
    r12c4.locations.append(locations["r12c4y18x70"])
    r12c4.locations.append(locations["r12c4y98x50"])
    r12c4.locations.append(locations["r12c4y58x10"])
    r12c4.locations.append(locations["r12c4y18x30"])

    r12c5s = Region("r12c5s", 101)
    r12c5s.locations.append(locations["r12c5y58xd0"])
    r12c5s.locations.append(locations["r12c5y98xd0"])
    r12c5s.locations.append(locations["r12c5y58xe0"])
    r12c5s.locations.append(locations["r12c5y98x10"])
    r12c5s.locations.append(locations["r12c5y58xc0"])
    r12c5s.locations.append(locations["r12c5y58x30"])

    r12c5n = Region("r12c5n")

    r12c6s = Region("r12c6s", 102)
    r12c6s.locations.append(locations["r12c6y58x20"])
    r12c6s.locations.append(locations["r12c6y98x20"])
    r12c6s.locations.append(locations["r12c6y58xa0"])
    r12c6s.locations.append(locations["r12c6y98xe0"])
    r12c6s.locations.append(locations["r12c6y98xb0"])

    r12c6n = Region("r12c6n")

    r13c1e = Region("r13c1e", 105)
    r13c1e.locations.append(locations["r13c1y58xa0"])
    r13c1e.locations.append(locations["r13c1y18x80"])
    r13c1e.locations.append(locations["r13c1y18x70"])
    r13c1e.locations.append(locations["r13c1y98xa0"])
    r13c1e.locations.append(locations["r13c1y58x90"])

    r13c1w = Region("r13c1w")
    r13c1w.locations.append(locations["r13c1y98x10"])

    r13c2 = Region("r13c2", 106)
    r13c2.locations.append(locations["r13c2y98x50"])
    r13c2.locations.append(locations["r13c2y98xb0"])
    r13c2.locations.append(locations["r13c2y98x70"])
    r13c2.locations.append(locations["r13c2y98x30"])
    r13c2.locations.append(locations["r13c2y98x90"])

    r13c3s = Region("r13c3s", 107)
    r13c3s.locations.append(locations["r13c3y58x30"])
    r13c3s.locations.append(locations["r13c3y58xc0"])
    r13c3s.locations.append(locations["r13c3y98xe0"])
    r13c3s.locations.append(locations["r13c3y58xd0"])
    r13c3s.locations.append(locations["r13c3y58xe0"])

    r13c3n = Region("r13c3n")

    r13c4 = Region("r13c4", 108)
    r13c4.locations.append(locations["r13c4y58x70"])
    r13c4.locations.append(locations["r13c4y58x80"])
    r13c4.locations.append(locations["r13c4y38x40"])
    r13c4.locations.append(locations["r13c4y38x30"])
    r13c4.locations.append(locations["r13c4y98x90"])

    r13c5nw = Region("r13c5nw", 109)
    r13c5nw.locations.append(locations["r13c5y58x70"])
    r13c5nw.locations.append(locations["r13c5y18x10"])
    r13c5nw.locations.append(locations["r13c5y98x80"])
    r13c5nw.locations.append(locations["r13c5y58x50"])
    r13c5nw.locations.append(locations["r13c5y58x90"])

    r13c5se = Region("r13c5se")  # canister behind the door
    r13c5se.locations.append(locations["r13c5y98xa0"])

    r13c6w = Region("r13c6w", 110)
    r13c6w.locations.append(locations["r13c6y18x50"])
    r13c6w.locations.append(locations["r13c6y58x30"])
    r13c6w.locations.append(locations["r13c6y98xa0"])
    r13c6w.locations.append(locations["r13c6y18x40"])
    r13c6w.locations.append(locations["r13c6y58x20"])

    r13c6e = Region("r13c6e")
    r13c6e.locations.append(locations["r13c6y18xe0"])

    r14c1ne = Region("r14c1ne")
    r14c1ne.locations.append(locations["r14c1y18x70"])
    r14c1ne.locations.append(locations["r14c1y18x10"])
    r14c1ne.locations.append(locations["r14c1y98xc0"])
    r14c1ne.locations.append(locations["r14c1y18x40"])

    r14c1sw = Region("r14c1sw")
    r14c1sw.locations.append(locations["r14c1y98x70"])
    r14c1sw.locations.append(locations["r14c1y98x30"])

    r14c2 = Region("r14c2", 114)
    r14c2.locations.append(locations["r14c2y78xb0"])
    r14c2.locations.append(locations["r14c2y38x10"])
    r14c2.locations.append(locations["r14c2y78x80"])
    r14c2.locations.append(locations["r14c2y98xd0"])
    r14c2.locations.append(locations["r14c2y98x60"])

    r14c3 = Region("r14c3", 115)
    r14c3.locations.append(locations["r14c3y38x40"])
    r14c3.locations.append(locations["r14c3y98x10"])
    r14c3.locations.append(locations["r14c3y18x70"])
    r14c3.locations.append(locations["r14c3y98xb0"])
    r14c3.locations.append(locations["r14c3y98xc0"])
    r14c3.locations.append(locations["r14c3y18x10"])

    r14c4 = Region("r14c4", 116)
    r14c4.locations.append(locations["r14c4y18x10"])
    r14c4.locations.append(locations["r14c4y98x70"])
    r14c4.locations.append(locations["r14c4y98xb0"])
    r14c4.locations.append(locations["r14c4y18x90"])
    r14c4.locations.append(locations["r14c4y98x90"])

    r14c5 = Region("r14c5", 117)
    r14c5.locations.append(locations["r14c5y38x10"])
    r14c5.locations.append(locations["r14c5y38xa0"])
    r14c5.locations.append(locations["r14c5y98xe0"])
    r14c5.locations.append(locations["r14c5y38x70"])
    r14c5.locations.append(locations["r14c5y58xe0"])
    r14c5.locations.append(locations["r14c5y38x40"])

    r14c6n = Region("r14c6n", 118)
    r14c6n.locations.append(locations["r14c6y18x10"])
    r14c6n.locations.append(locations["r14c6y18x30"])
    r14c6n.locations.append(locations["r14c6y58xd0"])
    r14c6n.locations.append(locations["r14c6y18x50"])
    r14c6n.locations.append(locations["r14c6y58xe0"])

    r14c6s = Region("r14c6s")
    r14c6s.locations.append(locations["r14c6y98x10"])

    r15c2nw = Region("r15c2nw", 122)
    r15c2nw.locations.append(locations["r15c2y18xc0"])
    r15c2nw.locations.append(locations["r15c2y98x30"])
    r15c2nw.locations.append(locations["r15c2y18x70"])
    r15c2nw.locations.append(locations["r15c2y58xd0"])
    r15c2nw.locations.append(locations["r15c2y58xb0"])

    r15c2se = Region("r15c2se")
    r15c2se.locations.append(locations["r15c2y98x80"])

    r15c3e = Region("r15c3e", 123)
    r15c3e.locations.append(locations["r15c3y58x70"])
    r15c3e.locations.append(locations["r15c3y18x50"])
    r15c3e.locations.append(locations["r15c3y18x80"])
    r15c3e.locations.append(locations["r15c3y18x70"])
    r15c3e.locations.append(locations["r15c3y18x60"])

    r15c3w = Region("r15c3w")
    r15c3w.locations.append(locations["r15c3y58x10"])

    r15c4 = Region("r15c4", 124)
    r15c4.locations.append(locations["r15c4y58x10"])
    r15c4.locations.append(locations["r15c4y58xe0"])
    r15c4.locations.append(locations["r15c4y18x70"])
    r15c4.locations.append(locations["r15c4y18x50"])
    r15c4.locations.append(locations["r15c4y98xe0"])

    r15c5 = Region("r15c5", 125)
    r15c5.locations.append(locations["r15c5y98x70"])
    r15c5.locations.append(locations["r15c5y98x20"])
    r15c5.locations.append(locations["r15c5y58xc0"])
    r15c5.locations.append(locations["r15c5y58xd0"])
    r15c5.locations.append(locations["r15c5y58xe0"])

    r15c6w = Region("r15c6w", 126)
    r15c6w.locations.append(locations["r15c6y98x50"])
    r15c6w.locations.append(locations["r15c6y98x60"])
    r15c6w.locations.append(locations["r15c6y78x30"])
    r15c6w.locations.append(locations["r15c6y78x20"])
    r15c6w.locations.append(locations["r15c6y58x10"])

    r15c6e = Region("r15c6e")
    r15c6e.locations.append(locations["r15c6y18xd0"])

    r16c2e = Region("r16c2e", 130)
    r16c2e.locations.append(locations["r16c2y18x70"])
    r16c2e.locations.append(locations["r16c2y18x60"])
    r16c2e.locations.append(locations["r16c2y60x80"])
    r16c2e.locations.append(locations["r16c2y18x50"])
    r16c2e.locations.append(locations["r16c2y18x80"])

    r16c2w = Region("r16c2w")
    r16c2w.locations.append(locations["r16c2y18x30"])

    # connections
    # TODO: change the door literals to region.door

    start.to(r02c7)
    r02c7.to(r01c7, door=r02c7.door)

    start.to(left_of_start, union=(Req(skill=1), Req(hp=300)))
    left_of_start.to(r02c0)
    left_of_start.to(r01c2)
    r01c2.to(r01c3, door=10)
    r01c3.to(r01c5, union=(Req(skill=1), Req(hp=180)))

    start.to(r03c5)
    r03c5.to(r03c4, door=29)
    r03c4.connections[r03c5].jump = 1
    r03c4.to(r03c3, door=28)
    r03c3.to(r03c2, door=27)

    r03c2.to(r04c1, door=26)
    r04c1.to(r04c2, door=33)
    r03c2.to(r04c2, door=26)

    r04c2.to(r04c4, door=34)
    r04c4.to(r04c5, door=36)

    between_blue_red = Region("between_blue_red")

    r04c5.to(between_blue_red, door=37)
    between_blue_red.to(r05c5)
    between_blue_red.to(r05c7)

    r05c7.to(r06c7, door=47, union=(Req(skill=1), Req(hp=360)))
    r06c7.connections[r05c7].hp = 120
    r06c7.to(r06c6, door=r06c7.door)

    # r06c6 is red junction

    # left

    r06c6.to(r06c4, door=r06c6.door)
    r06c4.to(r06c3, door=r06c4.door)
    r06c3.to(r05c3, door=r06c3.door)
    r05c3.to(r05c4sw, door=r05c3.door)
    r05c4sw.to(r05c4ne, door=r05c4sw.door, union=(Req(skill=1), Req(hp=300)))

    # down left

    r06c6.to(r07c6, door=55)
    r07c6.to(r07c5, door=62)
    r07c5.to(r07c4, door=r07c5.door)
    r07c4.to(r07c3)
    r07c3.to(r08c3, door=r07c3.door)
    r08c3.to(r08c4sw)

    # down right

    r07c6.to(r07c7, door=62)
    r07c7.to(r08c7, door=r07c7.door)
    r08c7.to(r08c6, door=r08c7.door)
    r08c6.to(r08c5, door=r08c6.door)
    r08c5.to(r08c4ne, door=r08c5.door)
    r08c4ne.to(r09c4, door=r08c4ne.door)
    r09c4.to(r09c5, door=r09c4.door)
    r09c5.to(r09c7, door=r09c5.door)
    r09c4.to(r09c3, door=r09c4.door)

    red_elevator = Region("red_elevator")

    r09c3.to(red_elevator, door=r09c3.door)
    r08c3.to(red_elevator, door=r08c3.door)
    r06c3.to(red_elevator, door=r06c3.door)
    red_elevator.to(r05c1)
    r05c1.to(r06c1, door=r05c1.door)
    r06c1.to(r07c1, door=r06c1.door)
    r07c1.to(r09c1, door=r07c1.door)

    big_elevator = Region("big_elevator")

    r07c1.to(big_elevator, door=r07c1.door)
    big_elevator.to(r11c1w)
    r11c1w.to(r10c1s, door=r11c2.door)  # this is a strange door req, not a mistake
    big_elevator.to(r13c1w)
    big_elevator.to(r14c1sw, door=r14c2.door)  # a not-as-strange door req
    big_elevator.to(r16c2w)
    big_elevator.to(r15c2nw)

    # paperclip time

    r15c2nw.to(r14c2, door=r15c2nw.door)
    r14c2.to(r14c1ne, door=r14c2.door)
    r14c1ne.to(r14c1sw)  # fall within room
    r14c1sw.connections[r14c1ne].jump = 5
    r14c2.to(r14c3, door=r14c2.door)
    r14c3.to(r13c3s, door=r14c3.door)
    r14c3.to(r14c4, door=r14c3.door)
    r14c4.to(r15c4, door=r14c4.door)
    r15c4.to(r15c3e, door=r15c4.door)
    r14c4.to(r13c4, door=r14c4.door)

    # long path paperclip junction

    # right

    r13c4.to(r13c5nw, door=r13c4.door)
    r13c5nw.to(r12c5s, door=r13c5nw.door)
    r12c5s.to(r12c6s, door=r12c5s.door)
    r13c5nw.to(r13c5se, door=r13c5nw.door)
    r13c5se.to(r14c5, door=r13c5nw.door)  # that's when this elevator appears
    r14c5.to(r15c5, door=r14c5.door)
    r15c5.connections[r14c5].jump = 3
    r15c5.to(r15c6w, door=r15c5.door, jump=3)
    # TODO: this r15c5 to r15c6w jump 3 is not required,
    # it's a workaround for reverse requirements (r15c5 to r14c5)
    # not being taken into account by the logic
    r13c5se.to(r13c6w)
    r13c6w.to(r14c6n, door=r13c6w.door)
    r13c6e.to(r13c6w)  # fall from red card
    r13c6w.connections[r13c6e].jump = 5

    # left

    r13c4.to(r13c3n, door=r13c4.door)
    r13c3n.to(r13c2, door=r13c3s.door)  # pre-opened door
    r13c2.to(r13c1e, door=r13c2.door)
    r13c1e.to(r12c1, door=r13c1e.door)
    r13c2.to(r12c2, door=r13c2.door, jump=3)
    r12c2.to(r12c3, door=r12c2.door)
    r12c3.to(r11c3, door=r12c3.door)
    r11c3.to(r11c4, door=r11c3.door)
    r11c4.to(r11c5w, door=r11c4.door)
    r11c4.to(r10c4e, door=r11c4.door)
    r11c3.to(r11c2, door=r11c3.door)
    r11c2.to(r11c1e, door=r11c2.door)
    r11c2.to(r10c2, door=r11c2.door)
    r10c2.to(r10c1n, door=r10c2.door)
    r10c2.to(r10c3s, door=r10c2.door)
    r10c3s.to(r10c4w, door=r10c3s.door)
    r10c4w.to(r10c3n, door=r10c4e.door)  # floppy  # pre-opened door

    # backtrack for Champ

    r12c3.to(r12c4, door=r12c3.door)
    r12c4.connections[r12c3].union = (Req(skill=1), Req(jump=5))  # not easy to get out of there
    r12c4.to(r12c5n, door=r12c4.door, jump=2)
    r12c5n.to(r12c6n, door=r12c5s.door)  # pre-opened door
    r12c6n.to(r11c6ne, door=r12c6s.door)  # pre-opened door
    r11c6ne.to(r11c5e, door=r11c6ne.door)  # Champ
    r11c5e.connections[r11c6ne].jump = 3  # This is why Champ couldn't get out.
    r11c5e.connections[r11c6ne].skill = 2  # hard jump - TODO: find out if this requires speed
    # TODO: or jump 5 to get out
    r11c5e.to(r11c6sw, door=r11c5w.door)  # pre-opened door

    # go mode!

    r14c3.to(r15c3w, door=r14c3.door)
    r15c3w.to(r15c2se, door=r15c3e.door)  # pre-opened door
    r15c2se.to(r16c2e, door=r15c2nw.door)  # or is this door always open? (doesn't matter unless I change map)
    r16c2e.to(r15c6e, door=r16c2e.door)  # long hallway
    r15c6e.to(r14c6s, door=r15c6w.door)  # pre-opened door
    final_elevator = Region("final_elevator")  # dun, dun, du-u-un-n-n-n....
    r14c6s.to(final_elevator, door=r14c6n.door)  # pre-opened door
    final_elevator.to(r13c6e)  # pick up red id card
    final_elevator.to(r10c5)  # main computer

    return start
