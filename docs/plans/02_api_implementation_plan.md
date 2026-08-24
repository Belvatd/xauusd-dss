## Goal Description
The objective is to operationalize the trained LightGBM Decision Support System (DSS) model by wrapping it in a REST API using **FastAPI**. 
This API will allow external applications (like a web dashboard or trading bot) to send real-time market conditions (JSON) and receive instant probabilistic predictions and DSS recommendations (Sweep / Breakout / Abstain) based on the model's intelligence.

Since this API project will be implemented in a separate folder (potentially by another Antigravity session), this plan acts as the definitive blueprint.

## User Review Required
> [!IMPORTANT]
> **API Folder Location:** We need to agree on where this API project will live. I propose creating a new folder: `api_service/` inside your main research repository. Is this acceptable?

> [!WARNING]
> **Model File Transfer:** Before the API can be built, the `.pkl` model file must be exported from Databricks and downloaded into the `api_service/` folder. The API cannot run without the "brain". 

## Proposed Changes

---

### Component 1: Databricks Model Export
Before building the API, the existing Databricks notebook must export the trained model.

#### [MODIFY] `databricks_pipelines/04_machine_learning_dss.ipynb`
At the very end of the notebook, we will add a cell to export the `calibrated_lgb` object using `joblib`.
```python
import joblib
# Simpan model beserta pipeline kalibrasinya
joblib.dump(calibrated_lgb, 'xauusd_dss_model.pkl')
print("Model diekspor ke xauusd_dss_model.pkl")
```
*(Tindakan Manual: Pengguna harus mengunduh file `xauusd_dss_model.pkl` ini dari Databricks dan meletakkannya di folder `api_service/models/` di laptop lokal).*

---

### Component 2: FastAPI Backend Project
This is the core API server that will be built in the new session.

#### [NEW] `api_service/requirements.txt`
Dependencies needed to run the API:
```text
fastapi
uvicorn
pydantic
pandas
scikit-learn
lightgbm
joblib
```

#### [NEW] `api_service/schemas.py`
Pydantic models to strictly validate incoming JSON requests, ensuring the API doesn't crash if bad data is sent.
```python
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    session: str = Field(..., description="Sesi market: ASIA, LONDON, NY, OFF_SESSION")
    day_of_week: int = Field(..., ge=0, le=4, description="0=Senin, 4=Jumat")
    level_type: str = Field(..., description="PDH, PDL, PWH, PWL")
    is_weekend_cross: int = Field(..., ge=0, le=1)
    hour_of_day: int = Field(..., ge=0, le=23)
    crossover_volume: float
    breakout_depth: float
    window_hours: float

class PredictionResponse(BaseModel):
    probability_breakout: float
    probability_sweep: float
    dss_recommendation: str
    confidence_score: str
```

#### [NEW] `api_service/main.py`
The FastAPI application logic.
```python
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from schemas import PredictionRequest, PredictionResponse

app = FastAPI(title="XAUUSD DSS Prediction API", version="1.0")

# Load model saat server menyala
try:
    model = joblib.load("models/xauusd_dss_model.pkl")
except Exception as e:
    model = None
    print(f"Peringatan: Model gagal dimuat. {e}")

@app.post("/predict", response_model=PredictionResponse)
def predict_event(req: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model belum dimuat di server.")

    # Konversi JSON ke Pandas DataFrame (1 baris)
    input_data = pd.DataFrame([req.dict()])
    
    # Casting kolom kategorikal persis seperti saat training di Databricks
    cat_cols = ['session', 'day_of_week', 'level_type', 'is_weekend_cross']
    for col in cat_cols:
        input_data[col] = input_data[col].astype('category')

    # Prediksi
    prob_breakout = float(model.predict_proba(input_data)[0, 1])
    prob_sweep = 1.0 - prob_breakout

    # Logika DSS (Abstain Zone 35% - 65%)
    if prob_breakout >= 0.65:
        recommendation = "SIGNAL_BREAKOUT (Follow)"
        conf = "High"
    elif prob_breakout <= 0.35:
        recommendation = "SIGNAL_SWEEP (Fade/Reversal)"
        conf = "High"
    else:
        recommendation = "ZONA_ABSTAIN (No Trade)"
        conf = "Low / Ambiguous"

    return PredictionResponse(
        probability_breakout=round(prob_breakout, 4),
        probability_sweep=round(prob_sweep, 4),
        dss_recommendation=recommendation,
        confidence_score=conf
    )
```

## Verification Plan

### Automated Tests
*For the Antigravity Agent implementing this later:*
1. Run `pip install -r requirements.txt`.
2. Start the server using `uvicorn main:app --reload`.
3. Test the endpoint using `curl` or Python `requests`:
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/predict' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "session": "LONDON",
  "day_of_week": 2,
  "level_type": "PDH",
  "is_weekend_cross": 1,
  "hour_of_day": 14,
  "crossover_volume": 450,
  "breakout_depth": 2.5,
  "window_hours": 6.0
}'
```

### Manual Verification
- The user will open `http://127.0.0.1:8000/docs` in their browser to access the interactive Swagger UI and manually fire test predictions.
