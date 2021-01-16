"""Fondat package for Amazon Web Services."""

from aiobotocore.config import AioConfig
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    region_name: Optional[str] = None
    verify: Optional[bool] = None
    endpoint_url: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
