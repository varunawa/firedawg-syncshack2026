"""Pydantic schemas = the shape of JSON going in and out of the API.

Keeping these separate from ORM models lets you expose only what you want.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: int
    created_at: datetime
