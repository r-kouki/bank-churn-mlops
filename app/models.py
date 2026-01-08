from pydantic import BaseModel, Field


class CustomerFeatures(BaseModel):
    CreditScore: int = Field(..., ge=300, le=850)
    Age: int = Field(..., ge=18, le=120)
    Tenure: int = Field(..., ge=0, le=50)
    Balance: float = Field(..., ge=0)
    NumOfProducts: int = Field(..., ge=1, le=10)
    HasCrCard: int = Field(..., ge=0, le=1)
    IsActiveMember: int = Field(..., ge=0, le=1)
    EstimatedSalary: float = Field(..., ge=0)
    Geography_Germany: int = Field(..., ge=0, le=1)
    Geography_Spain: int = Field(..., ge=0, le=1)

    model_config = {"extra": "forbid"}


class PredictionResponse(BaseModel):
    churn_probability: float
    prediction: int
    risk_level: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
