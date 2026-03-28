import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any
from datetime import datetime


class MLPipeline:
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans_model = None
        self.isolation_forest_model = None
        self.n_clusters = 3

    def prepare_expense_data(self, expenses: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(expenses)

        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"])
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["week"] = df["date"].dt.isocalendar().week

        category_mapping = {
            "food": 1,
            "groceries": 1,
            "dining": 1,
            "transport": 2,
            "travel": 2,
            "fuel": 2,
            "entertainment": 3,
            "shopping": 3,
            "leisure": 3,
            "utilities": 4,
            "bills": 4,
            "rent": 4,
            "healthcare": 5,
            "medical": 5,
            "pharmacy": 5,
            "education": 6,
            "books": 6,
            "courses": 6,
            "other": 7,
        }

        df["category_encoded"] = (
            df["category"]
            .str.lower()
            .map(
                lambda x: next(
                    (v for k, v in category_mapping.items() if k in str(x).lower()), 7
                )
            )
        )

        return df

    def detect_spending_patterns(
        self, expenses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if len(expenses) < 5:
            return {
                "patterns": [],
                "insights": ["Add more expenses to detect spending patterns."],
                "cluster_centers": [],
            }

        df = self.prepare_expense_data(expenses)

        if df.empty or len(df) < 3:
            return {
                "patterns": [],
                "insights": ["Not enough data for pattern analysis."],
                "cluster_centers": [],
            }

        features = df[["amount", "category_encoded", "day_of_week"]].values
        scaled_features = self.scaler.fit_transform(features)

        n_clusters = min(self.n_clusters, len(df) // 2 + 1)
        self.kmeans_model = KMeans(
            n_clusters=n_clusters, random_state=42, n_init="auto"
        )
        df["cluster"] = self.kmeans_model.fit_predict(scaled_features)

        cluster_centers = self.scaler.inverse_transform(
            self.kmeans_model.cluster_centers_
        )

        patterns = []
        insights = []

        for i, center in enumerate(cluster_centers):
            cluster_expenses = df[df["cluster"] == i]
            avg_amount = center[0]
            dominant_category = (
                cluster_expenses["category"].mode().iloc[0]
                if not cluster_expenses["category"].mode().empty
                else "other"
            )
            common_day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][
                int(center[2]) % 7
            ]

            pattern = {
                "cluster_id": int(i),
                "avg_amount": round(float(avg_amount), 2),
                "category": dominant_category,
                "common_day": common_day,
                "expense_count": int(len(cluster_expenses)),
            }
            patterns.append(pattern)

            insights.append(
                f"You spend around ₹{avg_amount:.0f} on {dominant_category} around {common_day}. "
                f"This pattern appears {len(cluster_expenses)} times."
            )

        weekly_spending = df.groupby("week")["amount"].sum().mean()
        insights.append(
            f"Your average weekly spending is approximately ₹{weekly_spending:.0f}."
        )

        return {
            "patterns": patterns,
            "insights": insights,
            "cluster_centers": cluster_centers.tolist(),
        }

    def detect_anomalies(self, expenses: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(expenses) < 3:
            return {"anomalies": [], "anomaly_count": 0, "severity_summary": {}}

        df = self.prepare_expense_data(expenses)

        if df.empty:
            return {"anomalies": [], "anomaly_count": 0, "severity_summary": {}}

        features = df[["amount", "category_encoded"]].values

        contamination = str(min(0.1, max(0.01, 1 / len(df))))
        self.isolation_forest_model = IsolationForest(
            contamination=contamination, random_state=42, n_estimators=100
        )

        df["anomaly"] = self.isolation_forest_model.fit_predict(features)
        df["anomaly_score"] = self.isolation_forest_model.decision_function(features)

        anomalies = df[df["anomaly"] == -1]

        anomaly_list = []
        severity_counts = {"low": 0, "medium": 0, "high": 0}

        for _, row in anomalies.iterrows():
            score = row["anomaly_score"]
            severity = "high" if score < -0.5 else "medium" if score < -0.2 else "low"
            severity_counts[severity] += 1

            reason = self._get_anomaly_reason(row, df)

            anomaly_list.append(
                {
                    "expense_id": str(row.get("id", "unknown")),
                    "amount": float(row["amount"]),
                    "category": row["category"],
                    "date": row["date"].isoformat() if pd.notna(row["date"]) else None,
                    "severity": severity,
                    "reason": reason,
                    "score": float(score),
                }
            )

        return {
            "anomalies": anomaly_list,
            "anomaly_count": len(anomaly_list),
            "severity_summary": severity_counts,
        }

    def _get_anomaly_reason(self, row: pd.Series, df: pd.DataFrame) -> str:
        amount = row["amount"]
        category = row["category"]

        category_stats = df[df["category"] == category]["amount"]
        if len(category_stats) > 0:
            cat_mean = category_stats.mean()
            cat_std = category_stats.std()

            if cat_std > 0 and amount > cat_mean + 2 * cat_std:
                return f"Unusual spike: ₹{amount:.0f} is significantly higher than your typical {category} spending (avg: ₹{cat_mean:.0f})"

        overall_mean = df["amount"].mean()
        if amount > overall_mean * 3:
            return f"Major outlier: ₹{amount:.0f} is more than 3x your average expense"

        return f"Unusual spending detected in {category}"

    def generate_recommendations(
        self, expenses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        patterns = self.detect_spending_patterns(expenses)
        anomalies = self.detect_anomalies(expenses)

        recommendations = []

        if anomalies["anomaly_count"] > 0:
            high_severity = anomalies["severity_summary"]["high"]
            if high_severity > 0:
                recommendations.append(
                    {
                        "type": "alert",
                        "priority": "high",
                        "message": f"⚠️ You have {high_severity} high-severity spending anomaly(ies). Review your recent expenses.",
                    }
                )

        df = pd.DataFrame(expenses) if expenses else pd.DataFrame()
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])

            last_7_days = df[df["date"] >= (datetime.now() - pd.Timedelta(days=7))]
            last_30_days = df[df["date"] >= (datetime.now() - pd.Timedelta(days=30))]

            if len(last_7_days) > 0:
                weekly_total = last_7_days["amount"].sum()
                recommendations.append(
                    {
                        "type": "info",
                        "priority": "medium",
                        "message": f"This week's total spending: ₹{weekly_total:.0f}",
                    }
                )

            if len(last_30_days) > 0:
                monthly_total = last_30_days["amount"].sum()
                monthly_avg = monthly_total / 4
                recommendations.append(
                    {
                        "type": "tip",
                        "priority": "low",
                        "message": f"Consider setting a weekly budget of ₹{monthly_avg:.0f} to manage monthly expenses of ₹{monthly_total:.0f}",
                    }
                )

        for pattern in patterns["patterns"][:2]:
            if pattern["expense_count"] >= 3:
                recommendations.append(
                    {
                        "type": "tip",
                        "priority": "low",
                        "message": f"Regular {pattern['category']} spending on {pattern['common_day']}s? Consider if this is a necessary recurring expense.",
                    }
                )

        return {
            "recommendations": recommendations,
            "patterns": patterns,
            "anomalies": anomalies,
            "summary": {
                "total_patterns": len(patterns["patterns"]),
                "total_anomalies": anomalies["anomaly_count"],
                "recommendation_count": len(recommendations),
            },
        }


ml_pipeline = MLPipeline()
