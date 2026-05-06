from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    start: str
    destination: str
    timeOfDay: str
    vehicleType: str

class OptimizeRequest(BaseModel):
    start: str
    destination: str
    vehicleType: str
