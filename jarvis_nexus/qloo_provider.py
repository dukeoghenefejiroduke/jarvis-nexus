"""Lightweight Qloo API client for JARVIS Cultural Intelligence."""

import json
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from jarvis_nexus.config import Config


ALLOWED_CATEGORIES = {
    "artist": "urn:entity:artist",
    "movie": "urn:entity:movie",
    "tv_show": "urn:entity:tv_show",
    "book": "urn:entity:book",
    "brand": "urn:entity:brand",
    "destination": "urn:entity:destination",
    "person": "urn:entity:person",
    "place": "urn:entity:place",
    "podcast": "urn:entity:podcast",
    "videogame": "urn:entity:videogame",
}


def normalize_category(cat: str) -> str:
    """Normalize category strings or aliases into valid ALLOWED_CATEGORIES keys."""
    if not cat:
        return "movie"
    c = str(cat).strip().lower()
    if c.startswith("urn:entity:"):
        c = c[len("urn:entity:"):]
    elif c.startswith("urn:"):
        c = c.split(":")[-1]
    c = c.replace("-", "_").replace(" ", "_")
    if c in ALLOWED_CATEGORIES:
        return c
    aliases = {
        "movies": "movie",
        "film": "movie",
        "films": "movie",
        "artist": "artist",
        "artists": "artist",
        "musician": "artist",
        "musicians": "artist",
        "band": "artist",
        "bands": "artist",
        "tv": "tv_show",
        "tv_shows": "tv_show",
        "tvshow": "tv_show",
        "tvshows": "tv_show",
        "shows": "tv_show",
        "show": "tv_show",
        "book": "book",
        "books": "book",
        "brand": "brand",
        "brands": "brand",
        "destination": "destination",
        "destinations": "destination",
        "person": "person",
        "persons": "person",
        "people": "person",
        "place": "place",
        "places": "place",
        "podcast": "podcast",
        "podcasts": "podcast",
        "videogame": "videogame",
        "videogames": "videogame",
        "video_game": "videogame",
        "video_games": "videogame",
        "game": "videogame",
        "games": "videogame",
    }
    return aliases.get(c, "movie")


class QlooProvider:
    """Call Qloo search and insights endpoints without exposing API credentials."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 20,
    ) -> None:
        self.api_key = api_key if api_key is not None else Config.QLOO_API_KEY
        self.base_url = (
            base_url or Config.QLOO_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key or self.api_key.strip() in (
            "your_api_key_here",
            "your_qloo_api_key_here",
        ):
            raise ValueError(
                "QLOO_API_KEY is missing. Configure it locally before making API calls."
            )

        if not self.base_url.startswith("https://"):
            raise ValueError("QLOO_BASE_URL must use HTTPS.")

        query = urlencode({
            key: value for key, value in params.items()
            if value is not None
        }, doseq=True)

        url = f"{self.base_url}{endpoint}"
        if query:
            url = f"{url}?{query}"

        request = Request(
            url,
            headers={
                "X-Api-Key": self.api_key,
                "Accept": "application/json",
                "User-Agent": "JARVIS-Cultural-Intelligence/1.0",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if not isinstance(payload, dict):
                raise ValueError("Qloo returned an unexpected response format.")

            return payload

        except HTTPError as exc:
            if exc.code == 429:
                raise RuntimeError("Qloo API rate limit exceeded. Please try again later.") from None
            if exc.code == 403:
                raise RuntimeError("Qloo API access forbidden. Check your API key and account permissions.") from None
            if exc.code == 404:
                raise RuntimeError("Qloo API endpoint or resource not found.") from None
            # Do not include the request URL, headers, or response body.
            raise RuntimeError(
                f"Qloo API returned HTTP {exc.code}. Check the endpoint, "
                "parameters, API key, and account access."
            ) from None
        except URLError:
            raise RuntimeError(
                "Could not reach Qloo. Check your internet connection and try again."
            ) from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise RuntimeError("Qloo returned invalid JSON.") from None

    def search(self, query: str, **params: Any) -> Dict[str, Any]:
        """Search Qloo for entities matching a text query."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty.")

        return self._get("/v2/search", {"query": query.strip(), **params})

    def insights(self, **params: Any) -> Dict[str, Any]:
        """Request recommendations using documented Qloo insight parameters."""
        if not params:
            raise ValueError(
                "Insights require valid Qloo API parameters."
            )

        return self._get("/v2/insights", params)

    def trending(self, category: str = "movie", **params: Any) -> Dict[str, Any]:
        """Request trending entities for a category using Qloo insights or search fallback."""
        norm_cat = normalize_category(category)
        type_urn = ALLOWED_CATEGORIES.get(norm_cat, ALLOWED_CATEGORIES.get(category, f"urn:entity:{category}"))

        try:
            p = {
                "filter.type": type_urn,
                "bias.trends": "high",
                **params,
            }
            return self.insights(**p)
        except Exception:
            take = params.get("take", 12)
            try:
                res = self.search(category, types=type_urn, take=take)
                if res and (res.get("results") or res.get("entities") or res.get("items") or isinstance(res, list)):
                    return res
            except Exception:
                pass

            try:
                res = self.search("popular", types=type_urn, take=take)
                return res
            except Exception:
                raise RuntimeError("Qloo trending currently unavailable.")

    def audience(self, seed_entity_id: str, target_type: str = "movie", **params: Any) -> Dict[str, Any]:
        """Request audience-related affinity insights."""
        p = {
            "filter.type": f"urn:entity:{target_type}",
            "signal.interests.entities": seed_entity_id,
            **params,
        }
        return self.insights(**p)

    def geographic(self, location: str, seed_entity_id: str, target_type: str = "movie", **params: Any) -> Dict[str, Any]:
        """Request location-filtered cultural recommendations."""
        p = {
            "filter.type": f"urn:entity:{target_type}",
            "signal.interests.entities": seed_entity_id,
            "filter.location.query": location,
            **params,
        }
        return self.insights(**p)

    def compare(self, entity_ids: List[str], target_type: str = "movie", **params: Any) -> Dict[str, Any]:
        """Compare multiple interest entities to generate insights."""
        if not entity_ids:
            raise ValueError("Comparison requires at least one entity ID.")
        p = {
            "filter.type": f"urn:entity:{target_type}",
            "signal.interests.entities": entity_ids,
            **params,
        }
        return self.insights(**p)
