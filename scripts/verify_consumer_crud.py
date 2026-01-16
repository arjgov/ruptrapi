import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def test_consumer_crud():
    # 1. Create Org
    suffix = str(uuid.uuid4())[:8]
    org_slug = f"cons-test-org-{suffix}"
    print(f"Creating Org: {org_slug}")
    res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"Cons Test Org {suffix}", "slug": org_slug})
    if res.status_code != 200:
        print(f"Failed to create org: {res.text}")
        return
    org_id = res.json()["id"]

    # 2. Create Service (needed for dependency)
    print("Creating Service...")
    res = httpx.post(f"{BASE_URL}/services/", json={
        "name": "Dependency Service",
        "base_path": "/api/v1/dep",
        "organization_id": org_id
    })
    service_id = res.json()["id"]

    # 3. Create Consumer
    print("Creating Consumer...")
    res = httpx.post(f"{BASE_URL}/consumers/", json={
        "name": "My Frontend App",
        "description": "Consumes APIs",
        "organization_id": org_id
    })
    if res.status_code != 200:
        print(f"Failed to create consumer: {res.text}")
        return
    consumer = res.json()
    consumer_id = consumer["id"]
    print(f"Created Consumer ID: {consumer_id}")

    # 4. Add Dependency
    print("Adding Dependency...")
    res = httpx.post(f"{BASE_URL}/consumers/{consumer_id}/dependencies/", json={
        "service_id": service_id,
        "http_method": "GET",
        "path": "/users"
    })
    if res.status_code != 200:
        print(f"Failed to add dependency: {res.text}")
        return
    dep_id = res.json()["id"]
    print("Dependency added.")

    # 5. List Dependencies
    print("Listing Dependencies...")
    res = httpx.get(f"{BASE_URL}/consumers/{consumer_id}/dependencies/")
    deps = res.json()
    if len(deps) != 1:
        print("ERROR: Expected 1 dependency")
    else:
        print("SUCCESS: 1 dependency listed")

    # 6. Remove Dependency
    print("Removing Dependency...")
    res = httpx.delete(f"{BASE_URL}/consumers/{consumer_id}/dependencies/{dep_id}")
    if not res.json()["is_deleted"]:
        print("Dependency remove failed")
    
    # 7. List again (empty)
    res = httpx.get(f"{BASE_URL}/consumers/{consumer_id}/dependencies/")
    if len(res.json()) != 0:
        print("ERROR: Dependency still visible after delete")
    
    print("SUCCESS: Dependency removed/hidden.")

    # 8. Soft Delete Consumer
    print("Soft Deleting Consumer...")
    res = httpx.patch(f"{BASE_URL}/consumers/{consumer_id}", json={"is_deleted": True})
    if not res.json()["is_deleted"]:
        print("Consumer delete failed")
    
    print("Test Complete.")

if __name__ == "__main__":
    test_consumer_crud()
