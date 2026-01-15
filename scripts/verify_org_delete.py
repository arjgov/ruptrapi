import httpx
import sys
import uuid

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def test_soft_delete():
    # 1. Create
    suffix = str(uuid.uuid4())[:8]
    slug = f"delete-me-py-{suffix}"
    print(f"Creating Organization with slug: {slug}...")
    res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"Delete Me Corp {suffix}", "slug": slug})
    if res.status_code != 200:
        print(f"Failed to create: {res.text}")
        return
    org = res.json()
    org_id = org["id"]
    print(f"Created ID: {org_id}")

    # 2. Delete (Soft delete via PATCH)
    print(f"Deleting ID (PATCH): {org_id}")
    res = httpx.patch(f"{BASE_URL}/organizations/{org_id}", json={"is_deleted": True})
    if res.status_code != 200:
        print(f"Failed to delete: {res.text}")
        return
    deleted_org = res.json()
    if deleted_org["is_deleted"] is not True:
        print("ERROR: is_deleted is not True in response")
    
    # 3. List (Default - should NOT be present)
    print("Listing (Default)...")
    res = httpx.get(f"{BASE_URL}/organizations/")
    orgs = res.json()
    found = any(o["id"] == org_id for o in orgs)
    if found:
        print("ERROR: Deleted org found in default list")
    else:
        print("SUCCESS: Deleted org NOT found in default list")

    # 4. List (Include Deleted - SHOULD be present)
    print("Listing (Include Deleted)...")
    res = httpx.get(f"{BASE_URL}/organizations/?include_deleted=true")
    orgs = res.json()
    found = any(o["id"] == org_id for o in orgs)
    if found:
        print("SUCCESS: Deleted org FOUND when include_deleted=true")
    else:
        print("ERROR: Deleted org NOT found when include_deleted=true")

if __name__ == "__main__":
    try:
        test_soft_delete()
    except Exception as e:
        print(f"Exception: {e}")
