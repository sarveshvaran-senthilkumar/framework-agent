import json

import uvicorn
from fastapi import FastAPI, HTTPException

import classes

app = FastAPI(title="Dynamic Class Loader")

REGISTRY_FILE = "class_reg.txt"
STRING_MAPPING_FILE = "string_mapping.txt"


def _load_class_map():
    with open(STRING_MAPPING_FILE, "r") as file:
        return json.load(file)


def invoke_class(class_name: str):
    key = class_name.lower()
    class_str = _load_class_map().get(key)
    if class_str is None:
        raise HTTPException(status_code=404, detail=f"Unknown class '{class_name}'")
    cls = getattr(classes, class_str, None)
    if cls is None:
        raise HTTPException(status_code=500, detail=f"Class '{class_str}' not found")
    return cls.load_all(REGISTRY_FILE, key)


@app.get("/{class_name}")
def get_records(class_name: str):
    records = invoke_class(class_name)
    return [vars(record) for record in records]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
