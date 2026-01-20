"""
Comprehensive test script for DiffEngine detection enhancements
Tests all scenarios from the user's test matrix
"""

from app.core.diff_engine import DiffEngine

def test_parameter_removal():
    print("\n=== Test: Parameter Removal ===")
    old_spec = {
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {"name": "id", "in": "query", "required": True, "schema": {"type": "string"}}
                    ]
                }
            }
        }
    }
    new_spec = {
        "paths": {
            "/test": {
                "get": {
                    "parameters": []
                }
            }
        }
    }
    
    engine = DiffEngine()
    changes = engine.compute_diff(old_spec, new_spec)
    
    print(f"Found {len(changes)} changes:")
    for c in changes:
        print(f"  - {c['severity']}/{c['change_type']}: {c['description']}")
    
    assert any("removed" in c['description'].lower() and "id" in c['description'] for c in changes), "Parameter removal not detected!"
    print("✅ PASS")

def test_parameter_type_change():
    print("\n=== Test: Parameter Type Change ===")
    old_spec = {
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {"name": "count", "in": "query", "schema": {"type": "string"}}
                    ]
                }
            }
        }
    }
    new_spec = {
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {"name": "count", "in": "query", "schema": {"type": "integer"}}
                    ]
                }
            }
        }
    }
    
    engine = DiffEngine()
    changes = engine.compute_diff(old_spec, new_spec)
    
    print(f"Found {len(changes)} changes:")
    for c in changes:
        print(f"  - {c['severity']}/{c['change_type']}: {c['description']}")
    
    assert any("type changed" in c['description'].lower() for c in changes), "Type change not detected!"
    print("✅ PASS")

def test_response_field_removal():
    print("\n=== Test: Response Field Removal ===")
    old_spec = {
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = {
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    engine = DiffEngine()
    changes = engine.compute_diff(old_spec, new_spec)
    
    print(f"Found {len(changes)} changes:")
    for c in changes:
        print(f"  - {c['severity']}/{c['change_type']}: {c['description']}")
    
    assert any("name" in c['description'].lower() and "removed" in c['description'].lower() for c in changes), "Response field removal not detected!"
    print("✅ PASS")

def test_response_field_addition():
    print("\n=== Test: Response Field Addition ===")
    old_spec = {
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = {
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "id": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    engine = DiffEngine()
    changes = engine.compute_diff(old_spec, new_spec)
    
    print(f"Found {len(changes)} changes:")
    for c in changes:
        print(f"  - {c['severity']}/{c['change_type']}: {c['description']}")
    
    assert any("email" in c['description'].lower() and "added" in c['description'].lower() for c in changes), "Response field addition not detected!"
    print("✅ PASS")

def test_response_type_change():
    print("\n=== Test: Response Type Change ===")
    old_spec = {
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "count": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = {
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "count": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    engine = DiffEngine()
    changes = engine.compute_diff(old_spec, new_spec)
    
    print(f"Found {len(changes)} changes:")
    for c in changes:
        print(f"  - {c['severity']}/{c['change_type']}: {c['description']}")
    
    assert any("type changed" in c['description'].lower() and "count" in c['description'].lower() for c in changes), "Response type change not detected!"
    print("✅ PASS")

if __name__ == "__main__":
    print("=" * 60)
    print("DiffEngine Enhanced Detection Test Suite")
    print("=" * 60)
    
    try:
        test_parameter_removal()
        test_parameter_type_change()
        test_response_field_removal()
        test_response_field_addition()
        test_response_type_change()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
