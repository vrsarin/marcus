from pydantic import BaseModel

class RankRequest(BaseModel):
    folder_path: str
    factor: str


class RankResult(BaseModel):
    folder: str
    score: float
    reason: str