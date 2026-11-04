
import os
import hmac
import hashlib
import pytest
from unittest.mock import Mock, patch
from app.client import APIClient
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

HEADERS = {
    "X-API-Key": "my-secret-api-key"
}



def test_create_customer():

    response = client.post(
        "/customers",
        headers=HEADERS,
        json={
            "name": "John",
            "email": "john_task4_unique_582@gmail.com"
        }
    )

    assert response.status_code == 200



def test_missing_api_key():

    response = client.get("/customers")

    assert response.status_code == 401



def test_wrong_api_key():

    response = client.get(
        "/customers",
        headers={"X-API-Key": "wrong-key"}
    )

    assert response.status_code == 403



def test_customer_not_found():

    response = client.get(
        "/customers/999",
        headers=HEADERS
    )

    assert response.status_code == 404



def test_duplicate_customer():

    data = {
        "name": "John",
        "email": "duplicate@gmail.com"
    }

    client.post(
        "/customers",
        headers=HEADERS,
        json=data
    )

    response = client.post(
        "/customers",
        headers=HEADERS,
        json=data
    )

    assert response.status_code == 409



def test_invalid_customer():

    response = client.post(
        "/customers",
        headers=HEADERS,
        json={
            "name": "John",
            "email": "invalid-email"
        }
    )

    assert response.status_code == 422


def test_valid_webhook():

    payload = b'{"order_id":101}'

    secret = os.getenv(
        "WEBHOOK_SECRET",
        "my-webhook-secret"
    )

    signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/webhooks/order-events",
        content=payload,
        headers={"X-Signature": signature}
    )

    assert response.status_code == 200



def test_tampered_webhook():

    payload = b'{"order_id":101}'

    response = client.post(
        "/webhooks/order-events",
        content=payload,
        headers={"X-Signature": "wrong-signature"}
    )

    assert response.status_code == 401

def test_token_endpoint():

    response = client.post(
        "/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "my-client",
            "client_secret": "my-client-secret"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] == "sample-access-token"
    assert data["token_type"] == "bearer"

    


def test_token_refresh_on_401():

    api = APIClient(
        base_url="http://testserver",
        client_id="my-client",
        client_secret="my-client-secret"
    )

    api.token = "old-token"

    with patch("app.client.requests.get") as mock_get:
        with patch.object(api, "refresh_token") as mock_refresh:

            mock_refresh.side_effect = (
                lambda: setattr(api, "token", "new-token")
            )

            first = Mock()
            first.status_code = 401

            second = Mock()
            second.status_code = 200
            second.headers = {"X-RateLimit-Remaining": "5"}
            second.json.return_value = {
                "customers": []
            }

            mock_get.side_effect = [first, second]

            result = api.fetch_all(
                "http://testserver/customers"
            )

            assert result == []
            assert mock_refresh.call_count == 1

def test_fetch_all_pagination():

    from unittest.mock import patch, Mock
    from app.client import APIClient

    api = APIClient(
        base_url="http://testserver",
        client_id="my-client",
        client_secret="my-client-secret"
    )

    api.token = "test-token"

    with patch("app.client.requests.get") as mock_get:

        first = Mock()
        first.status_code = 200
        first.headers = {"X-RateLimit-Remaining": "5"}
        first.json.return_value = {
            "customers": [
                {"id": i} for i in range(1, 6)
            ]
        }

        second = Mock()
        second.status_code = 200
        second.headers = {"X-RateLimit-Remaining": "5"}
        second.json.return_value = {
            "customers": [
                {"id": 6}
            ]
        }

        mock_get.side_effect = [first, second]

        result = api.fetch_all(
            "http://testserver/customers"
        )

        assert len(result) == 6
        assert mock_get.call_count == 2            

def test_rate_limit_sleep():

    from unittest.mock import patch, Mock
    from app.client import APIClient

    api = APIClient(
        base_url="http://testserver",
        client_id="my-client",
        client_secret="my-client-secret"
    )

    api.token = "test-token"

    with patch("app.client.requests.get") as mock_get:
        with patch("app.client.time.sleep") as mock_sleep:

            response = Mock()
            response.status_code = 200
            response.headers = {
                "X-RateLimit-Remaining": "0"
            }
            response.json.return_value = {
                "customers": []
            }

            mock_get.return_value = response

            result = api.fetch_all(
                "http://testserver/customers"
            )

            assert result == []
            mock_sleep.assert_called_once_with(1)        