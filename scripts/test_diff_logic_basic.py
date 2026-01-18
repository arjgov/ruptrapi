import sys
import os

# Adjust path to find app module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.diff_engine import DiffEngine
from app.models.analysis import ChangeType, Severity

def test_diff_engine():
    old_spec = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False}
                    ]
                },
                "post": {}
            },
            "/deleted-endpoint": {
                "get": {}
            }
        }
    }

    new_spec = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False}, # Existing
                        {"name": "offset", "in": "query", "required": True}  # NEW REQUIRED -> BREAKING
                    ]
                }
                # POST removed -> BREAKING
            },
            "/new-endpoint": { # Added -> NON_BREAKING
                "get": {}
            }
        }
    }

    engine = DiffEngine()
    changes = engine.compute_diff(old_spec, new_spec)

    print(f"Computed {len(changes)} changes:")
    for c in changes:
        print(f"[{c['change_type']}] [{c['severity']}] {c['http_method']} {c['path']}: {c['description']}")

    # Assertions
    # 1. /deleted-endpoint removed
    assert any(c['path'] == "/deleted-endpoint" and c['change_type'] == ChangeType.BREAKING for c in changes), "Missing deleted path detection"
    
    # 2. /users POST removed
    assert any(c['path'] == "/users" and c['http_method'] == "POST" and c['change_type'] == ChangeType.BREAKING for c in changes), "Missing removed method detection"
    
    # 3. /users GET new param 'offset' (Required)
    assert any(c['path'] == "/users" and c['http_method'] == "GET" and "offset" in c['description'] and c['change_type'] == ChangeType.BREAKING for c in changes), "Missing new required param detection"

    # 4. /new-endpoint added
    assert any(c['path'] == "/new-endpoint" and c['change_type'] == ChangeType.NON_BREAKING for c in changes), "Missing added path detection"

    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    test_diff_engine()
