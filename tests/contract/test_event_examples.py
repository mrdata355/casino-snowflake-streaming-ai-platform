import json
from pathlib import Path

from jsonschema import Draft202012Validator

from local_demo.generator import generate_slot_events


def test_generated_events_match_slot_contract() -> None:
    schema = json.loads(Path("contracts/slot_event.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = []
    for event in generate_slot_events(20):
        errors.extend(validator.iter_errors(event.to_dict()))
    assert not errors
