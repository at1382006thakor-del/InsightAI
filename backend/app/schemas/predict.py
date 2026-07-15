from pydantic import BaseModel
from typing import List, Optional

class TrainRequest(BaseModel):
    model_type: str = "xgboost"  # "linear", "random_forest", "xgboost"

class TrainResponse(BaseModel):
    success: bool
    message: str
    mape: float
    r2_score: float
    model_type: str

class PredictRequest(BaseModel):
    months_ahead: int = 6
    model_type: str = "xgboost"
    region: Optional[str] = None
    category: Optional[str] = None

class PredictionDataPoint(BaseModel):
    month: str  # "YYYY-MM"
    predicted_sales: float
    confidence_lower: float
    confidence_upper: float

class PredictResponse(BaseModel):
    model_used: str
    predictions: List[PredictionDataPoint]
