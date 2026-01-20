from typing import List, Dict, Any, Optional
import copy
from app.models.analysis import ChangeType, Severity

class DiffEngine:
    """
    Compares two OpenAPI specifications and detects changes.
    """

    def __init__(self):
        self.changes = []

    def compute_diff(self, old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main entry point. Returns a list of dicts representing ApiChange objects.
        Warning: This does NOT save to DB. It returns dictionaries.
        """
        self.changes = []
        self.old_spec = old_spec
        self.new_spec = new_spec

        # 1. Compare Paths
        self._compare_paths()

        return self.changes

    def _add_change(self, 
                    change_type: ChangeType, 
                    severity: Severity, 
                    description: str, 
                    method: Optional[str] = None, 
                    path: Optional[str] = None):
        self.changes.append({
            "change_type": change_type,
            "severity": severity,
            "description": description,
            "http_method": method,
            "path": path
        })

    def _compare_paths(self):
        old_paths = self.old_spec.get("paths", {})
        new_paths = self.new_spec.get("paths", {})

        # Removed Paths
        for path in old_paths:
            if path not in new_paths:
                self._add_change(
                    ChangeType.BREAKING, 
                    Severity.HIGH, 
                    f"Path '{path}' was removed.", 
                    path=path
                )
            else:
                # Path exists in both, compare operations
                self._compare_operations(path, old_paths[path], new_paths[path])

        # Added Paths
        for path in new_paths:
            if path not in old_paths:
                self._add_change(
                    ChangeType.NON_BREAKING, 
                    Severity.LOW, 
                    f"Path '{path}' was added.", 
                    path=path
                )

    def _compare_operations(self, path: str, old_path_item: Dict, new_path_item: Dict):
        # Operations are keys like 'get', 'post', 'put', 'delete', etc.
        # Ignore keys starting with 'x-' or 'parameters' (top-level path params handled separately if needed)
        
        # Merge keys to iterate
        all_methods = set(old_path_item.keys()) | set(new_path_item.keys())
        
        for method in all_methods:
            # Only process valid HTTP methods
            if method.lower() not in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}:
                continue
            
            method_upper = method.upper()

            if method not in new_path_item:
                self._add_change(
                    ChangeType.BREAKING, 
                    Severity.HIGH, 
                    f"Operation {method_upper} {path} was removed.", 
                    method=method_upper, 
                    path=path
                )
                continue
            
            if method not in old_path_item:
                self._add_change(
                    ChangeType.NON_BREAKING, 
                    Severity.LOW, 
                    f"Operation {method_upper} {path} was added.", 
                    method=method_upper, 
                    path=path
                )
                continue

            # Compare specific operation details
            self._compare_operation_details(
                path, 
                method_upper, 
                old_path_item[method], 
                new_path_item[method]
            )

    def _compare_operation_details(self, path: str, method: str, old_op: Dict, new_op: Dict):
        # 1. Compare Parameters
        self._compare_parameters(path, method, old_op.get("parameters", []), new_op.get("parameters", []))
        
        # 2. Compare Request Body
        self._compare_request_body(path, method, old_op.get("requestBody"), new_op.get("requestBody"))
        
        # 3. Compare Responses
        self._compare_responses(path, method, old_op.get("responses", {}), new_op.get("responses", {}))

    def _compare_request_body(self, path: str, method: str, old_body: Optional[Dict], new_body: Optional[Dict]):
        """Compare request body schemas"""
        # Request body removed
        if old_body and not new_body:
            self._add_change(
                ChangeType.BREAKING,
                Severity.HIGH,
                f"Request body was removed.",
                method=method,
                path=path
            )
            return
        
        # Request body added
        if not old_body and new_body:
            is_required = new_body.get("required", False)
            if is_required:
                self._add_change(
                    ChangeType.BREAKING,
                    Severity.HIGH,
                    f"Required request body was added.",
                    method=method,
                    path=path
                )
            else:
                self._add_change(
                    ChangeType.NON_BREAKING,
                    Severity.LOW,
                    f"Optional request body was added.",
                    method=method,
                    path=path
                )
            return
        
        # Both exist - compare schemas
        if old_body and new_body:
            old_schema = old_body.get("content", {}).get("application/json", {}).get("schema", {})
            new_schema = new_body.get("content", {}).get("application/json", {}).get("schema", {})
            
            if old_schema or new_schema:
                self._compare_schema(path, method, old_schema, new_schema, context="request body")

    def _compare_responses(self, path: str, method: str, old_responses: Dict, new_responses: Dict):
        """Compare response schemas (focusing on 200/2xx responses)"""
        # Check success responses (200, 201, etc.)
        success_codes = ["200", "201", "202", "204"]
        
        for code in success_codes:
            old_resp = old_responses.get(code)
            new_resp = new_responses.get(code)
            
            if old_resp and not new_resp:
                self._add_change(
                    ChangeType.BREAKING,
                    Severity.HIGH,
                    f"Response {code} was removed.",
                    method=method,
                    path=path
                )
                continue
            
            if not old_resp or not new_resp:
                continue
            
            # Compare response schemas
            old_schema = old_resp.get("content", {}).get("application/json", {}).get("schema", {})
            new_schema = new_resp.get("content", {}).get("application/json", {}).get("schema", {})
            
            if old_schema or new_schema:
                self._compare_schema(path, method, old_schema, new_schema, context=f"response {code}")

    def _compare_schema(self, path: str, method: str, old_schema: Dict, new_schema: Dict, context: str = "schema"):
        """Compare two JSON schemas for breaking changes"""
        # Compare properties (fields)
        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))
        
        # Check removed fields
        for field_name in old_props:
            if field_name not in new_props:
                if "response" in context:
                    self._add_change(
                        ChangeType.BREAKING,
                        Severity.HIGH,
                        f"Response field '{field_name}' was removed.",
                        method=method,
                        path=path
                    )
                else:
                    self._add_change(
                        ChangeType.BREAKING,
                        Severity.MEDIUM,
                        f"Request field '{field_name}' was removed.",
                        method=method,
                        path=path
                    )
        
        # Check added fields
        for field_name in new_props:
            if field_name not in old_props:
                if field_name in new_required:
                    self._add_change(
                        ChangeType.BREAKING,
                        Severity.HIGH,
                        f"Required field '{field_name}' was added to {context}.",
                        method=method,
                        path=path
                    )
                else:
                    self._add_change(
                        ChangeType.NON_BREAKING,
                        Severity.LOW,
                        f"Optional field '{field_name}' was added to {context}.",
                        method=method,
                        path=path
                    )
            else:
                # Field exists in both - check type changes
                old_field = old_props[field_name]
                new_field = new_props[field_name]
                
                old_type = old_field.get("type")
                new_type = new_field.get("type")
                
                if old_type and new_type and old_type != new_type:
                    self._add_change(
                        ChangeType.BREAKING,
                        Severity.HIGH,
                        f"Field '{field_name}' type changed from '{old_type}' to '{new_type}' in {context}.",
                        method=method,
                        path=path
                    )


    def _compare_parameters(self, path: str, method: str, old_params: List[Dict], new_params: List[Dict]):
        # Map parameters by (name, in) unique key
        old_pmap = { (p["name"], p["in"]): p for p in old_params if "name" in p and "in" in p }
        new_pmap = { (p["name"], p["in"]): p for p in new_params if "name" in p and "in" in p }

        # Check Removed
        for key, old_p in old_pmap.items():
            if key not in new_pmap:
                self._add_change(
                    ChangeType.BREAKING,
                    Severity.MEDIUM,
                    f"Parameter '{old_p['name']}' (in {old_p['in']}) was removed.",
                    method=method,
                    path=path
                )

        # Check Added
        for key, new_p in new_pmap.items():
            if key not in old_pmap:
                is_required = new_p.get("required", False)
                if is_required:
                    self._add_change(
                        ChangeType.BREAKING,
                        Severity.HIGH,
                        f"Required parameter '{new_p['name']}' (in {new_p['in']}) was added.",
                        method=method,
                        path=path
                    )
                else:
                    self._add_change(
                        ChangeType.NON_BREAKING,
                        Severity.LOW,
                        f"Optional parameter '{new_p['name']}' (in {new_p['in']}) was added.",
                        method=method,
                        path=path
                    )
            else:
                # Parameter exists in both - check for type changes
                old_p = old_pmap[key]
                self._compare_parameter_schema(path, method, old_p, new_p)

    def _compare_parameter_schema(self, path: str, method: str, old_param: Dict, new_param: Dict):
        """Compare schema changes for a parameter that exists in both versions"""
        param_name = old_param.get("name", "unknown")
        param_in = old_param.get("in", "unknown")
        
        # Get schema (can be direct or nested in schema key)
        old_schema = old_param.get("schema", old_param)
        new_schema = new_param.get("schema", new_param)
        
        # Check type changes
        old_type = old_schema.get("type")
        new_type = new_schema.get("type")
        
        if old_type and new_type and old_type != new_type:
            self._add_change(
                ChangeType.BREAKING,
                Severity.HIGH,
                f"Parameter '{param_name}' (in {param_in}) type changed from '{old_type}' to '{new_type}'.",
                method=method,
                path=path
            )
        
        # Check required flag changes
        old_required = old_param.get("required", False)
        new_required = new_param.get("required", False)
        
        if not old_required and new_required:
            self._add_change(
                ChangeType.BREAKING,
                Severity.HIGH,
                f"Parameter '{param_name}' (in {param_in}) is now required.",
                method=method,
                path=path
            )
        elif old_required and not new_required:
            self._add_change(
                ChangeType.NON_BREAKING,
                Severity.LOW,
                f"Parameter '{param_name}' (in {param_in}) is no longer required.",
                method=method,
                path=path
            )
