from fastapi.testclient import TestClient

import main
from services import admin as admin_service


client = TestClient(main.app)


def test_get_admin_policy_settings(monkeypatch):
    monkeypatch.setattr(admin_service, "get_admin_policies", lambda: {
        "payment": {
            "plans": {
                "free": {"credits": 5, "price": 0},
                "pro": {"credits": 50, "price": 2900},
                "studio": {"credits": 500, "price": 19800},
            }
        },
        "retention": {
            "plans": {
                "free": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                "pro": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                "studio": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
            }
        },
    })

    response = client.get("/admin/policy")

    assert response.status_code == 200
    assert response.json()["data"]["payment"]["plans"]["free"]["credits"] == 5
    assert response.json()["data"]["payment"]["plans"]["pro"]["price"] == 2900
    assert response.json()["data"]["payment"]["plans"]["studio"]["price"] == 19800
    assert response.json()["data"]["retention"]["plans"]["free"]["metadataRetentionDays"] == 90


def test_update_admin_policy_settings(monkeypatch):
    saved = []

    def fake_update(policies, *args, **kwargs):
        saved.append(policies)
        return policies

    monkeypatch.setattr(admin_service, "update_admin_policies", fake_update)

    payload = {
        "policies": {
            "payment": {
                "plans": {
                    "free": {"credits": 5, "price": 0},
                    "pro": {"credits": 50, "price": 2900},
                    "studio": {"credits": 500, "price": 19800},
                }
            },
            "retention": {
                "plans": {
                    "free": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                    "pro": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                    "studio": {"autoDeleteOriginalHours": 12, "metadataRetentionDays": 90},
                }
            },
        }
    }

    response = client.put("/admin/policy", json=payload)

    assert response.status_code == 200
    assert saved == [payload["policies"]]
    assert response.json()["data"]["payment"]["plans"]["pro"]["price"] == 2900
    assert response.json()["data"]["retention"]["plans"]["studio"]["autoDeleteOriginalHours"] == 12
