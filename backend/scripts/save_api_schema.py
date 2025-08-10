import json
from app.main import app

# Generate and save the OpenAPI schema to a file
with open("../openapi.json", "w") as f:
    schema = app.openapi()
    f.write(json.dumps(schema, indent=2))
