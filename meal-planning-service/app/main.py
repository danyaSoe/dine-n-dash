from fastapi import FastAPI, HTTPException

from app.clients.errors import DependencyRequestError
from app.schemas import RecommendationRequest, RecommendationsResponse
from app.services.planner import create_recommendations

app = FastAPI(title="Meal Planning Service")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "meal-planning-service"}


@app.post("/recommendations", response_model=RecommendationsResponse)
def recommend(
    request: RecommendationRequest,
) -> RecommendationsResponse:
    try:
        return create_recommendations(request)
    except DependencyRequestError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
