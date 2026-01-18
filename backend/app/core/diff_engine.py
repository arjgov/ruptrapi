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
            if method.startswith("x-") or method == "parameters" or method == "summary" or method == "description":
                continue # Skip metadata for now
            
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
        
        # 2. Compare Responses (simplified for V0)
        # TODO: Deep comparison of Request Body and Response Schemas

    def _compare_parameters(self, path: str, method: str, old_params: List[Dict], new_params: List[Dict]):
        # Map parameters by (name, in) unique key
        old_pmap = { (p["name"], p["in"]): p for p in old_params if "name" in p and "in" in p }
        new_pmap = { (p["name"], p["in"]): p for p in new_params if "name" in p and "in" in p }

        # Check Removed
        for key, p in old_pmap.items():
            if key not in new_pmap:
                self._add_change(
                    ChangeType.BREAKING,
                    Severity.MEDIUM,
                    f"Parameter '{p['name']}' (in {p['in']}) was removed.",
                    method=method,
                    path=path
                )

        # Check Added
        for key, p in new_pmap.items():
            if key not in old_pmap:
                is_required = p.get("required", False)
                if is_required:
                    self._add_change(
                        ChangeType.BREAKING,
                        Severity.HIGH,
                        f"Required parameter '{p['name']}' (in {p['in']}) was added.",
                        method=method,
                        path=path
                    )
                else:
                    self._add_change(
                        ChangeType.NON_BREAKING,
                        Severity.LOW,
                        f"Optional parameter '{p['name']}' (in {p['in']}) was added.",
                        method=method,
                        path=path
                    )
