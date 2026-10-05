#!/usr/bin/env python
import json
import sys
from typing import override

import numpy as np
import paho.mqtt.client as mqtt

import mkdd
from dolphin_mqtt import DolphinMqtt
from gamecube import *
from helpers import *
from mkdd import *
from stats import PlayerStats


class MkddMqtt(DolphinMqtt):
    def __init__(self) -> None:
        super().__init__("mkdd", "mkdd-gamestate")
        self.message_handlers = {
            "mkdd-remote": {
                "music_volume": self.on_set_music_volume,
                "pause": self.on_set_pause,
            },
            "mkdd-debug": {
                "find_vectors": self.on_find_vectors,
                "write_vectors": self.on_write_vectors,
            },
        }

        self.stats = [PlayerStats() for i in range(8)]

    def get_game_id(self, length: int = 6) -> str:
        game_id = super().get_game_id(length)
        if game_id == "GM4E01":
            marker = b"Mon Jul  5 13:04:10  2004"
            if dme.read_bytes(0x803608E0, len(marker)) == marker:
                game_id = "GM4E01dbg"

        return game_id

    def on_set_music_volume(self, client: mqtt.Client, msg: mqtt.MQTTMessage):
        vol = float(msg.payload.decode())
        # TODO: fix hardcoded address
        dme.write_float(0x803B0770, vol)

    def on_set_pause(self, client: mqtt.Client, msg: mqtt.MQTTMessage):
        # TODO: fix hardcoded address
        dme.write_byte(0x803CB6DC, int(msg.payload.decode()[0]))

    def on_find_vectors(self, client: mqtt.Client, msg: mqtt.MQTTMessage):
        data = json.loads(msg.payload)
        target = data.get("target", "player")
        max_dist = data.get("max_dist", 1000.0)
        if target == "player":
            target = self.curr_state["players"][0]["pos"]
            target = np.array(target)
        else:
            target = np.array(target)

        print(f"target pos: {target}")
        addrs, vecs = self.find_vectors(target, max_dist)

        lim = 500
        addrs = addrs[:lim].tolist()
        vecs = vecs[:lim].tolist()
        vecs = round_floats(vecs)
        self.emit("found_vectors", {"addrs": addrs, "vecs": vecs})

    def find_vectors(self, target, max_dist=1000):
        target = np.asarray(target, dtype=np.float64)
        data = dme.read_bytes(MEM1_START, MEM1_SIZE)

        n = MEM1_SIZE // 4
        floats = np.frombuffer(data, dtype=">f4", count=n).astype(np.float64)
        vecs = np.stack([floats[0 : n - 2], floats[1 : n - 1], floats[2:n]], axis=1)

        dist = np.linalg.norm(vecs - target, axis=1)
        mask = np.isfinite(dist) & (dist < max_dist)  # & (dist > 500.0)
        idxs = np.nonzero(mask)[0]

        order = idxs[np.argsort(dist[idxs])]  # closest first
        print(f"Found {len(idxs)} vectors")
        for k in order[:20]:
            addr = MEM1_START + int(k) * 4
            print(f"0x{addr:X}: dist={dist[k]:.3f}  vec={vecs[k]}")

        addrs = MEM1_START + order * 4
        return addrs, vecs[order]

    def on_write_vectors(self, client: mqtt.Client, msg: mqtt.MQTTMessage):
        data = json.loads(msg.payload)
        for addr, vec in zip(data["addrs"], data["vecs"]):
            dme.write_float(addr, vec[0])
            dme.write_float(addr + 4, vec[1])
            dme.write_float(addr + 8, vec[2])

    def read(self, spec: list, default=None):
        return r_struct(self.symbols, spec, default)

    @override
    def read_game_state(self):
        game_id = self.get_game_id()
        self.symbols = mkdd.SYMBOLS.get(game_id)
        if not self.symbols:
            return {"error": f"Unsupported game: {game_id}"}

        frames = self.read(["sRaceManager", "frame"], -1)
        start_signal_frames = self.read(["gMgr", "jugem", "*", "signal", "_188"], -1)
        lights = min(start_signal_frames // 60, 5)

        course_id = self.read(["msCourseID"]) or -1
        course_name = mkdd.COURSE_NAMES.get(course_id, f"unknown (0x{course_id:X})")
        course_codename = mkdd.COURSE_CODENAMES.get(course_id, "unknown")
        num_karts = self.read(["mKartCtrl", "kart_count"], 0)
        num_players = self.read(["gRaceInfo", "player_num"])

        # TODO: reliably detect if we are not in a race right now
        if num_karts > 8 or num_karts < 1:
            num_karts = 0

        items = {
            ITEM_ID[i]: [
                {"addr": hex(self.read(item) or 0)}
                | {field: self.read(item + [field]) for field in ITEM_OBJ}
                for item in iter_jsu_list(self.symbols, ["gItemMgr", "_3e8", [i]])
            ]
            for i in range(22)
        }

        # gMgr->_350 JsuLists:
        # 0: finish line, wanwan, ducks, water, tornado, the sun, desert spikes, traffic, fire wheels, fake piranha plants, skaters
        # 1: water on peach beach
        # 2: no idea, seems to be invisible objects floating all over the place
        # 3: lakitus and their stuff
        # 4: item boxes
        # 5: ?
        # 6: bridge
        # 7: origin?
        # 8: some (but not all) item boxes
        # 9: some of the rest of the item boxes
        state = {
            "entities": [
                {"addr": hex(self.read(item) or 0)}
                | {field: self.read(item + [field]) for field in GEOGRAPHY_OBJ}
                for item in iter_jsu_list(self.symbols, ["gMgr", "_350", [0]])
            ]
            + [
                {"addr": hex(self.read(item) or 0)}
                | {field: self.read(item + [field]) for field in GEOGRAPHY_OBJ}
                for item in iter_jsu_list(self.symbols, ["gMgr", "_350", [4]])
            ],
            "items": items,
            "race_frames": frames,
            "start_signal_frames": start_signal_frames,
            "start_lights": lights,
            "course_id": course_id,
            "course_name": course_name,
            "course_codename": course_codename,
            "total_laps": self.read(["sRaceManager", "total_lap_number"]),
            "num_karts": num_karts,
            "num_players": num_players,
            "players": [
                self.read_player_state(i, i < num_players) for i in range(num_karts)
            ],
            "game_pads": [
                (self.read(["mKartCtrl", "game_pads", [i]])) for i in range(16)
            ],
            "lap_times": [
                self.read(["gRaceInfo", "lap_times", [i]]) for i in range(num_karts)
            ],
        }

        w = self.read(["GeoWater::sSupervisor", "water_height"])
        if w:
            state["water_height"] = w

        for idx, p in enumerate(state["players"]):
            if start_signal_frames > 4 * 60:
                self.stats[idx].sample(p, frames)

            p["stats"] = self.stats[idx].as_dict()

        # if frames % 60 == 0:
        #    print(self.stats[0].get_stats())

        return state

    def read_player_state(self, i, is_player: bool = True):
        p = mkdd.PLAYER_DATA[i]

        result = {
            "player": i + 1,
            "items": [mkdd.ITEM_ID.get(self.read(item)) for item in p["items"]],
        } | {
            field: self.read(p[field])
            for field in p
            if isinstance(p[field], list) and field != "items"
        }

        result["base_addr"] = hex(result["base_addr"])

        if not is_player:
            del result["camera_pos"]
            del result["camera_look_pos"]
            del result["kart_cam_mtx"]

        char_ids = result["char_ids"]
        if char_ids:
            result["char_names"] = (
                mkdd.DRIVER_NAMES.get(char_ids[0], "unknown"),
                mkdd.DRIVER_NAMES.get(char_ids[1], "unknown"),
            )
        else:
            result["char_names"] = ["", ""]

        car_status = result["car_status"] or 0
        result["car_status__"] = car_status

        result["car_status"] = CarStatus(car_status).as_dict()

        return result

    @override
    def post_hook(self):
        game_id = self.get_game_id()
        self.symbols = mkdd.SYMBOLS.get(game_id)
        if not self.symbols:
            raise NotImplementedError(f"Unsupported game: {game_id}")

        print(f"Game: {game_id}")

    def reset_stats(self):
        for s in self.stats:
            s.reset()

    def detect_events(self, prev, curr):
        events = []

        lights = curr["start_lights"]
        if prev is None or prev["start_lights"] != lights:
            self.emit("start_lights", lights)
            events.append({"type": "start_lights", "start_lights": lights})

            if lights == 1:
                self.reset_stats()

        if prev is None:
            return events

        if lights > 0:
            frames = curr["race_frames"] - prev["race_frames"]
            curr["frame_diff"] = frames
            # assert frames < 2 # could maybe be done with 120hz polling but need to avoid sending redundant updates

        # per-player events
        m = min(len(prev["players"]), len(curr["players"]))
        for i in range(m):
            pp, pc = prev["players"][i], curr["players"][i]
            pnum = i + 1

            # lap completed
            if pc["lap"] > pp["lap"]:
                ev = {"type": "lap_complete", "player": pnum, "lap": pc["lap"]}
                if curr["total_laps"] is not None and pc["lap"] == curr["total_laps"]:
                    ev["final_lap"] = True

                events.append(ev)

            # position change (overtake)
            if pp["my_rank"] != pc["my_rank"]:
                events.append(
                    {
                        "type": "position_change",
                        "player": pnum,
                        "from": pp["my_rank"],
                        "to": pc["my_rank"],
                    }
                )

        return events


if __name__ == "__main__":
    try:
        m = MkddMqtt()
        m.main()
    except KeyboardInterrupt:
        sys.exit(0)
