
import requests
import time


class APIClient:

    def __init__(self, base_url, client_id, client_secret):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def refresh_token(self):

        response = requests.post(
            f"{self.base_url}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )

        response.raise_for_status()

        self.token = response.json()["access_token"]

    def fetch_all(self, url):

        results = []
        offset = 0
        limit = 5

        if not self.token:
            self.refresh_token()

        while True:

            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            response = requests.get(
                url,
                params={
                    "offset": offset,
                    "limit": limit
                },
                headers=headers
            )

            if response.status_code == 401:
                self.refresh_token()
                continue

            response.raise_for_status()

            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )

            if remaining == "0":
                time.sleep(1)

            data = response.json()
            customers = data["customers"]

            results.extend(customers)

            if len(customers) < limit:
                break

            offset += limit

        return results
