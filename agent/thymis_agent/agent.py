from dataclasses import dataclass
import json
import logging
import pathlib
import sched

from httpcore import URL

logger = logging.getLogger(__name__)

class AgentScheduler(sched.scheduler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def periodic(self, interval, action, actionargs=()):
        self.enter(interval, 1, self.periodic, (interval, action, actionargs))
        action(*actionargs)

class Storage:

    path: pathlib.Path = pathlib.Path("/var") / "lib" / "thymis-agent" / "device.json"

    def __init__(self):
        pass

    def read_state(self):
        # read the state from the json file to a dictionary
        text = self.path.read_text()
        # parse the json to a dictionary
        return json.loads(text)
    
    def write_state(self, state):
        json_text = json.dumps(state)
        self.path.write_text(json_text)


@dataclass
class DeviceState:
    registered: bool = False
    identifier: str | None = None
    name: str | None = None


class Agent:
    controller_host: str
    storage: Storage

    def __init__(self, controller_host: URL):
        self.controller_host = controller_host
        self.storage = Storage()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    scheduler = AgentScheduler()
    scheduler.periodic(1, print, ("Hello, world!",))
    scheduler.run()