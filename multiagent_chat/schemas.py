from pydantic import BaseModel, Field


class InputSchema(BaseModel):
    prompt: str = Field(..., title="Chat question")
