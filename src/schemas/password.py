from pydantic import BaseModel


class ResetPasswordRequest(BaseModel):
    new_password: str
