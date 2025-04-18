from unittest.mock import patch


def test_create_contact(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+380991112233",
            "birthday": "1990-01-01",
        }

        response = client.post(
            "/api/v1/contacts/",
            json={**contact_data},
            headers={"Authorization": f"Bearer {get_token}"},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["first_name"] == "John"
        assert data["email"] == "john@example.com"
        assert "id" in data
        assert data["id"] == 1


def test_get_contact(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.get(
            "api/v1/contacts/1",
            headers={"Authorization": f"Bearer {get_token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == 1
        print(data)
        assert data["first_name"] == "John"


def test_get_contact_not_found(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.get(
            "/api/v1/contacts/999",
            headers={"Authorization": f"Bearer {get_token}"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Contact not found"


def test_get_contacts_list(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.get(
            "/api/v1/contacts/",
            headers={"Authorization": f"Bearer {get_token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == 1


def test_update_contact(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        update_data = {
            "first_name": "Updated",
            "last_name": "Contact",
            "email": "updated@example.com",
            "phone": "+380991119999"
        }

        response = client.put(
            "/api/v1/contacts/1",
            json=update_data,
            headers={"Authorization": f"Bearer {get_token}"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["email"] == "updated@example.com"


def test_update_contact_not_found(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.put(
            "/api/v1/contacts/999",
            json={"first_name": "Ghost"},
            headers={"Authorization": f"Bearer {get_token}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Contact not found"


def test_delete_contact(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.delete(
            f"/api/v1/contacts/1",
            headers={"Authorization": f"Bearer {get_token}"},
        )
        assert response.status_code == 204


def test_search_contacts(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.get(
            "/api/v1/contacts/search/?query=Test",
            headers={"Authorization": f"Bearer {get_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


def test_get_birthdays(client, get_token):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.get(
            "/api/v1/contacts/birthdays/?days=7",
            headers={"Authorization": f"Bearer {get_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)