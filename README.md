# mkdd-gamestate

mkdd-gamestate uses py-dolphin-memory-engine to extract game state from Mario Kart Double Dash and publishes it via MQTT. It was inspired by [Counter-Strike's Game State Integration](https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Game_State_Integration) and the spectator features of [CTWC](https://thectwc.com/). Extracting the game state allows for several things that might be useful to tournament organizers, such as the creation of spectator overlays and syncing lights (or other real-world things) to game events.

## Usage

You can use `uv run main.py` to install dependencies and run the project. You need an MQTT broker running on localhost, configured to allow large messages, see `rumqttd/docker-compose.yml` for a known-good setup. On Linux `run.sh` has everything you need.

## MQTT Topics

The main topics published are:

- `mkdd/status`: status of the Dolphin process hook
- `mkdd/game_id`: the Game ID of the currently loaded game, e.g. `GM4E01` for NTSC-U MKDD
- `mkdd/game_state`: a JSON dictionary of various game state, sent once per frame
- `mkdd/start_lights`: state of the pre-race countdown

## TODO:

There are still a number of issues to be resolved and enhancements to be made:

- Memory reads are not synced to frames, sometimes a frame will be missed, leading to visual glitches
- Non-race gamestates (being in a menu) are not handled yet

## Compatibility

The goal is compatibility with all versions of MKDD, the current state is:

- [x] NTSC-U
- [x] Debug build
- [ ] NTSC-J
- [ ] PAL
- [x] Mods based on compatible versions should work, e.g. [LAN Edition](https://mkdd.org/wiki/Mario_Kart:_Double_Dash!!_LAN_Edition)

Due to an [issue](https://github.com/randovania/py-dolphin-memory-engine/issues/12) in py-dolphin-memory-engine, versions that request increased RAM size can only be hooked with Dolphin versions <=2606.

## LLM usage disclosure

The project started as a small entirely vibe-coded proof of concept, since then almost all of that code has been rewritten by hand, except for trivial stuff like converting HTML tables into dictionaries.
