from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

# MLflow configuration
mlflow.set_tracking_uri("./mlruns")
mlflow.set_experiment("bank-churn-prediction")

DATA_PATH = Path("data") / "bank_churn.csv"
MODEL_DIR = Path("model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_PATH.exists():
    raise SystemExit("Missing data file. Run: python generate_data.py")

print("Loading data...")
df = pd.read_csv(DATA_PATH)

print(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
print(f"Churn rate: {df['Exited'].mean():.2%}")

# Separate features/target
X = df.drop("Exited", axis=1)
y = df["Exited"]

# Split train/test (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTrain: {len(X_train)} rows")
print(f"Test: {len(X_test)} rows")

print("\nTraining model...")
with mlflow.start_run(run_name="random-forest-v1"):
    params = {
        "n_estimators": 100,
        "max_depth": 10,
        "min_samples_split": 5,
        "random_state": 42,
    }

    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    mlflow.log_params(params)
    mlflow.log_metrics(
        {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "roc_auc": auc,
        }
    )

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title("Confusion Matrix")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.savefig("confusion_matrix.png")
    mlflow.log_artifact("confusion_matrix.png")
    plt.close()

    # Feature importance
    feature_importance = (
        pd.DataFrame(
            {"feature": X.columns, "importance": model.feature_importances_}
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    plt.figure(figsize=(10, 6))
    plt.barh(feature_importance["feature"], feature_importance["importance"])
    plt.xlabel("Importance")
    plt.title("Feature Importance")
    plt.tight_layout()
    plt.savefig("feature_importance.png")
    mlflow.log_artifact("feature_importance.png")
    plt.close()

    # Log model to MLflow
    try:
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="bank-churn-classifier",
        )
    except Exception:
        mlflow.sklearn.log_model(model, "model")

    # Save local model
    model_path = MODEL_DIR / "churn_model.pkl"
    joblib.dump(model, model_path)

    mlflow.set_tags(
        {
            "environment": "development",
            "model_type": "RandomForest",
            "task": "binary_classification",
        }
    )

    print("\n" + "=" * 50)
    print("TRAINING RESULTS")
    print("=" * 50)
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")
    print(f"ROC AUC   : {auc:.4f}")
    print("=" * 50)

    print(f"\nModel saved at: {model_path}")
    print("MLflow UI: mlflow ui --port 5000")
