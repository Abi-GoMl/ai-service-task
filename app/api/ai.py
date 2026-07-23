from fastapi import APIRouter, HTTPException, status
 
from app.schemas.ticket import SummarizeRequest, SummarizeResponse
from app.services.aws.bedrock_service import (
    BedrockService,
    BedrockServiceError,
)
 
router = APIRouter(prefix="/ai", tags=["AI"])
 
service = BedrockService()
 
 
@router.post("/summarize", response_model=SummarizeResponse)
def summarize_ticket(payload: SummarizeRequest):
    try:
        return service.summarize_ticket(payload.ticket_description)
    except BedrockServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service is temporarily unavailable",
        ) from exc
 