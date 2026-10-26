"""Tool registrations for Qloo Cultural Intelligence in JARVIS Nexus chat agent."""

from typing import Any, Dict, List, Optional
from jarvis_nexus.cultural_studio import (
    handle_cultural_recommend,
    handle_cultural_trending,
    handle_cultural_geographic,
    handle_cultural_compare,
    ALLOWED_CATEGORIES
)
from jarvis_nexus.qloo_provider import QlooProvider


def register_qloo_tools(tool_registry: Any) -> None:
    """Register Qloo cultural intelligence tools into the ToolRegistry."""

    def qloo_recommend(
        query: Optional[str] = None,
        queries: Optional[List[str]] = None,
        seed_type: str = "artist",
        target_type: str = "movie",
        explainability: bool = True,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cultural recommendations based on seed entities or queries using Qloo API."""
        payload = {
            "query": query,
            "queries": queries,
            "seed_type": seed_type,
            "target_type": target_type,
            "explainability": explainability,
            "location": location or ""
        }
        return handle_cultural_recommend(payload)

    tool_registry.register(
        name="qloo_recommend",
        description="Search Qloo for cultural recommendations across categories (artist, movie, tv_show, book, brand, destination, person, place, podcast, videogame) with optional explainability and location filtering.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Single seed interest or entity name (e.g. 'Burna Boy')."},
                "queries": {"type": "array", "items": {"type": "string"}, "description": "Multiple seed interest queries for multi-interest taste blending."},
                "seed_type": {"type": "string", "description": "Seed category (artist, movie, tv_show, book, brand, destination, person, place, podcast, videogame).", "default": "artist"},
                "target_type": {"type": "string", "description": "Target recommendation category.", "default": "movie"},
                "explainability": {"type": "boolean", "description": "Whether to include explainability reasoning.", "default": True},
                "location": {"type": "string", "description": "Optional location filter query (e.g. 'Tokyo')."}
            },
            "required": []
        },
        func=qloo_recommend
    )

    def qloo_trending(category: str = "movie") -> Dict[str, Any]:
        """Get currently trending cultural entities for a given category (movie, artist, tv_show, book, brand, destination, podcast, videogame)."""
        return handle_cultural_trending({"category": category})

    tool_registry.register(
        name="qloo_trending",
        description="Get currently trending cultural entities for a category (movie, artist, tv_show, book, brand, destination, podcast, videogame).",
        parameters={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category name (movie, artist, tv_show, book, brand, destination, podcast, videogame).", "default": "movie"}
            },
            "required": []
        },
        func=qloo_trending
    )

    def qloo_geographic(location: str, seed_entity_id: str, target_type: str = "movie") -> Dict[str, Any]:
        """Get location-filtered cultural recommendations based on a seed entity ID."""
        return handle_cultural_geographic({
            "location": location,
            "seed_entity_id": seed_entity_id,
            "target_type": target_type
        })

    tool_registry.register(
        name="qloo_geographic",
        description="Get location-filtered cultural recommendations for a specific city/region based on a seed entity ID.",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Location query (e.g. 'Tokyo', 'New York')."},
                "seed_entity_id": {"type": "string", "description": "Qloo seed entity ID."},
                "target_type": {"type": "string", "description": "Target category.", "default": "movie"}
            },
            "required": ["location", "seed_entity_id"]
        },
        func=qloo_geographic
    )

    def qloo_compare(entity_ids: List[str], target_type: str = "movie") -> Dict[str, Any]:
        """Compare multiple interest entity IDs to generate cross-interest cultural insights."""
        return handle_cultural_compare({
            "entity_ids": entity_ids,
            "target_type": target_type
        })

    tool_registry.register(
        name="qloo_compare",
        description="Compare multiple interest entity IDs to generate cross-interest cultural recommendations and insights.",
        parameters={
            "type": "object",
            "properties": {
                "entity_ids": {"type": "array", "items": {"type": "string"}, "description": "List of Qloo entity IDs to compare."},
                "target_type": {"type": "string", "description": "Target category.", "default": "movie"}
            },
            "required": ["entity_ids"]
        },
        func=qloo_compare
    )
