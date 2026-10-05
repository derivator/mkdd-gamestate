# data type format characters:
# ? bool
# f f32
# B u8
# H u16
# i i32
# I u32
# Q u64


def jsu_list_def(ty):
    link = {"data": (ty, 0x0)}  # see update below
    list_ = {
        "head": (link, 0x0),
        "tail": (link, 0x4),
        "link_count": ("I", 0x8),
        "__size": 12,
    }
    link.update({"ptr_list": (list_, 0x4), "prev": (link, 0x8), "next": (link, 0xC)})
    return list_, link


JSU_LIST, JSU_LINK = jsu_list_def("I")

from helpers import Value, r_struct


def iter_jsu_list(ty, spec):
    count = r_struct(ty, spec + ["link_count"])
    if count == 0 or count == None:
        return

    # TODO: this is a bandaid fix to not turn your CPU into a space heater if we accidentally read a huge invalid number
    # the real fix would be to fix the underlying issue (which is either a bug or the fact that we are not reading synced to frames)
    if count > 500:
        return

    next = spec + ["head"]
    for i in range(count):
        yield next + ["data"]
        next = next + ["next"]


KART_CAMERA = {
    "mtx": ("12f", 0x80),
    "far": 0x154,
    "camera_pos": ("3f", 0x1E8),
    "camera_look_pos": ("3f", 0x1F4),
}

KART_BODY = {
    # "star_timer": ("H", [0xD4, 0x6]),
    "kart_item": ("12s", 0xF4),
    "char_ids": ("II", 0x104),
    "player_pos_mtx": ("12f", 0x140),
    "pos": ("fff", 0x23C),
    "speed": ("f", 0x444),
    "speed_scale": ("f", 0x470),
    "tire_angle": ("f", 0x478),
    "car_status": ("Q", 0x570),
    "game_status": ("I", 0x578),
    "boost_timer": ("H", 0x596),
    "mt_boost": ("H", 0x59E),
    "mt_boost_max": ("H", 0x5A0),
    "my_rank": ("B", 0x5C6),
    "mt_state": ("B", 0x5C7),
}

STICK = {
    "x": ("f", 0),
    "y": ("f", 0x4),
}

KART_GAME_PAD = {
    "button": ("I", 0x18),
    # "main_stick": (STICK, 0x48),
    # "sub_stick": (STICK, 0x58),
    "main_stick_x": ("f", 0x48),
    "main_stick_y": ("f", 0x48 + 4),
    # "sub_stick_x": ("f", 0x58),
    # "sub_stick_y": ("f", 0x58 + 4),
    "pad_type": ("I", 0xA8),
    "pad_port": ("i", 0xAC),
    "pad_state": ("I", 0xB0),
}

KART_CTRL = {
    "mKartCtrl": 0x803CC588,
    "game_pads": (KART_GAME_PAD, 0x20),
    # "kart_pads": ("I", 0x60),
    "kart_bodies": (KART_BODY, 0xA0),
    "kart_cams": (KART_CAMERA, 0x200),
    "kart_count": ("I", 0x22C),
}

KART_CHECKER = {
    "race_end": ("?", 0x29),
    "lap": ("I", 0x2C),
    "lap_progression": ("f", 0x48),
    "race_progression": ("f", 0x54),
}

G_ITEM_MGR = 0x803CBF40

ITEM_OBJ = {
    "pos": ("3f", 0x4),
    "max_vel": ("f", 0x30),
    "item_kind": ("I", 0x7C),
    "state": ("I", 0x118),
    "mtx": ("12f", 0xAC),
}

JSU_LIST_ITEM_OBJ, JSU_LINK_ITEM_OBJ = jsu_list_def(ITEM_OBJ)

ITEM_R_TURTLE = ITEM_OBJ | {"target_num": ("I", 0x2F0)}
ITEM_FLY_TURTLE = ITEM_OBJ | {"target_num": ("I", 0x2CC)}  # actually target_kart_num


ITEM_OBJ_MGR = {
    "stock_item_kind": ("I", [G_ITEM_MGR, 0x24C, 0]),
    "equip_item": (ITEM_OBJ, 0x2CC),
    "_3e8": (Value(JSU_LIST_ITEM_OBJ), 0x3E8),
    "_4f0": (Value(JSU_LIST_ITEM_OBJ), 0x4F0),
}

RACE_INFO = {
    "is_lan_mode": ("?", 0x01),
    "random_seed": ("I", 0x04),
    "race_mode": ("I", 0x08),
    "kart_num": ("H", 0x1C),
    "player_num": ("H", 0x1E),
    "console_num": ("H", 0x20),
    "status_num": ("H", 0x22),
    "finish_time": ("8I", 0x138),
    "lap_times": ("10I", 0x158),
}

RACE_MANAGER = {
    "frame": ("I", 0x24),
    "total_lap_number": ("H", 0x2E),
    "race_bgm_player": ("I", 0x3C),
    "console": ("I", 0x40),
    "course": ("I", 0x44),
    "kart_checker": (KART_CHECKER, 0x48),
}
JUGEM_ROD_SIGNAL = {"_188": ("I", 0x188)}

J_OFF = 0
JUGEM = {
    "jugem_item": ("I", 0x1B0 - J_OFF),
    "kart_num": ("b", 0x249 - J_OFF),
    "item": ("III", 0x258 - J_OFF),
    "signal": (JUGEM_ROD_SIGNAL, 0x26C - J_OFF),
}

GEOGRAPHY_OBJ = {
    "pos": ("3f", 0x4),
    "rot_mtx": ("12f", 0x10),
    "scale": ("3f", 0x40),
    "kind": ("I", 0x10C),
}
JSU_LIST_GEO_OBJ, JSU_LINK_GEO_OBJ = jsu_list_def(GEOGRAPHY_OBJ)


def array(ty):
    return {"*": (ty, 0x0)}


GEOGRAPHY_OBJ_MGR = {
    "vtable": ("I", 0x0),
    "root_heap": ("I", 0x4),
    "pointer_links": (Value(JSU_LINK), 0x8),
    "_350": (Value(JSU_LIST_GEO_OBJ), 0x350),
    "jugem": (array(JUGEM), 0x3FC),
    "kart_collide_pos": ("3f", 0x410),
    "kart_collide_radius": ("f", 0x470),
    "is_ballon_battle": ("?", 0x491),
    "is_bomb_battle": ("?", 0x492),
    # "is_robbery_battle": ("?", 0x493),
    "is_escape_battle": ("?", 0x494),
}

PAD_RECORDER = {
    "frames": ("I", 0x0),
}

GEO_WATER_SUPERVISOR = {"water_height": ("f", 0xFC)}

SYMBOLS_NTSC_U = {
    "msCourseID": ("I", 0x803CB6A8),  # not sure it's that var but works
    "sRaceManager": (RACE_MANAGER, 0x803CB7E8),
    "mspRecorder": (PAD_RECORDER, 0x803CBE5C),
    "gRaceInfo": (Value(RACE_INFO), 0x803B145C),
    "mKartCtrl": (KART_CTRL, 0x803CC588),  # actually called mCtrl
    "gMgr": (GEOGRAPHY_OBJ_MGR, 0x803CBEC0),
    "gItemMgr": (ITEM_OBJ_MGR, 0x803CBF40),
    "GeoWater::sSupervisor": (GEO_WATER_SUPERVISOR, 0x803CB89C),
}

SYMBOLS_DBG = {
    "msCourseID": ("I", 0x8041693C),
    "sRaceManager": (RACE_MANAGER, 0x804163A8),
    "mspRecorder": (PAD_RECORDER, 0x80416A54),
    "gRaceInfo": (Value(RACE_INFO), 0x803FBFA8),
    "mKartCtrl": (KART_CTRL, 0x804171A0),
    "gMgr": (GEOGRAPHY_OBJ_MGR, 0x80416AD0),
    "gItemMgr": (ITEM_OBJ_MGR, 0x80416B50),
    "GeoWater::sSupervisor": (GEO_WATER_SUPERVISOR, 0x80416464),
}


SYMBOLS = {
    "GM4E01": SYMBOLS_NTSC_U,  # NTSC-U
    "GM4E24": SYMBOLS_NTSC_U,  # LAN Edition
    "GM4E01dbg": SYMBOLS_DBG,  # Debug build
}

PLAYER_DATA = [
    {
        "items": [
            ["gItemMgr", "equip_item", [i * 2 + driver_idx], "item_kind"]
            for driver_idx in range(2)
        ],
        "base_addr": ["mKartCtrl", "kart_bodies", [i]],
        "kart_cam_mtx": [
            "mKartCtrl",
            "kart_cams",
            [i],
            "mtx",
        ],
        "camera_pos": ["mKartCtrl", "kart_cams", [i], "camera_pos"],
        "camera_look_pos": ["mKartCtrl", "kart_cams", [i], "camera_look_pos"],
    }
    | {field: ["mKartCtrl", "kart_bodies", [i], field] for field in KART_BODY}
    | {field: ["mKartCtrl", "game_pads", [2 * i], field] for field in KART_GAME_PAD}
    | {field: ["sRaceManager", "kart_checker", [i], field] for field in KART_CHECKER}
    for i in range(8)
]


COURSE_NAMES = {
    0x21: "Baby Park",
    0x22: "Peach Beach",
    0x23: "Daisy Cruiser",
    0x24: "Luigi Circuit",
    0x25: "Mario Circuit",
    0x26: "Yoshi Circuit",
    0x28: "Mushroom Bridge",
    0x29: "Mushroom City",
    0x2A: "Waluigi Stadium",
    0x2B: "Wario Colosseum",
    0x2C: "Dino Dino Jungle",
    0x2D: "DK Mountain",
    0x2F: "Bowser's Castle",
    0x31: "Rainbow Road",
    0x32: "Dry Dry Desert",
    0x33: "Sherbet Land",
    0x34: "Luigi's Mansion",
    0x35: "Nintendo GameCube",
    0x36: "Block City",
    0x37: "Unused",
    0x38: "Tilt-a-Kart",
    0x39: "Unused",
    0x3A: "Cookie Land",
    0x3B: "Pipe Plaza",
    0x44: "Award ceremony",
    0x45: "Ending credits",
}

COURSE_CODENAMES = {
    0x21: "BabyLuigi",
    0x22: "Peach",
    0x23: "Daisy",
    0x24: "Luigi",
    0x25: "Mario",
    0x26: "Yoshi",
    0x28: "Nokonoko",
    0x29: "Patapata",
    0x2A: "Waluigi",
    0x2B: "Wario",
    0x2C: "Diddy",
    0x2D: "Donkey",
    0x2F: "Koopa",
    0x31: "Rainbow",
    0x32: "Desert",
    0x33: "Snow",
    0x34: "Mini1",
    0x35: "Mini2",
    0x36: "Mini3",
    0x37: "Mini4",
    0x38: "Mini5",
    0x39: "Mini6",
    0x3A: "Mini7",
    0x3B: "Mini8",
    0x3C: "Reverse1",
    0x3D: "Reverse2",
    0x3E: "Reverse3",
    0x3F: "Reverse4",
    0x40: "Reverse5",
    0x41: "Reverse6",
    0x42: "Reverse7",
    0x43: "Reverse8",
    0x44: "Award",
    0x45: "Ending",
}


ITEM_NAMES = {
    0x00: "Green Shell",
    0x01: "Bowser's Shell",
    0x02: "Red Shell",
    0x03: "Banana",
    0x04: "Giant Banana",
    0x05: "Mushroom",
    0x06: "Star",
    0x07: "Chain Chomp",
    0x08: "Bob-omb",
    0x09: "Fireballs (Mario)",
    0x0A: "Lightning",
    0x0B: "Yoshi's Egg",
    0x0C: "Golden Mushroom",
    0x0D: "Spiny Shell",
    0x0E: "Heart",
    0x0F: "Fake Item",
    0x10: "None",
    0x11: "Triple Green Shells",
    0x12: "Triple Mushrooms",
    0x13: "Triple Red Shells",
    0x14: "Bob-omb",
    0x15: "Fireballs",
    0x16: "None",
    0x17: "Double Green Shells",
    0x18: "Double Mushrooms",
    0x19: "Double Red Shells",
    0x1A: "Fireballs (Luigi)",
    0x1B: "Birdo's Egg",
    0x1C: "Green Shell (?)",
    0x1D: "Mushroom (?)",
    0x1E: "Red Shell (?)",
}

ITEM_ID = {
    0x00: "kame_green",
    0x01: "koopa",
    0x02: "kame_red",
    0x03: "banana",
    0x04: "big_banana",
    0x05: "kinoko",
    0x06: "star",
    0x07: "wanwan",
    0x08: "bomb_hei",
    0x09: "fire_ball",
    0x0A: "thunder",
    0x0B: "egg",
    0x0C: "GoldenKinoko",
    0x0D: "kame_wing",
    0x0E: "heart",
    0x0F: "dummybox",
    0x10: "empty",
    0x11: "kame_green_3",
    0x12: "kinoko_3",
    0x13: "kame_red_3",
    0x14: "kame_green_3",
    0x15: "fire_ball",
    0x16: "empty",
    0x17: "kame_green_2",
    0x18: "kinoko_2",
    0x19: "kame_red_2",
    0x1A: "fire_ball_luigi",
    0x1B: "egg_catherine",
    0x1C: "kame_green",
    0x1D: "kinoko",
    0x1E: "kame_red",
}

ITEM_CLASS = {
    0x02: ITEM_R_TURTLE,
    0x0D: ITEM_FLY_TURTLE,
}

DRIVER_NAMES = {
    1: "BABY_MARIO",
    2: "BABY_LUIGI",
    3: "PARATROOPA",
    4: "KOOPATROOPA",
    5: "PEACH",
    6: "DAISY",
    7: "MARIO",
    8: "LUIGI",
    9: "WARIO",
    10: "WALUIGI",
    11: "YOSHI",
    12: "BIRDO",
    13: "DONKEY_KONG",
    14: "DIDDY_KONG",
    15: "BOWSER",
    16: "BOWSER_JR",
    17: "TOAD",
    18: "TOADETTE",
    19: "KING_BOO",
    20: "PETEY",
}

from enum import IntFlag


class CarStatus(IntFlag):
    DRIFT_R = 1
    DRIFT_L = 1 << 1
    S2 = 1 << 2
    S3 = 1 << 3
    S4 = 1 << 4
    SLOWDOWN = 1 << 5
    IN_AIR = 1 << 6
    CHANGING_DRIVER = 1 << 7
    S8 = 1 << 8
    S9 = 1 << 9
    CONTACT = 1 << 10  # rumble?
    BOOST = 1 << 11
    S12 = 1 << 12
    S13 = 1 << 13  # hit wanwan
    S14 = 1 << 14  # boosting via mushroom, hit other car
    S15 = 1 << 15  # boosting via mushroom/pad, hit other car
    S16 = 1 << 16
    S17 = 1 << 17  # boosting via pad

    INVULNERABLE = 1 << 18
    S19 = 1 << 19  # hit big banana
    HIT = 1 << 20  # hit banana, fake item, wanwan, big banana
    S21 = 1 << 21  # hit fake item
    S22 = 1 << 22
    S23 = 1 << 23
    S24 = 1 << 24  # hit banana
    S25 = 1 << 25
    S26 = 1 << 26
    S27 = 1 << 27
    S28 = 1 << 28  # hit sth with star
    S29 = 1 << 29
    S30 = 1 << 30

    AUTOPILOT = 1 << 31
    S32 = 1 << 32
    S33 = 1 << 33
    S34 = 1 << 34
    S35 = 1 << 35
    S36 = 1 << 36
    SKIDDING = 1 << 37
    S38 = 1 << 38
    S39 = 1 << 39
    S40 = 1 << 40

    def is_drifting(self):
        return self & CarStatus.DRIFT_R > 0 or self & CarStatus.DRIFT_L > 0

    def as_dict(self):
        d = {key.name.lower(): self & key > 0 for key in CarStatus}
        return d | {"drifting": self.is_drifting()}
