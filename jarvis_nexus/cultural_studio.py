"""Cultural Intelligence Studio backend service and serialization logic for Qloo integration."""

import json
from typing import Any, Dict, List, Optional
from jarvis_nexus.qloo_provider import QlooProvider
from jarvis_nexus.security import safe_exception_message

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


def normalize_entity_type(raw_type: str) -> str:
    """Normalize entity type URNs into clean human-readable categories."""
    if not raw_type:
        return "Entity"
    t = raw_type.strip()
    if t.startswith("urn:entity:"):
        t = t[len("urn:entity:"):]
    elif t.startswith("urn:"):
        parts = t.split(":")
        t = parts[-1]

    if not t:
        return "Entity"

    abbreviations = {"tv": "TV", "dj": "DJ", "ai": "AI"}
    words = t.replace("_", " ").split()
    normalized_words = [abbreviations.get(w.lower(), w.capitalize()) for w in words]
    return " ".join(normalized_words)


def normalize_url(url: str) -> str:
    """Validate schemes and upgrade known services to HTTPS safely."""
    if not isinstance(url, str):
        return ""
    u = url.strip()
    if u.startswith("http://"):
        parsed_lower = u.lower()
        known_https_domains = [
            "wikipedia.org", "imdb.com", "spotify.com", "instagram.com",
            "youtube.com", "twitter.com", "x.com", "facebook.com",
            "amazon.com", "apple.com", "soundcloud.com", "discogs.com",
            "wikidata.org", "qloo.com", "goodreads.com", "letterboxd.com"
        ]
        for domain in known_https_domains:
            if domain in parsed_lower:
                u = "https://" + u[7:]
                break
    return u


def serialize_entity(item: dict) -> dict:
    props = item.get("properties") or {}

    # Support diverse Qloo image representations (string, dict, list of dicts/strings)
    raw_img = (
        props.get("image") or
        item.get("image") or
        props.get("images") or
        item.get("images") or
        props.get("thumbnail") or
        ""
    )
    image = ""
    if isinstance(raw_img, list) and raw_img:
        raw_img = raw_img[0]
    if isinstance(raw_img, dict):
        image = (
            raw_img.get("url") or
            raw_img.get("source") or
            raw_img.get("large") or
            raw_img.get("medium") or
            raw_img.get("small") or
            ""
        )
    elif isinstance(raw_img, str):
        image = raw_img
    image = normalize_url(image)

    raw_type = str(item.get("type") or item.get("entity_type") or props.get("type") or "")
    normalized_type = normalize_entity_type(raw_type)

    raw_tags = item.get("tags") or props.get("tags") or []
    tags = []
    for t in raw_tags[:15]:
        if isinstance(t, dict):
            tags.append({
                "id": str(t.get("id") or ""),
                "name": str(t.get("name") or t.get("title") or ""),
                "type": str(t.get("type") or "tag"),
            })
        elif isinstance(t, str):
            tags.append({"id": t, "name": t, "type": "tag"})

    raw_ext = item.get("external") or props.get("external") or {}
    external = {}
    if isinstance(raw_ext, dict):
        for k, v in raw_ext.items():
            if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                external[k] = normalize_url(v)
            elif isinstance(v, dict) and "url" in v:
                external[k] = normalize_url(str(v["url"]))

    websites = props.get("websites") or item.get("websites") or []
    if isinstance(websites, list):
        valid_webs = [normalize_url(w) for w in websites if isinstance(w, str) and (w.startswith("http://") or w.startswith("https://"))]
        if valid_webs:
            external["website"] = valid_webs[0]

    explainability = item.get("explainability") or props.get("explainability") or None

    return {
        "entity_id": str(item.get("entity_id") or item.get("id") or ""),
        "name": str(item.get("name") or "Unnamed result")[:200],
        "type": normalized_type,
        "type_urn": raw_type,
        "subtype": str(item.get("subtype") or ""),
        "disambiguation": str(item.get("disambiguation") or ""),
        "popularity": item.get("popularity"),
        "properties": {
            "description": str(props.get("description") or props.get("plot_summary") or "")[:1000],
            "plot_summary": str(props.get("plot_summary") or "")[:1500],
            "genre_description": str(props.get("genre_description") or ""),
            "genres": props.get("genres") or [],
            "keywords": props.get("keywords") or [],
            "release_year": props.get("release_year") or props.get("release_date") or "",
            "duration": props.get("duration") or "",
            "content_rating": props.get("content_rating") or "",
            "production_companies": props.get("production_companies") or [],
            "filming_location": props.get("filming_location") or [],
            "release_country": props.get("release_country") or "",
            "image": str(image),
        },
        "tags": tags,
        "external": external,
        "explainability": explainability,
    }


def handle_cultural_recommend(data: Dict[str, Any]) -> Dict[str, Any]:
    queries = data.get("queries")
    if not queries:
        q_single = data.get("query", "")
        if q_single:
            queries = [q_single]
    seed_type = str(data.get("seed_type", "artist"))
    target_type = str(data.get("target_type", "artist"))
    explainability = bool(data.get("explainability", False))
    location = data.get("location", "").strip()

    if not isinstance(queries, list) or not queries or not queries[0].strip():
        return {"error": "Enter an interest to search for."}
    if seed_type not in ALLOWED_CATEGORIES or target_type not in ALLOWED_CATEGORIES:
        return {"error": "Unsupported entity category."}

    qloo = QlooProvider()
    seed_ids = []
    safe_seeds = []
    last_error = None
    for q in queries[:5]:
        if not isinstance(q, str) or not q.strip():
            continue
        try:
            search_result = qloo.search(
                q.strip(),
                types=ALLOWED_CATEGORIES[seed_type],
                take=1,
            )
        except Exception as exc:
            last_error = exc
            continue
        s_data = search_result.get("results", search_result)
        s_entities = s_data.get("entities", s_data.get("items", [])) if isinstance(s_data, dict) else s_data if isinstance(s_data, list) else []
        if s_entities:
            s = s_entities[0]
            s_id = s.get("entity_id") or s.get("id")
            if s_id:
                seed_ids.append(str(s_id))
                safe_seeds.append({
                    "name": str(s.get("name") or q)[:200],
                    "entity_id": str(s_id),
                })

    if not seed_ids:
        if last_error:
            return {"error": safe_exception_message(last_error)}
        return {"error": "Qloo found no matching entity. Try a different name."}

    insights_params = {
        "filter.type": ALLOWED_CATEGORIES[target_type],
        "signal.interests.entities": seed_ids if len(seed_ids) > 1 else seed_ids[0],
        "take": 12,
    }
    if explainability:
        insights_params["feature.explainability"] = "true"
    if location:
        insights_params["filter.location.query"] = location

    try:
        insight_result = qloo.insights(**insights_params)
    except Exception as exc:
        return {"error": safe_exception_message(exc)}

    ins_data = insight_result.get("results", insight_result)
    recommendations = ins_data.get("entities", ins_data.get("items", [])) if isinstance(ins_data, dict) else ins_data if isinstance(ins_data, list) else []

    safe_recs = [serialize_entity(item) for item in recommendations if isinstance(item, dict)]
    legacy_seed = safe_seeds[0] if safe_seeds else {"name": queries[0], "entity_id": ""}

    return {
        "seed": legacy_seed,
        "seeds": safe_seeds,
        "recommendations": safe_recs,
    }


def handle_cultural_trending(data: Dict[str, Any]) -> Dict[str, Any]:
    category = str(data.get("category", "movie"))
    if category not in ALLOWED_CATEGORIES:
        return {"error": "Unsupported category."}
    qloo = QlooProvider()
    try:
        res = qloo.trending(category=category, take=12)
    except Exception as exc:
        return {"error": safe_exception_message(exc)}
    d = res.get("results", res)
    items = d.get("entities", d.get("items", [])) if isinstance(d, dict) else d if isinstance(d, list) else []
    return {"recommendations": [serialize_entity(i) for i in items if isinstance(i, dict)]}


def handle_cultural_geographic(data: Dict[str, Any]) -> Dict[str, Any]:
    location = str(data.get("location", ""))
    seed_id = str(data.get("seed_entity_id", ""))
    target_type = str(data.get("target_type", "movie"))
    if not location or not seed_id or target_type not in ALLOWED_CATEGORIES:
        return {"error": "Location, seed entity ID, and valid target category are required."}
    qloo = QlooProvider()
    try:
        res = qloo.geographic(location=location, seed_entity_id=seed_id, target_type=target_type, take=12)
    except Exception as exc:
        return {"error": safe_exception_message(exc)}
    d = res.get("results", res)
    items = d.get("entities", d.get("items", [])) if isinstance(d, dict) else d if isinstance(d, list) else []
    return {"recommendations": [serialize_entity(i) for i in items if isinstance(i, dict)]}


def handle_cultural_compare(data: Dict[str, Any]) -> Dict[str, Any]:
    entity_ids = data.get("entity_ids", [])
    target_type = str(data.get("target_type", "movie"))
    if not isinstance(entity_ids, list) or not entity_ids or target_type not in ALLOWED_CATEGORIES:
        return {"error": "Entity IDs list and valid target category are required."}
    qloo = QlooProvider()
    try:
        res = qloo.compare(entity_ids=entity_ids, target_type=target_type, take=12)
    except Exception as exc:
        return {"error": safe_exception_message(exc)}
    d = res.get("results", res)
    items = d.get("entities", d.get("items", [])) if isinstance(d, dict) else d if isinstance(d, list) else []
    return {"recommendations": [serialize_entity(i) for i in items if isinstance(i, dict)]}


def handle_cultural_favorites_get(memory_store: Any) -> Dict[str, Any]:
    favs = []
    for mem in memory_store.list_memories("cultural_favorite"):
        try:
            favs.append(json.loads(mem["value"]))
        except Exception:
            pass
    return {"favorites": favs}


def handle_cultural_favorites_post(data: Dict[str, Any], memory_store: Any) -> Dict[str, Any]:
    entity_data = data.get("entity")
    if not isinstance(entity_data, dict) or not entity_data.get("entity_id"):
        return {"error": "Valid entity data with entity_id is required."}
    eid = str(entity_data["entity_id"])
    success = memory_store.save_memory(
        key=f"fav_{eid}",
        value=json.dumps(entity_data),
        category="cultural_favorite"
    )
    return {"success": success}


def handle_cultural_favorites_delete(query: Dict[str, List[str]], memory_store: Any) -> Dict[str, Any]:
    entity_id = query.get("entity_id", [""])[0]
    success = memory_store.delete_memory(f"fav_{entity_id}") if entity_id else False
    return {"success": success}
