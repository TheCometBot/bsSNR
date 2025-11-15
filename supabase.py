import os
import aiohttp
from typing import Optional, Dict, Any

BASE_URL = os.getenv("SUPABASE_URL")
API_KEY  = os.getenv("SUPABASE_KEY")
TABLE    = "User"


class Supabase:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def create_user(self, user: dict) -> Dict[str, Any]:
        async with self.session.post(
            f"{BASE_URL}/{TABLE}",
            headers={
                "apikey": API_KEY,
                "Content-Type": "application/json"
            },
            json=user
        ) as r:
            return await r.json()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        params = {"id": f"eq.{user_id}"}

        async with self.session.get(
            f"{BASE_URL}/{TABLE}",
            headers={
                "apikey": API_KEY,
                "Accept": "application/json"
            },
            params=params
        ) as r:
            data = await r.json()
            return data[0] if data else None

    async def save_user(self, user_id: int, user: dict) -> Dict[str, Any]:
        params = {"id": f"eq.{user_id}"}

        async with self.session.patch(
            f"{BASE_URL}/{TABLE}",
            headers={
                "apikey": API_KEY,
                "Content-Type": "application/json"
            },
            params=params,
            json=user
        ) as r:
            return await r.json()