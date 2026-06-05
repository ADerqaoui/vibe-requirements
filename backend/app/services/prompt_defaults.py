"""Settings-backed prompt default variant map."""
import json

from sqlalchemy.orm import Session

from app.models.setting import Setting

PROMPT_DEFAULTS_KEY = "prompt_defaults"


def default_key(task: str, layer_id: int | None) -> str:
    """Return the stable settings-map key for a task/layer group."""
    return f"{task}|{layer_id if layer_id is not None else 'null'}"


def read_prompt_defaults(db: Session) -> dict[str, str]:
    """Read prompt defaults from the settings key-value table."""
    setting = db.get(Setting, PROMPT_DEFAULTS_KEY)
    if setting is None or setting.value is None or setting.value.strip() == "":
        return {}
    try:
        parsed = json.loads(setting.value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): str(value) for key, value in parsed.items() if isinstance(value, str)}


def write_prompt_defaults(db: Session, defaults: dict[str, str]) -> None:
    """Persist prompt defaults as compact JSON in one settings row."""
    value = json.dumps(defaults, sort_keys=True, separators=(",", ":"))
    setting = db.get(Setting, PROMPT_DEFAULTS_KEY)
    if setting is None:
        db.add(Setting(key=PROMPT_DEFAULTS_KEY, value=value))
        return
    setting.value = value
