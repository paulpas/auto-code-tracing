import yaml, logging, pathlib
log = logging.getLogger(__name__)

class Planner:
    def __init__(self, yaml_path=None):
        self.yaml_path = pathlib.Path(yaml_path or __file__).with_name('planner.yaml')
        self.cfg = yaml.safe_load(self.yaml_path.open())
        log.info("Loaded planner config")
