from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.model_selection import train_test_split
import pandas as pd
import joblib
import json
import io
import logging

logger = logging.getLogger("trainer")

def train_model(dataset: pd.DataFrame, target_col: str, algorithm: str = "random_forest", task_type: str = "regression"):
    """
    Train a model on the provided dataset.
    """
    if target_col not in dataset.columns:
        raise ValueError(f"Target column {target_col} not in dataset")
        
    X = dataset.drop(columns=[target_col, "_time", "device_id", "factory_id", "result", "table"], errors="ignore")
    y = dataset[target_col]
    
    # Simple imputation
    X = X.fillna(X.mean())
    y = y.fillna(y.mean() if task_type == "regression" else y.mode()[0])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = None
    if task_type == "regression":
        if algorithm == "linear_regression":
            model = LinearRegression()
        else: # Default Random Forest
            model = RandomForestRegressor(n_estimators=100)
            
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        metric = mean_squared_error(y_test, preds)
        metrics = {"mse": metric, "rmse": metric**0.5}
        
    else: # Classification
        if algorithm == "logistic_regression":
            model = LogisticRegression()
        else:
            model = RandomForestClassifier(n_estimators=100)
            
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        metrics = {"accuracy": acc}
        
    # Serialize model
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    buffer.seek(0)
    
    return buffer.read(), metrics

def infer_model(model_bytes, dataset: pd.DataFrame):
     buffer = io.BytesIO(model_bytes)
     model = joblib.load(buffer)
     # Predict...
     # For now returning placeholder as inference logic depends heavily on feature alignment
     return []
