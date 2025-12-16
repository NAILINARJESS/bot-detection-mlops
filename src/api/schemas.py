from pydantic import BaseModel
from typing import Optional

class BotRequest(BaseModel):
    hour: int
    day_of_week: int
    action_code: int
    actions_per_session: int
    session_duration_sec: float
    time_diff_sec: float
    is_private_ip: int

    action: str
    ip_address: str
    user_agent: str
    device_type: str
    browser_family: str
    os_family: str
    bot_type: Optional[str] = "unknown"

