import logging
import os
import traceback
from typing import List

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.drift_detect import detect_drift
from app.models import CustomerFeatures, HealthResponse, PredictionResponse
from app.utils import build_feature_array

try:
    from opencensus.ext.azure.log_exporter import AzureLogHandler
except ImportError:  # Optional dependency
    AzureLogHandler = None


# ============================================================
# LOGGING & APPLICATION INSIGHTS
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bank-churn-api")

APPINSIGHTS_CONN = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if APPINSIGHTS_CONN and AzureLogHandler:
    handler = AzureLogHandler(connection_string=APPINSIGHTS_CONN)
    logger.addHandler(handler)
    logger.info(
        "app_startup",
        extra={
            "custom_dimensions": {
                "event_type": "startup",
                "status": "application_insights_connected",
            }
        },
    )
else:
    logger.warning(
        "app_startup",
        extra={
            "custom_dimensions": {
                "event_type": "startup",
                "status": "application_insights_not_configured",
            }
        },
    )


# ============================================================
# FASTAPI INIT
# ============================================================
app = FastAPI(
    title="Bank Churn Prediction API",
    description="API for churn prediction and monitoring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.getenv("MODEL_PATH", "model/churn_model.pkl")
model = None


@app.on_event("startup")
async def load_model() -> None:
    global model
    try:
        model = joblib.load(MODEL_PATH)
        logger.info(
            "model_loaded",
            extra={
                "custom_dimensions": {
                    "event_type": "model_load",
                    "model_path": MODEL_PATH,
                    "status": "success",
                }
            },
        )
    except Exception as exc:
        logger.error(
            "model_load_failed",
            extra={
                "custom_dimensions": {
                    "event_type": "model_load",
                    "error": str(exc),
                }
            },
        )
        model = None


# ============================================================
# GENERAL ENDPOINTS
# ============================================================
@app.get("/", tags=["General"])
def root() -> dict:
    return {
        "message": "Bank Churn Prediction API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return HealthResponse(status="healthy", model_loaded=True)


# ============================================================
# PREDICTION ENDPOINTS
# ============================================================
@app.post("/predict", response_model=PredictionResponse)
def predict(features: CustomerFeatures) -> PredictionResponse:
    if model is None:
        raise HTTPException(status_code=503, detail="Model unavailable")

    try:
        input_data = build_feature_array(features)

        proba = float(model.predict_proba(input_data)[0][1])
        prediction = int(proba > 0.5)

        risk = "Low" if proba < 0.3 else "Medium" if proba < 0.7 else "High"

        logger.info(
            "prediction",
            extra={
                "custom_dimensions": {
                    "event_type": "prediction",
                    "endpoint": "/predict",
                    "probability": proba,
                    "prediction": prediction,
                    "risk_level": risk,
                }
            },
        )

        return PredictionResponse(
            churn_probability=round(proba, 4),
            prediction=prediction,
            risk_level=risk,
        )

    except Exception as exc:
        logger.error(
            "prediction_error",
            extra={
                "custom_dimensions": {
                    "event_type": "prediction_error",
                    "error": str(exc),
                }
            },
        )
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/predict/batch")
def predict_batch(features_list: List[CustomerFeatures]) -> dict:
    if model is None:
        raise HTTPException(status_code=503, detail="Model unavailable")

    try:
        predictions = []

        for features in features_list:
            input_data = build_feature_array(features)

            proba = float(model.predict_proba(input_data)[0][1])
            prediction = int(proba > 0.5)

            predictions.append(
                {
                    "churn_probability": round(proba, 4),
                    "prediction": prediction,
                }
            )

        logger.info(
            "batch_prediction",
            extra={
                "custom_dimensions": {
                    "event_type": "batch_prediction",
                    "count": len(predictions),
                }
            },
        )

        return {
            "predictions": predictions,
            "count": len(predictions),
        }

    except Exception as exc:
        logger.error(
            "batch_prediction_error",
            extra={
                "custom_dimensions": {
                    "event_type": "batch_prediction_error",
                    "error": str(exc),
                }
            },
        )
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================
# DRIFT LOGGING TO APPLICATION INSIGHTS
# ============================================================

def log_drift_to_insights(drift_results: dict) -> None:
    total = len(drift_results)
    drifted = sum(1 for result in drift_results.values() if result.get("drift_detected"))
    percentage = round((drifted / total) * 100, 2) if total else 0

    risk = "LOW" if percentage < 20 else "MEDIUM" if percentage < 50 else "HIGH"

    logger.warning(
        "drift_detection",
        extra={
            "custom_dimensions": {
                "event_type": "drift_detection",
                "drift_percentage": percentage,
                "risk_level": risk,
            }
        },
    )

    for feature, details in drift_results.items():
        if details.get("drift_detected"):
            logger.warning(
                "feature_drift",
                extra={
                    "custom_dimensions": {
                        "event_type": "feature_drift",
                        "feature_name": feature,
                        "p_value": float(details.get("p_value", 0)),
                        "statistic": float(details.get("statistic", 0)),
                        "type": details.get("type", "unknown"),
                    }
                },
            )


# ============================================================
# DRIFT ENDPOINTS
# ============================================================
@app.post("/drift/check")
def check_drift(threshold: float = 0.05) -> dict:
    try:
        results = detect_drift(
            reference_file="data/bank_churn.csv",
            production_file="data/production_data.csv",
            threshold=threshold,
        )

        log_drift_to_insights(results)

        return {
            "status": "success",
            "features_analyzed": len(results),
            "features_drifted": sum(
                1 for result in results.values() if result["drift_detected"]
            ),
        }

    except Exception:
        tb = traceback.format_exc()
        logger.error(
            "drift_error",
            extra={
                "custom_dimensions": {
                    "event_type": "drift_error",
                    "traceback": tb,
                }
            },
        )
        raise HTTPException(status_code=500, detail="Drift check failed")


@app.post("/drift/alert")
def manual_drift_alert(
    message: str = "Manual drift alert triggered",
    severity: str = "warning",
) -> dict:
    logger.warning(
        "manual_drift_alert",
        extra={
            "custom_dimensions": {
                "event_type": "manual_drift_alert",
                "alert_message": message,
                "severity": severity,
                "triggered_by": "api_endpoint",
            }
        },
    )

    return {"status": "alert_sent"}
