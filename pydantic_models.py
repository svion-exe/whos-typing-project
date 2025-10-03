from pydantic import BaseModel
from typing import List

class KeystrokeEvent(BaseModel):
    """Represents a single key press or release event from the browser."""
    key: str
    event: str
    timestamp: float

class LivePredictionRequest(BaseModel):
    """The structure for a request to the live prediction endpoint."""
    events: List[KeystrokeEvent]
    target_word: str

class DataSubmissionRequest(BaseModel):
    """The structure for a request to submit new training data."""
    style_id: str
    events: List[KeystrokeEvent]
    target_word: str

