from pydantic import BaseModel

class MintRequest(BaseModel):
    route: str
    creditsEarned: int
    co2Reduced: float
    fuelSaved: float
    greenBoost: float = 0.0
