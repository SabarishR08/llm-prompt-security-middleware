# backend/services/google_safebrowsing_service.py

import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()
SAFE_BROWSING_API_KEY = os.getenv("SAFE_BROWSING_API_KEY")

SAFE_BROWSING_URL = (
    f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={SAFE_BROWSING_API_KEY}"
)

# Threat types we want:
THREAT_TYPES = [
    "MALWARE",
    "SOCIAL_ENGINEERING",
    "UNWANTED_SOFTWARE",
    "POTENTIALLY_HARMFUL_APPLICATION",
    "THREAT_TYPE_UNSPECIFIED"
]

PLATFORM_TYPES = ["ANY_PLATFORM"]
THREAT_ENTRY_TYPES = ["URL"]


async def check_url_safebrowsing(url: str):
    """Check a single URL in Google Safe Browsing."""
    
    # Safety check: API key must exist
    if not SAFE_BROWSING_API_KEY:
        return {"url": url, "status": "Unknown (No API Key)"}

    payload = {
        "client": {"clientId": "email-phishing-detector", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": THREAT_TYPES,
            "platformTypes": PLATFORM_TYPES,
            "threatEntryTypes": THREAT_ENTRY_TYPES,
            "threatEntries": [{"url": url}],
        },
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(SAFE_BROWSING_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            # No threat detected
            if "matches" not in data:
                return {"url": url, "status": "Safe"}

            # Threat found
            threat = data["matches"][0]["threatType"]
            return {"url": url, "status": threat}

        except Exception as e:
            return {"url": url, "status": f"Error: {str(e)}"}


async def check_urls_safebrowsing_async(urls: list[str]):
    """Check multiple URLs concurrently."""
    tasks = [check_url_safebrowsing(url) for url in urls]
    return await asyncio.gather(*tasks)
