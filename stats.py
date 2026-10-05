class PlayerStats:
    def __init__(self):
        self.samples = 0
        self.speed = 0
        self.drift = 0
        self.boost = 0

        self.lap_frames = []

    def reset(self):
        self.__init__()

    def sample(self, player: dict, frames: int):
        self.samples += 1
        self.speed += player["speed"]
        self.boost += int(player["boost_timer"] > 0)
        self.drift += int(player["car_status"]["drifting"])

        if player["lap"] - 1 > len(self.lap_frames):
            self.lap_frames.append(frames)

    def as_dict(self) -> dict[str, float]:
        samples = max(self.samples, 1)
        return {
            "speed": self.speed / samples,
            "drift": self.drift / samples,
            "boost": self.boost / samples,
            "lap_frames": self.lap_frames,
        }
