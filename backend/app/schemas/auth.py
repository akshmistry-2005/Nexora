from typing import Literal

from pydantic import BaseModel, Field

# The 5 allow-listed public demonstration roles
DemoRoleType = Literal[
    "executive",
    "department_manager",
    "data_analyst",
    "data_scientist",
    "general_viewer",
]


class OwnerLoginRequest(BaseModel):
    """Credentials required for private owner authentication."""

    email: str = Field(..., description="Owner corporate email address")
    password: str = Field(..., min_length=6, description="Owner password")


class DemoLoginRequest(BaseModel):
    """Role selection for controlled read-only demo access."""

    role: str = Field(
        ...,
        description=(
            "Target demonstration role. Allowed: executive, department_manager, "
            "data_analyst, data_scientist, general_viewer."
        ),
    )


class TokenResponse(BaseModel):
    """Authentication token payload returned upon successful login."""

    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    user_id: int
    email: str
    full_name: str
    role: str
    permissions: list[str]


class AuthMeResponse(BaseModel):
    """User profile and active permissions for the current session."""

    user_id: int
    email: str
    full_name: str
    is_owner: bool
    role: str
    permissions: list[str]
