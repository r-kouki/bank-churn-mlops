import numpy as np

from app.models import CustomerFeatures


def build_feature_array(features: CustomerFeatures) -> np.ndarray:
    return np.array(
        [
            [
                features.CreditScore,
                features.Age,
                features.Tenure,
                features.Balance,
                features.NumOfProducts,
                features.HasCrCard,
                features.IsActiveMember,
                features.EstimatedSalary,
                features.Geography_Germany,
                features.Geography_Spain,
            ]
        ]
    )
