import pathlib
import yaml

class AgentConfig:
    """Load configuration from a YAML file.

    Expected keys in ``config.yaml``:
    - ``api_base``
    - ``api_key``
    - ``model``
    """

    def __init__(self, config_path: str | None = None):
        # Determine the path to the YAML configuration file.
        if config_path is None:
            config_path = pathlib.Path(__file__).with_name("config.yaml")
        else:
            config_path = pathlib.Path(config_path)

        # Load the YAML file; fall back to defaults if missing or malformed.
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            data = {}

        self.api_base: str = data.get("api_base", "http://gx10:8000/v1")
        self.api_key: str = data.get("api_key", "dummy")
        self.model: str = data.get("model", "gpt-oss-120b")
        self.vector_db: str = data.get("vector_db", "http://localhost:6333")
        # Tools schema name is constant for this project.
        self.tools: str = "TOOL_SCHEMAS"

