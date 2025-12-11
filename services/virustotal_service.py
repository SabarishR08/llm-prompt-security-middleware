import os
import json
import asyncio
import httpx

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
CACHE_FILE = r"cache/url_cache.json"

# Load or initialize cache
url_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r") as f:
            url_cache = json.load(f)
    except Exception:
        url_cache = {}

def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(url_cache, f)
    except Exception as e:
        print(f"[VirusTotal] Failed to save cache: {e}")


async def fetch_vt_status(client, url):
    """Fetch the final VirusTotal analysis status for a URL."""
    if url in url_cache and url_cache[url] not in ["Error", "VT_API_MISSING", "Pending"]:
        return url, url_cache[url]

    if not VIRUSTOTAL_API_KEY:
        url_cache[url] = "VT_API_MISSING"
        return url, "VT_API_MISSING"

    try:
        # Step 1: Submit URL for analysis
        resp = await client.post(
            "https://www.virustotal.com/api/v3/urls",
            headers={"x-apikey": VIRUSTOTAL_API_KEY, "Accept": "application/json"},
            data={"url": url},
            timeout=30
        )
        resp.raise_for_status()
        analysis_id = resp.json()["data"]["id"]

        # Step 2: Poll for final analysis result
        final_status = "Pending"
        for _ in range(10):  # poll up to 10 times (~20s)
            analysis_resp = await client.get(
                f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                headers={"x-apikey": VIRUSTOTAL_API_KEY, "Accept": "application/json"},
                timeout=30
            )
            analysis_resp.raise_for_status()
            data = analysis_resp.json()["data"]["attributes"]

            stats = data.get("results", {}).get("stats", None)
            if stats:
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                if malicious > 0:
                    final_status = "Malicious"
                elif suspicious > 0:
                    final_status = "Suspicious"
                else:
                    final_status = "Safe"
                break  # got final verdict
            await asyncio.sleep(2)  # wait before polling again

        url_cache[url] = final_status
        save_cache()
        return url, final_status

    except Exception as e:
        url_cache[url] = "Error"
        save_cache()
        print(f"[VirusTotal] Error for {url}: {e}")
        return url, "Error"


async def check_urls_async(urls):
    valid_urls = [u for u in urls if u.startswith(('http://', 'https://'))]
    if not valid_urls:
        return {}
    async with httpx.AsyncClient() as client:
        tasks = [fetch_vt_status(client, url) for url in valid_urls]
        results = await asyncio.gather(*tasks)
    return dict(results)


def check_url_virustotal(url: str):
    """Synchronous wrapper for a single URL."""
    try:
        return asyncio.run(check_urls_async([url]))[url]
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(check_urls_async([url]))[url]
