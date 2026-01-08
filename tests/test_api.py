import numpy as np
from fastapi.testclient import TestClient

import app.main as main


class DummyModel:
    def predict_proba(self, features):
        rows = len(features)
        return np.tile([0.3, 0.7], (rows, 1))


client = TestClient(main.app)


def test_health_ok():
    main.model = DummyModel()
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["model_loaded"] is True


def test_predict_ok():
    main.model = DummyModel()
    response = client.post(
        "/predict",
        json={
            "CreditScore": 650,
            "Age": 35,
            "Tenure": 5,
            "Balance": 50000,
            "NumOfProducts": 2,
            "HasCrCard": 1,
            "IsActiveMember": 1,
            "EstimatedSalary": 75000,
            "Geography_Germany": 0,
            "Geography_Spain": 1,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "churn_probability" in payload
    assert payload["prediction"] == 1
    assert payload["risk_level"] in {"Low", "Medium", "High"}


def test_predict_batch_ok():
    main.model = DummyModel()
    response = client.post(
        "/predict/batch",
        json=[
            {
                "CreditScore": 650,
                "Age": 35,
                "Tenure": 5,
                "Balance": 50000,
                "NumOfProducts": 2,
                "HasCrCard": 1,
                "IsActiveMember": 1,
                "EstimatedSalary": 75000,
                "Geography_Germany": 0,
                "Geography_Spain": 1,
            },
            {
                "CreditScore": 720,
                "Age": 44,
                "Tenure": 8,
                "Balance": 120000,
                "NumOfProducts": 1,
                "HasCrCard": 0,
                "IsActiveMember": 0,
                "EstimatedSalary": 82000,
                "Geography_Germany": 1,
                "Geography_Spain": 0,
            },
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert len(payload["predictions"]) == 2
