from pydantic import BaseModel


class AISummarySettingUpdate(BaseModel):
    enabled: bool


class AISummarySettingResponse(BaseModel):
    enabled: bool
