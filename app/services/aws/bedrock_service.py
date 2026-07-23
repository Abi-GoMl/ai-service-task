from __future__ import annotations
 
import json
import os
from typing import Any
 
import boto3
from botocore.exceptions import BotoCoreError, ClientError
 
from app.services.aws.prompt_templates import TICKET_SUMMARY_V1
 
from dotenv import load_dotenv
load_dotenv()
 
 
class BedrockServiceError(RuntimeError):
    pass
 
 
class BedrockService:
    """Wrapper around the Amazon Bedrock Converse API.
 
    The boto3 client is injectable, allowing deterministic unit tests without
    live network calls or model cost.
    """
 
    def __init__(
        self,
        client: Any | None = None,
    ) -> None:
        self.model_id = os.getenv("BEDROCK_MODEL_ID")
        self.client = client or boto3.client(
            "bedrock-runtime",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
 
    def summarize_ticket(self, ticket_description: str) -> dict[str, str]:
        prompt = TICKET_SUMMARY_V1.render(
            ticket_description=ticket_description,
        )
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": 350,
                    "temperature": 0.1,
                },
            )
        except (BotoCoreError, ClientError) as exc:
            raise BedrockServiceError("Bedrock request failed") from exc
 
        try:
            print(response)
            text = response["output"]["message"]["content"][0]["text"]
            text = text.strip()
            if text.startswith("```"):
                text = "\n".join(line for line in text.splitlines()[1:] if not line.strip().startswith("```"))
                text = text.strip()
            parsed = json.loads(text)
            
            print("############")
            print(text)
            print("############")
            return {
                "summary": str(parsed["summary"]),
                "suggested_response": str(parsed["suggested_response"]),
            }
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise BedrockServiceError("Bedrock returned an invalid response") from exc
 
 
class FakeBedrockService:
    """Offline deterministic implementation for classroom demonstrations."""
 
    def summarize_ticket(self, ticket_description: str) -> dict[str, str]:
        short_description = ticket_description.strip()[:70]
        return {
            "summary": f"Support issue: {short_description}",
            "suggested_response": (
                "Acknowledge the issue, confirm that it is being investigated, "
                "and provide the next expected update."
            ),
        }
 
 