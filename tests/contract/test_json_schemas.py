import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_contracts_are_valid_json_schema():
    for path in Path("contracts").glob("*.schema.json"):
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)
