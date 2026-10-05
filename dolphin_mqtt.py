#!/usr/bin/env python3

import json
import sys
import time
from collections.abc import Callable

import dolphin_memory_engine as dme
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from gamecube import *
from helpers import *

type MessageHandlers = dict[str, Callable | MessageHandlers]


class JSONEncoderPlus(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return list(obj)

        return super().default(obj)


class DolphinMqtt:
    def __init__(self, namespace="dolphin", client_id="dolphin-mqtt") -> None:
        self.namespace = namespace
        self.poll_hz = 60
        self.mqttc = mqtt.Client(
            client_id=client_id, callback_api_version=CallbackAPIVersion.VERSION2
        )  # , protocol=mqtt.MQTTv5)
        self.mqttc.on_message = self.on_message

        self.mqttc.will_set(f"{self.namespace}/status", "offline", 1, retain=True)
        self.message_handlers: MessageHandlers = {}

    def subscribe(self):
        self.mqttc.subscribe("mkdd-debug/#")
        self.mqttc.subscribe("mkdd-remote/#")

    def on_message(self, client: mqtt.Client, _userdata, msg: mqtt.MQTTMessage):
        print(msg.topic, " ", msg.payload)
        d = self.message_handlers
        for part in msg.topic.split("/"):
            if type(d) == dict and part in d:
                d = d[part]
            else:
                print(f"unhandled message: {msg.topic}")
                return

        d(client, msg)

    def emit(self, topic, msg, **kwargs):
        if type(msg) == dict:
            output = json.dumps(msg, separators=(",", ":"), cls=JSONEncoderPlus)
            # print(output)
            self.mqttc.publish(
                f"{self.namespace}/{topic}",
                output,
                **kwargs,
            )
        else:
            self.mqttc.publish(f"{self.namespace}/{topic}", msg, **kwargs)

    def wait_for_hook(self):
        """Attach to Dolphin, retrying until emulation is running."""
        while not dme.is_hooked():
            dme.hook()
            if dme.is_hooked():
                print("status: hooked")
                self.post_hook()
                self.emit("status", "hooked", retain=True)
                return

            print("status: waiting for hook")
            self.emit("status", "waiting", retain=True)
            time.sleep(1.0)

    def get_game_id(self, length: int = 6) -> str:
        """
        Get the Game ID of the currently hooked Dolphin instance.
        Supports custom length to support extended IDs from mods.
        """
        dme.assert_hooked()
        data = dme.read_bytes(MEM1_START, length)
        return data.decode("ascii", errors="replace")

    def read_game_state(self):
        return {}

    def detect_events(self, prev, curr):
        return []

    def post_hook(self):
        pass

    def main(self):
        prev_state = None
        self.curr_state = None

        print("connecting to mqtt")
        self.mqttc.connect("localhost")
        self.subscribe()
        self.mqttc.loop_start()

        self.wait_for_hook()

        self.emit("game_id", self.get_game_id(), retain=True)

        duty_cycle = 0
        print("running")
        while True:
            loop_start = time.perf_counter()
            if not dme.is_hooked():
                prev_state = None
                self.wait_for_hook()

            error = False
            try:
                self.curr_state = self.read_game_state()
                error = "error" in self.curr_state
            except Exception as e:  # noqa BLE001
                self.curr_state = {"error": repr(e)}
                print(repr(e))
                error = True

            events = []
            if not error:
                try:
                    events = self.detect_events(prev_state, self.curr_state)
                except Exception as e:  # noqa BLE001
                    print(repr(e))
                    events = [{"error": repr(e)}]

            self.emit(
                "game_state",
                {
                    "time": time.time(),  # wall-clock timestamp
                    "state": self.curr_state,
                    "events": events,
                    "duty_cycle": duty_cycle,
                },
            )

            prev_state = self.curr_state

            # Keep a steady sample rate.
            elapsed = time.perf_counter() - loop_start

            period = 1.0 / self.poll_hz
            duty_cycle = elapsed / period
            if elapsed < period:
                time.sleep(period - elapsed)


if __name__ == "__main__":
    try:
        m = DolphinMqtt()
        m.main()
    except KeyboardInterrupt:
        sys.exit(0)
