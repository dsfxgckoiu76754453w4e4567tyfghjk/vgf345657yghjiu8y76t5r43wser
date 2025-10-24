# MODULE 06: TOOLS - AHKAM (RELIGIOUS RULINGS)
[◀️ Back to Index](./00-INDEX.md) | [Previous](./05-ADMIN-SYSTEM.md) | [Next: Hadith Tool ▶️](./07-TOOLS-HADITH.md)

---

## ⚠️ CRITICAL CHANGE IN v3.0

**The Ahkam tool has been completely redesigned. It does NOT use RAG. It fetches directly from official Marja websites with maximum citations.**

---

## 📋 TABLE OF CONTENTS
1. [Architecture & Design](#architecture--design)
2. [Database Tables](#database-tables)
3. [Tool Implementation](#tool-implementation)
4. [Fetching from Official Sources](#fetching-from-official-sources)
5. [Admin Management UI](#admin-management-ui)
6. [Configuration](#configuration)
7. [Rate Limiting & Caching](#rate-limiting--caching)

---

## UPDATED AHKAM TOOL (NOT RAG-BASED)

### Critical Change

**The Ahkam (religious rulings) tool has been completely redesigned. It does NOT use RAG retrieval. Instead, it fetches directly from official Marja websites with maximum citations.**

### Why This Change?

1. **Authenticity**: Direct fetching ensures rulings come from official sources
2. **Up-to-date**: Always gets the latest rulings, not cached embeddings
3. **Citations**: Provides direct links to official websites
4. **Trust**: Users can verify rulings directly on Marja's website

### Database Schema Addition

Already added to main plan:
- `marja_official_sources` table: Configuration for each Marja's official website
- `ahkam_fetch_log` table: Tracking all Ahkam fetches

### Implementation

```python
from typing import Optional, Dict, List
import httpx
from bs4 import BeautifulSoup
from langchain.tools import tool

@tool
async def ahkam_lookup_from_official_source(
    question: str,
    user_marja: str = "Khamenei",
    category: Optional[str] = None
) -> Dict:
    """
    Look up religious ruling (حکم) from official Marja website.

    CRITICAL: This does NOT use RAG. It fetches directly from official sources.

    Args:
        question: The ruling question in Persian, Arabic, or English
        user_marja: The Marja to consult (default: Khamenei)
        category: Fiqh category (optional: 'prayer', 'fasting', 'zakat', etc.)

    Returns:
        {
            "ruling": str,  # The ruling in original language
            "source_url": str,  # Direct link to official website
            "citation": str,  # Full citation with reference
            "confidence": float,
            "variations": list  # Other Marja opinions if different
        }
    """

    # Step 1: Get official source configuration from database
    marja_source = await get_marja_official_source(user_marja)

    if not marja_source or not marja_source.is_active:
        return {
            "ruling": f"No official source configured for Marja {user_marja}",
            "error": True,
            "source_url": None,
            "message_code": "NO_OFFICIAL_SOURCE_CONFIGURED"  # English standard code
        }

    # Step 2: Check cache first (24-hour cache as per config)
    cache_key = f"ahkam:{user_marja}:{hash(question)}"
    cached_result = await redis_client.get(cache_key)

    if cached_result:
        logger.info(f"Ahkam cache hit for {user_marja}: {question[:50]}")
        return json.loads(cached_result)

    # Step 3: Classify fiqh category if not provided
    if not category:
        category = await classify_fiqh_category_fast(question)

    try:
        # Step 4: Fetch from official website
        if marja_source.has_official_api:
            # Use official API
            result = await fetch_from_official_api(
                marja_source=marja_source,
                question=question,
                category=category
            )
        else:
            # Use web scraping (respectful, rate-limited)
            result = await fetch_via_web_scraping(
                marja_source=marja_source,
                question=question,
                category=category
            )

        if not result or not result.get("ruling_found"):
            return {
                "ruling": "No clear ruling found in official sources",
                "confidence": 0.0,
                "source_url": marja_source.official_website_url,
                "message_code": "NO_RULING_FOUND",
                "note": "Please consult the Marja's office directly for clarification"
            }

        # Step 5: Format response with maximum citations
        formatted_response = {
            "ruling": result["ruling_text"],
            "source_url": result["direct_url"],  # Direct link to this specific ruling
            "citation": format_official_citation(result, marja_source),
            "confidence": result.get("confidence", 0.9),
            "marja_name": marja_source.marja_name,
            "retrieved_at": datetime.now().isoformat(),
            "language": result.get("language", "fa"),
            "category": category,
            "message_code": "RULING_FOUND_SUCCESS"
        }

        # Step 6: Check for variations from other Maraji (optional)
        if should_fetch_variations(question):
            variations = await fetch_other_marja_opinions(
                question=question,
                category=category,
                exclude_marja=user_marja
            )
            formatted_response["variations"] = variations

        # Step 7: Cache the result
        await redis_client.setex(
            cache_key,
            marja_source.cache_duration_hours * 3600,
            json.dumps(formatted_response)
        )

        # Step 8: Log the fetch for monitoring
        await log_ahkam_fetch(
            marja_source_id=marja_source.id,
            question=question,
            category=category,
            success=True,
            response_url=result["direct_url"]
        )

        return formatted_response

    except Exception as e:
        logger.error(f"Error fetching Ahkam from {user_marja}: {e}")
        await log_ahkam_fetch(
            marja_source_id=marja_source.id,
            question=question,
            category=category,
            success=False,
            error_message=str(e)
        )

        return {
            "ruling": "Unable to fetch ruling from official source at this time",
            "error": True,
            "error_message": "Please try again later or visit the official website",
            "source_url": marja_source.official_website_url,
            "message_code": "FETCH_ERROR"
        }


async def fetch_from_official_api(
    marja_source,
    question: str,
    category: str
) -> Dict:
    """Fetch ruling using official API if available"""

    async with httpx.AsyncClient() as client:
        headers = {}
        if marja_source.api_key_required:
            # Get decrypted API key
            api_key = await get_decrypted_api_key(marja_source.id)
            headers["Authorization"] = f"Bearer {api_key}"

        params = {
            "query": question,
            "category": category,
            "language": "fa"  # or detect from question
        }

        response = await client.get(
            marja_source.api_endpoint,
            headers=headers,
            params=params,
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "ruling_found": True,
                "ruling_text": data.get("ruling"),
                "direct_url": data.get("url"),
                "confidence": 0.95,  # High confidence for official API
                "language": data.get("language", "fa")
            }
        else:
            return {"ruling_found": False}


async def fetch_via_web_scraping(
    marja_source,
    question: str,
    category: str
) -> Dict:
    """
    Fetch ruling via respectful web scraping.
    Implements rate limiting and robots.txt compliance.
    """

    # Step 1: Check rate limits
    if not await check_rate_limit(marja_source.id):
        raise Exception("Rate limit exceeded for this Marja source")

    # Step 2: Construct search URL
    search_url = marja_source.search_url
    params = json.loads(marja_source.search_parameters or "{}")
    params[params.get("query_param", "q")] = question

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                search_url,
                params=params,
                headers={
                    "User-Agent": "Shia-Islamic-Chatbot/1.0 (Educational Purpose; +https://example.com/bot)",
                    "Accept-Language": "fa,ar,en"
                }
            )

            if response.status_code != 200:
                return {"ruling_found": False}

            # Step 3: Parse HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            selectors = json.loads(marja_source.content_selectors or "{}")

            ruling_element = soup.select_one(selectors.get("content", ".fatwa-content"))
            title_element = soup.select_one(selectors.get("title", ".fatwa-title"))

            if not ruling_element:
                return {"ruling_found": False}

            ruling_text = ruling_element.get_text(strip=True)
            title = title_element.get_text(strip=True) if title_element else "Ruling"

            # Get direct URL (might be relative)
            direct_url = response.url
            if ruling_element.find_parent('a'):
                link = ruling_element.find_parent('a').get('href')
                direct_url = urljoin(marja_source.official_website_url, link)

            return {
                "ruling_found": True,
                "ruling_text": ruling_text,
                "title": title,
                "direct_url": str(direct_url),
                "confidence": 0.85,  # Slightly lower for scraped content
                "language": "fa"  # Could be detected
            }

        except Exception as e:
            logger.error(f"Web scraping error for {marja_source.marja_name}: {e}")
            return {"ruling_found": False}


def format_official_citation(result: Dict, marja_source) -> str:
    """
    Format a comprehensive citation with maximum detail.

    Example output:
    "Ayatollah Khamenei, Official Website (www.leader.ir), Fiqh Section, Retrieved: 2025-10-24
     Direct Link: https://www.leader.ir/fa/book/23/صلاه/page/1234"
    """

    citation = f"{marja_source.marja_name}, Official Website ({marja_source.official_website_url})"

    if result.get("title"):
        citation += f", {result['title']}"

    citation += f", Retrieved: {datetime.now().strftime('%Y-%m-%d')}"

    if result.get("direct_url"):
        citation += f"\nDirect Link: {result['direct_url']}"

    return citation
```

### Admin Management UI

Super-admins can configure Marja official sources through the dashboard:

```python
@admin_router.post("/marja-sources/create")
async def create_marja_source(
    source_config: MarjaSourceConfig,
    admin: Admin = Depends(verify_super_admin)
):
    """
    Create or update official Marja source configuration.
    Only super-admins can do this.
    """

    check_permission(admin, "manage_marja_sources")

    source = await create_marja_official_source(
        marja_name=source_config.marja_name,
        official_website_url=source_config.website_url,
        has_official_api=source_config.has_api,
        scraping_config=source_config.scraping_config,
        search_url=source_config.search_url,
        content_selectors=source_config.content_selectors,
        added_by=admin.id
    )

    return {
        "message": f"Official source for {source_config.marja_name} configured successfully",
        "source_id": source.id,
        "message_code": "MARJA_SOURCE_CREATED"
    }

@admin_router.put("/marja-sources/{source_id}/test")
async def test_marja_source(
    source_id: str,
    test_question: str,
    admin: Admin = Depends(verify_super_admin)
):
    """
    Test a Marja source configuration with a sample question.
    """

    source = await get_marja_source(source_id)

    result = await ahkam_lookup_from_official_source(
        question=test_question,
        user_marja=source.marja_name
    )

    return {
        "test_successful": not result.get("error"),
        "result": result,
        "recommendations": analyze_test_result(result),
        "message_code": "TEST_COMPLETED"
    }
```

---



---

## 🔗 Related Modules
- **Database:** [02-DATABASE-SCHEMA.md](./02-DATABASE-SCHEMA.md) - `marja_official_sources`, `ahkam_fetch_log` tables
- **Admin Dashboard:** [05-ADMIN-SYSTEM.md](./05-ADMIN-SYSTEM.md) - Configuration UI
- **LangGraph:** [11-LANGGRAPH.md](./11-LANGGRAPH.md) - Tool integration

---

[◀️ Back to Index](./00-INDEX.md) | [Previous](./05-ADMIN-SYSTEM.md) | [Next: Hadith Tool ▶️](./07-TOOLS-HADITH.md)
