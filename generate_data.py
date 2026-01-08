import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
n_samples = 10000

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

data = {
    "CreditScore": np.random.randint(300, 850, n_samples),
    "Age": np.random.randint(18, 80, n_samples),
    "Tenure": np.random.randint(0, 11, n_samples),
    "Balance": np.random.uniform(0, 200000, n_samples),
    "NumOfProducts": np.random.randint(1, 5, n_samples),
    "HasCrCard": np.random.choice([0, 1], n_samples),
    "IsActiveMember": np.random.choice([0, 1], n_samples),
    "EstimatedSalary": np.random.uniform(20000, 150000, n_samples),
    "Geography_Germany": np.random.choice([0, 1], n_samples),
    "Geography_Spain": np.random.choice([0, 1], n_samples),
}

# Target: higher churn chance if inactive, few products, etc.
churn_prob = (
    (1 - data["IsActiveMember"]) * 0.3
    + (data["NumOfProducts"] == 1) * 0.2
    + (data["Age"] > 60) * 0.15
    + (data["Balance"] == 0) * 0.25
)

churn_prob = np.clip(churn_prob, 0, 0.95)

data["Exited"] = (np.random.random(n_samples) < churn_prob).astype(int)

df = pd.DataFrame(data)
output_path = DATA_DIR / "bank_churn.csv"
df.to_csv(output_path, index=False)

print(f"Dataset created: {len(df)} rows")
print(f"Churn rate: {df['Exited'].mean():.2%}")
