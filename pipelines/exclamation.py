from pydantic import BaseModel
from typing import List, Optional

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
    def __init__(self):
        self.type = "filter"
        self.valves = self.Valves()
    async def outlet(self, body, user: Optional[dict] = None):
        body["messages"][-1]["content"] += "!!!"
        return body