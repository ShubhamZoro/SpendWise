from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
import os
from dotenv import load_dotenv

from ml_pipeline import ml_pipeline
from ocr_service import ocr_service

load_dotenv()

app = FastAPI(
    title="Family Expense Tracker AI Service",
    description="AI-powered expense tracking with ML insights and OCR receipt scanning",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Expense(BaseModel):
    id: Optional[str] = None
    user_id: str
    group_id: str
    amount: float
    category: str
    date: date
    notes: Optional[str] = None
    receipt_url: Optional[str] = None


class OCRRequest(BaseModel):
    image_base64: str


class AnalyticsRequest(BaseModel):
    expenses: List[Expense]
    group_id: Optional[str] = None


@app.get("/")
async def root():
    return {
        "service": "Family Expense Tracker AI Service",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "/health": "Health check",
            "/recommendations": "POST - Get AI-powered recommendations",
            "/analytics": "POST - Get expense analytics",
            "/anomalies": "POST - Detect spending anomalies",
            "/patterns": "POST - Detect spending patterns",
            "/ocr": "POST - Parse receipt image",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/recommendations")
async def get_recommendations(request: AnalyticsRequest):
    try:
        expenses_data = [e.model_dump() for e in request.expenses]
        result = ml_pipeline.generate_recommendations(expenses_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analytics")
async def get_analytics(request: AnalyticsRequest):
    try:
        expenses_data = [e.model_dump() for e in request.expenses]

        if not expenses_data:
            return {
                "total_amount": 0,
                "avg_amount": 0,
                "expense_count": 0,
                "category_breakdown": {},
                "monthly_trend": [],
            }

        df = ml_pipeline.prepare_expense_data(expenses_data)

        total_amount = float(df["amount"].sum())
        avg_amount = float(df["amount"].mean())
        expense_count = len(df)

        category_breakdown = (
            df.groupby("category")["amount"].agg(["sum", "count"]).to_dict("index")
        )
        category_breakdown = {
            cat: {"total": float(data["sum"]), "count": int(data["count"])}
            for cat, data in category_breakdown.items()
        }

        monthly_trend = (
            df.groupby(df["date"].dt.to_period("M"))["amount"].sum().reset_index()
        )
        monthly_trend = [
            {"month": str(row["date"]), "amount": float(row["amount"])}
            for _, row in monthly_trend.iterrows()
        ]

        return {
            "total_amount": total_amount,
            "avg_amount": round(avg_amount, 2),
            "expense_count": expense_count,
            "category_breakdown": category_breakdown,
            "monthly_trend": monthly_trend,
            "group_id": request.group_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/anomalies")
async def detect_anomalies(request: AnalyticsRequest):
    try:
        expenses_data = [e.model_dump() for e in request.expenses]
        result = ml_pipeline.detect_anomalies(expenses_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patterns")
async def detect_patterns(request: AnalyticsRequest):
    try:
        expenses_data = [e.model_dump() for e in request.expenses]
        result = ml_pipeline.detect_spending_patterns(expenses_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr")
async def parse_receipt(request: OCRRequest):
    try:
        if not request.image_base64:
            raise HTTPException(status_code=400, detail="Image data is required")

        result = ocr_service.extract_receipt_data(request.image_base64)

        if "error" in result and result.get("confidence", 1) == 0:
            raise HTTPException(status_code=400, detail=result["error"])

        validated_result = ocr_service.validate_extracted_data(result)

        return validated_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
