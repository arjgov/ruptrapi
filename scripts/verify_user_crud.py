import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def test_user_crud():
    # 1. Create Org
    suffix = str(uuid.uuid4())[:8]
    org_slug = f"user-test-org-{suffix}"
    print(f"Creating Org: {org_slug}")
    res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"User Test Org {suffix}", "slug": org_slug})
    if res.status_code != 200:
        print(f"Failed to create org: {res.text}")
        return
    org_id = res.json()["id"]

    # 2. Create User
    email = f"test-{suffix}@example.com"
    print(f"Creating User: {email}")
    res = httpx.post(f"{BASE_URL}/users/", json={
        "email": email,
        "name": "Test User",
        "organization_id": org_id,
        "role": "ADMIN"
    })
    if res.status_code != 200:
        print(f"Failed to create user: {res.text}")
        return
    user = res.json()
    user_id = user["id"]
    print(f"Created User ID: {user_id}")

    # 3. Get User by ID
    print("Getting User by ID...")
    res = httpx.get(f"{BASE_URL}/users/{user_id}")
    if res.status_code != 200:
        print(f"Failed to get user by ID: {res.text}")
    
    # 4. Get User by Email
    print("Getting User by Email...")
    res = httpx.get(f"{BASE_URL}/users/by-email/{email}")
    if res.status_code != 200:
        print(f"Failed to get user by email: {res.text}")

    # 5. Update User (Generic)
    print("Updating User name...")
    res = httpx.patch(f"{BASE_URL}/users/{user_id}", json={"name": "Updated Name"})
    if res.json()["name"] != "Updated Name":
        print("Update failed")
    
    # 6. Soft Delete
    print("Soft Deleting User...")
    res = httpx.patch(f"{BASE_URL}/users/{user_id}", json={"is_deleted": True})
    if not res.json()["is_deleted"]:
        print("Soft delete failed")

    # 7. List (ensure excluded)
    print("Listing users...")
    res = httpx.get(f"{BASE_URL}/users/?organization_id={org_id}")
    users = res.json()
    if any(u["id"] == user_id for u in users):
        print("ERROR: Soft deleted user found in list")
    else:
        print("SUCCESS: User correctly excluded from list")

if __name__ == "__main__":
    try:
        test_user_crud()
    except Exception as e:
        print(f"Exception: {e}")
