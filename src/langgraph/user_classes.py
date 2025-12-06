from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid
import httpx
import os
import json

class Profile(BaseModel):
    """Value Object representing raw profile data."""
    username: Optional[str] = None #needed for account creation
    full_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    education: Optional[List[str]] = Field(default_factory=list)
    profile_url: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    phone_number: Optional[str] = None

class LinkedInPiloterrAdapter():
    def __init__(self):
        self.base_url = "https://series.so/api/internal/piloterr-linkedin" # Using the URL provided by user

    async def get_profile(self, username: str) -> Profile | None:
        # For the hackathon/demo, if no API key is present or for specific users, we might want to mock or use the provided URL directly.
        # The user provided a specific URL: https://series.so/api/internal/piloterr-linkedin?query=itsandres

        async with httpx.AsyncClient() as client:
            try:
                # In a real scenario, we'd use the API key.
                # Here we follow the user's specific instruction to use the series.so internal API.
                response = await client.get(f"{self.base_url}?query={username}", timeout=30.0)
                response.raise_for_status()
                if "error" in response.json():
                    raise Exception()

                data = response.json()

                # Map response to Profile entity
                # The user provided JSON structure shows the data is inside "profile" key
                profile_data = data.get("profile", {})
                print(f"DEBUG: Profile Keys: {profile_data.keys()}")

                # Extract education (API uses 'educations' plural)
                education_list = []
                # Try both 'education' and 'educations' just in case
                raw_educations = profile_data.get("educations") or profile_data.get("education") or []

                for edu in raw_educations:
                    if isinstance(edu, dict):
                        school = edu.get("school") or edu.get("name")
                        if school:
                            education_list.append(school)
                    elif isinstance(edu, str):
                        education_list.append(edu)

                print(f"DEBUG: Extracted Education: {education_list}")

                return Profile(
                    username=profile_data.get("username") or username,
                    full_name=profile_data.get("full_name"),
                    headline=profile_data.get("headline"),
                    summary=profile_data.get("summary"),
                    location=profile_data.get("location"),
                    education=education_list,
                    profile_url=profile_data.get("profile_url"),
                    raw_data=data
                )
            except Exception as e:
                print(f"Error fetching profile: {e}")
                # Fallback/Mock for testing if API fails
                return None
