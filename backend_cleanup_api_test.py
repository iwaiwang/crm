import json
import os
import sys
import httpx


BASE_URL = os.getenv("CRM_TEST_API_BASE_URL", "http://127.0.0.1:8003/api")


def main():
    with httpx.Client(timeout=30.0, trust_env=False) as client:
        login = client.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        login.raise_for_status()
        token = login.json()["access_token"]

        response = client.post(
            f"{BASE_URL}/settings/cleanup-files",
            headers={"Authorization": f"Bearer {token}"},
        )

        result = {
            "status_code": response.status_code,
            "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if response.status_code >= 400:
            sys.exit(1)


if __name__ == "__main__":
    main()
