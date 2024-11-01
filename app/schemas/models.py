from typing import Dict

class SessionUpdateMessage(Dict):
    type: str
    session: Dict

class Message(Dict):
    type: str
    data: str