import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def test_service_crud():
    # 1. Create Org
    suffix = str(uuid.uuid4())[:8]
    org_slug = f"svc-test-org-{suffix}"
    print(f"Creating Org: {org_slug}")
    res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"Svc Test Org {suffix}", "slug": org_slug})
    if res.status_code != 200:
        print(f"Failed to create org: {res.text}")
        return
    org_id = res.json()["id"]

    # 2. Create Service
    print("Creating Service...")
    res = httpx.post(f"{BASE_URL}/services/", json={
        "name": "Order Service",
        "description": "Handles orders",
        "base_path": "/api/v1/orders",
        "organization_id": org_id
    })
    if res.status_code != 200:
        print(f"Failed to create service: {res.text}")
        return
    service = res.json()
    service_id = service["id"]
    print(f"Created Service ID: {service_id}")
    
    # 3. Create Duplicate Service (Should Fail)
    print("Creating Duplicate Service...")
    res = httpx.post(f"{BASE_URL}/services/", json={
        "name": "Order Service",
        "organization_id": org_id
    })
    if res.status_code != 400:
        print(f"ERROR: Duplicate service creation did not fail. Status: {res.status_code}")
    else:
        print("Duplicate service check passed.")

    # 4. Update Service
    print("Updating Service...")
    res = httpx.patch(f"{BASE_URL}/services/{service_id}", json={
        "description": "Updated Description"
    })
    if res.json()["description"] != "Updated Description":
        print("Update failed")

    # 5. Soft Delete
    print("Soft Deleting Service...")
    res = httpx.patch(f"{BASE_URL}/services/{service_id}", json={"is_deleted": True})
    if not res.json()["is_deleted"]:
        print("Soft delete failed")

    # 6. List (ensure excluded)
    print("Listing services...")
    res = httpx.get(f"{BASE_URL}/services/?organization_id={org_id}")
    services = res.json()
    if any(s["id"] == service_id for s in services):
        print("ERROR: Soft deleted service found in list")
    else:
        print("SUCCESS: Service correctly excluded from list")

if __name__ == "__main__":
    try:
        test_service_crud()
    except Exception as e:
        print(f"Exception: {e}")
