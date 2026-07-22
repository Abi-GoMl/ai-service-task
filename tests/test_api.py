def test_create_ticket(client):

    response = client.post(
        "/tickets",
        json={
            "title": "Payment failed",
            "priority": "high"
        }
    )

    assert response.status_code in [200, 201]

    data = response.json()

    assert data["title"] == "Payment failed"
    assert data["priority"] == "high"
    assert data["status"] == "open"

def test_reject_empty_title(client):

    response = client.post(
        "/tickets",
        json={
            "title": "",
            "priority": "high"
        }
    )

    assert response.status_code == 422

def test_reject_blank_title(client):

    response = client.post(
        "/tickets",
        json={
            "title": "      ",
            "priority": "high"
        }
    )

    assert response.status_code == 422

def test_invalid_priority(client):

    response = client.post(
        "/tickets",
        json={
            "title": "Login Failed",
            "priority": "urgent"
        }
    )

    assert response.status_code == 422

def test_response_time_header(client):

    response = client.get("/")

    assert response.status_code == 200

    assert "X-Response-Time" in response.headers

def test_invalid_uuid(client):

    response = client.get("/tickets/abcd")

    assert response.status_code == 422


def test_long_title(client):

    long_title = "A" * 300

    response = client.post(
        "/tickets",
        json={
            "title": long_title,
            "priority": "high"
        }
    )

    assert response.status_code == 422

#missing priority
def test_missing_priority(client):

    response = client.post(
        "/tickets",
        json={
            "title": "Login Failed"
        }
    )

    assert response.status_code == 422


#missing title
def test_missing_title(client):

    response = client.post(
        "/tickets",
        json={
            "priority": "high"
        }
    )

    assert response.status_code == 422