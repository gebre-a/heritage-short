"""Stage 0: validate storyboard.json against the schema before anything runs."""
import json, sys
import jsonschema
from common import load_storyboard

sb = load_storyboard()
schema = json.load(open("schema/storyboard.schema.json"))
try:
    jsonschema.validate(sb, schema)
except jsonschema.ValidationError as e:
    sys.exit(f"INVALID storyboard: {e.message} at {list(e.absolute_path)}")

ids = [s["id"] for s in sb["shots"]]
if len(ids) != len(set(ids)):
    sys.exit("INVALID storyboard: duplicate shot ids")

words = sum(len(s["narration"].split()) for s in sb["shots"])
print(f"storyboard OK: {len(ids)} shots, {words} narration words")