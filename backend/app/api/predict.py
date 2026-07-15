from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from ..database.connection import get_db
from ..database.models import User
from ..schemas.predict import TrainRequest, TrainResponse, PredictRequest, PredictResponse
from ..services.auth_service import get_current_user, get_current_admin
from ..ml.forecaster import train_forecaster, run_predictions
from ..ml.segmentation import train_segmentation_model, predict_customer_segments
from ..ml.churn_classifier import train_churn_model, predict_customer_churn_probabilities
from ..ml.demand_predictor import train_demand_model, run_demand_forecast
from ..ml.anomaly_detector import train_anomaly_detector, detect_transaction_anomalies
from .dashboard import get_active_dataset_id

router = APIRouter(prefix="/predict", tags=["Predictive Analytics & ML Engine"])

@router.post("/train", response_model=TrainResponse)
def train_model(
    payload: TrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """Trains a specific sales forecast model on the active dataset."""
    dataset_id = get_active_dataset_id(db)
    res = train_forecaster(db, dataset_id=dataset_id, model_type=payload.model_type)
    
    if not res.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", "Model training failed.")
        )
        
    return TrainResponse(
        success=True,
        message=f"Successfully trained {payload.model_type.upper()} model.",
        mape=res["mape"],
        r2_score=res["r2_score"],
        model_type=res["model_type"]
    )

@router.post("/run", response_model=PredictResponse)
def forecast_sales(
    payload: PredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Runs sales revenue predictions with 95% confidence intervals."""
    dataset_id = get_active_dataset_id(db)
    predictions = run_predictions(
        db,
        dataset_id=dataset_id,
        months_ahead=payload.months_ahead,
        model_type=payload.model_type,
        region=payload.region,
        category=payload.category
    )
    
    if not predictions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate predictions. Check dataset dates structure."
        )
        
    return PredictResponse(
        model_used=payload.model_type,
        predictions=predictions
    )

@router.post("/train-all")
def train_all_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Triggers concurrent retraining of all company ML models (Forecaster, Segmentation, Churn, Demand, Anomalies)."""
    dataset_id = get_active_dataset_id(db)
    
    forecaster_res = train_forecaster(db, dataset_id, model_type="xgboost")
    segmentation_res = train_segmentation_model(db, dataset_id)
    churn_res = train_churn_model(db, dataset_id)
    demand_res = train_demand_model(db, dataset_id)
    anomaly_res = train_anomaly_detector(db, dataset_id)

    return {
        "success": True,
        "message": "All workspace machine learning models retrained successfully.",
        "details": {
            "sales_forecaster_xgboost": forecaster_res,
            "customer_segmentation_kmeans": segmentation_res,
            "customer_churn_random_forest": churn_res,
            "demand_predictor_random_forest": demand_res,
            "transaction_anomalies_isolation_forest": anomaly_res
        }
    }

@router.get("/segmentation")
def get_customer_segmentation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves customer segments mapped by K-Means clustering."""
    dataset_id = get_active_dataset_id(db)
    return predict_customer_segments(db, dataset_id)

@router.get("/churn")
def get_customer_churn_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves customer churn probabilities using Random Forest predictions."""
    dataset_id = get_active_dataset_id(db)
    return predict_customer_churn_probabilities(db, dataset_id)

@router.get("/anomalies")
def get_anomalies(
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detects outlier transactions using Isolation Forest model scoring."""
    dataset_id = get_active_dataset_id(db)
    return detect_transaction_anomalies(db, dataset_id, limit)

@router.get("/demand")
def get_demand_forecast(
    months_ahead: int = Query(6),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves forecasted demand quantities projections."""
    dataset_id = get_active_dataset_id(db)
    predictions = run_demand_forecast(db, dataset_id, months_ahead, category)
    return {
        "model_used": "random_forest_regressor",
        "predictions": predictions
    }
