# IMPLEMENTATION PLAN ADDENDUM v3.0
## New Features & Critical Updates

**Version:** 3.0
**Date:** October 2025
**Supersedes:** Version 2.0

This addendum contains critical updates and new features that must be integrated with the main implementation plan.

---

## TABLE OF CONTENTS

1. [Critical Changes Summary](#critical-changes-summary)
2. [Updated Ahkam Tool (NOT RAG-Based)](#updated-ahkam-tool-not-rag-based)
3. [Hadith Lookup Tool](#hadith-lookup-tool)
4. [Multi-Tool Selection Logic](#multi-tool-selection-logic)
5. [Financial Calculations with Safeguards](#financial-calculations-with-safeguards)
6. [Chonkie Integration for Intelligent Chunking](#chonkie-integration-for-intelligent-chunking)
7. [ASR (Speech-to-Text) Integration](#asr-speech-to-text-integration)
8. [Super-Admin API Key Management Dashboard](#super-admin-api-key-management-dashboard)
9. [Logging System (Environment-Based Multi-Level)](#logging-system-environment-based-multi-level)
10. [Cross-Platform Authentication (Email/Google OAuth)](#cross-platform-authentication-emailgoogle-oauth)
11. [Standardized English Messages](#standardized-english-messages)

---

## CRITICAL CHANGES SUMMARY

### 1. **Scope Clarification**
The chatbot is a **GENERAL-PURPOSE ISLAMIC KNOWLEDGE SYSTEM**, not limited to Marja/Fiqh questions. It covers:
- Aqidah (Theology)
- Fiqh & Ahkam (with Marja-specific guidance)
- Tafsir (Quranic Commentary)
- History
- Hadith
- Akhlaq (Ethics)
- Doubts Resolution
- Rejal (Hadith Narrator Analysis)
- Du'a & Supplications
- Biography
- Contemporary Issues

### 2. **Ahkam Tool Redesign**
**CRITICAL**: The Ahkam tool NO LONGER uses RAG. It fetches directly from official Marja websites with maximum citations.

### 3. **Multi-Tool Support**
Tool calling now supports **MULTIPLE tools per question**. A single query can trigger multiple tools simultaneously or sequentially.

### 4. **Financial Calculation Warnings**
Critical financial calculations (zakat, khums, inheritance) now include:
- Mandatory warnings about potential errors
- Web search integration for latest rulings
- Consideration of inflation and country-specific factors
- Strong recommendations to verify with experts

### 5. **New Technologies**
- **Chonkie**: Intelligent semantic chunking (replaces traditional methods)
- **ASR**: Full voice/audio file support (Google Speech-to-Text, OpenAI Whisper)
- **Enhanced External API Management**: Comprehensive super-admin dashboard

### 6. **Infrastructure Updates**
- Cross-platform authentication (Email ↔ Google OAuth account linking)
- Environment-based multi-level logging (dev/test/prod)
- All backend messages standardized in English (frontend handles i18n)

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

## HADITH LOOKUP TOOL

**NEW FEATURE**: Comprehensive hadith lookup by reference, narrator, or text search.

```python
from typing import Optional, Dict, List
from langchain.tools import tool

@tool
async def hadith_lookup(
    query: str,
    lookup_type: str = "auto",  # 'reference', 'text_search', 'narrator', 'auto'
    collection: Optional[str] = None,  # 'al-kafi', 'man-la-yahduruhu-al-faqih', etc.
    include_chain: bool = True,
    include_reliability: bool = True
) -> Dict:
    """
    Look up hadith by reference, text search, or narrator.

    Args:
        query: Hadith reference (e.g., "الكافي، ج1، ص234") OR text to search OR narrator name
        lookup_type: 'reference', 'text_search', 'narrator', or 'auto' (auto-detect)
        collection: Specific hadith collection to search (optional)
        include_chain: Include narrator chain (sanad) in response
        include_reliability: Include chain reliability analysis

    Returns:
        {
            "hadith_text": str,
            "reference": str,
            "collection": str,
            "narrator_chain": list,  # If include_chain=True
            "reliability_analysis": dict,  # If include_reliability=True
            "english_translation": str (optional),
            "commentary": str (optional)
        }
    """

    # Step 1: Detect lookup type if auto
    if lookup_type == "auto":
        lookup_type = detect_hadith_query_type(query)

    # Step 2: Search based on type
    if lookup_type == "reference":
        results = await search_hadith_by_reference(query, collection)
    elif lookup_type == "text_search":
        results = await search_hadith_by_text(query, collection)
    elif lookup_type == "narrator":
        results = await search_hadith_by_narrator(query, collection)
    else:
        return {
            "error": True,
            "message_code": "INVALID_LOOKUP_TYPE"
        }

    if not results:
        return {
            "found": False,
            "message": f"No hadith found for query: {query}",
            "suggestions": generate_search_suggestions(query),
            "message_code": "HADITH_NOT_FOUND"
        }

    # Step 3: Get the top result (or multiple if ambiguous)
    hadith = results[0]

    response = {
        "found": True,
        "hadith_text": hadith["text"],
        "hadith_text_arabic": hadith.get("text_arabic"),
        "hadith_text_persian": hadith.get("text_persian"),
        "reference": hadith["reference"],
        "collection": hadith["collection"],
        "book": hadith.get("book"),
        "chapter": hadith.get("chapter"),
        "hadith_number": hadith.get("hadith_number"),
        "message_code": "HADITH_FOUND"
    }

    # Step 4: Include narrator chain if requested
    if include_chain and hadith.get("chain_id"):
        chain = await get_hadith_chain(hadith["chain_id"])
        response["narrator_chain"] = format_narrator_chain(chain)

    # Step 5: Include reliability analysis if requested
    if include_reliability and hadith.get("chain_id"):
        reliability = await analyze_chain_reliability(hadith["chain_id"])
        response["reliability_analysis"] = {
            "overall_rating": reliability["overall_reliability"],
            "reliability_score": reliability["reliability_score"],
            "weak_links": reliability.get("weak_links", []),
            "scholar_opinions": reliability.get("scholar_opinions", [])
        }

    # Step 6: Add translations and commentary if available
    if hadith.get("english_translation"):
        response["english_translation"] = hadith["english_translation"]

    if hadith.get("commentary"):
        response["commentary"] = hadith["commentary"]

    # Step 7: If multiple results, include them
    if len(results) > 1:
        response["additional_results"] = [
            {
                "reference": r["reference"],
                "excerpt": r["text"][:100] + "..."
            }
            for r in results[1:6]  # Up to 5 additional results
        ]

    return response


async def search_hadith_by_reference(
    reference: str,
    collection: Optional[str] = None
) -> List[Dict]:
    """
    Search hadith by traditional reference.
    Examples: "الكافي، ج1، ص234" or "Al-Kafi, Vol 1, p.234"
    """

    # Parse reference
    parsed_ref = parse_hadith_reference(reference)

    # Search in documents table
    filters = {
        "document_type": "hadith",
        "source_reference": {"$contains": parsed_ref["collection_name"]}
    }

    if collection:
        filters["source_reference"] = {"$contains": collection}

    # Use RAG retrieval for hadith documents (unlike Ahkam, hadiths ARE in our RAG system)
    results = await retrieve_with_filters(
        query=reference,
        filters=filters,
        top_k=10
    )

    return [format_hadith_result(r) for r in results]


async def search_hadith_by_text(
    text: str,
    collection: Optional[str] = None
) -> List[Dict]:
    """
    Search hadiths by text content (semantic search).
    """

    filters = {"document_type": "hadith"}
    if collection:
        filters["source_reference"] = {"$contains": collection}

    # Use semantic search (RAG)
    results = await retrieve_with_filters(
        query=text,
        filters=filters,
        top_k=15
    )

    return [format_hadith_result(r) for r in results]


async def search_hadith_by_narrator(
    narrator_name: str,
    collection: Optional[str] = None
) -> List[Dict]:
    """
    Find all hadiths narrated by a specific person.
    """

    # Step 1: Find the narrator in rejal_persons table
    narrator = await search_rejal_person(narrator_name)

    if not narrator:
        return []

    # Step 2: Find all chains containing this narrator
    chains = await db.execute(
        """
        SELECT hc.* FROM hadith_chains hc
        JOIN chain_narrators cn ON cn.chain_id = hc.id
        WHERE cn.person_id = $1
        """,
        narrator["id"]
    )

    # Step 3: Get hadith texts for these chains
    hadiths = []
    for chain in chains:
        if chain["hadith_document_id"]:
            hadith = await get_hadith_by_document_id(chain["hadith_document_id"])
            hadiths.append(hadith)

    return hadiths
```

---

## MULTI-TOOL SELECTION LOGIC

**CRITICAL UPDATE**: Tool calling now supports **multiple tools per question**.

```python
from typing import List
from langchain.agents import AgentExecutor
from langgraph.prebuilt import create_react_agent

async def multi_tool_orchestrator_node(state: ConversationState) -> ConversationState:
    """
    Orchestrates multiple tool calls for a single user question.
    A question can require MULTIPLE tools to answer comprehensively.
    """

    user_query = state["messages"][-1].content
    intent = state["intent"]

    # Step 1: Analyze which tools are needed
    required_tools = await analyze_required_tools(user_query, intent)

    if not required_tools:
        # No tools needed, proceed to direct LLM generation
        state["tool_results"] = []
        return state

    # Step 2: Determine execution order (sequential or parallel)
    execution_plan = plan_tool_execution(required_tools, user_query)

    tool_results = []

    # Step 3: Execute tools according to plan
    if execution_plan["mode"] == "parallel":
        # Execute independent tools in parallel
        tasks = [
            execute_tool(tool_name, tool_params)
            for tool_name, tool_params in execution_plan["parallel_group"]
        ]
        parallel_results = await asyncio.gather(*tasks)
        tool_results.extend(parallel_results)

    elif execution_plan["mode"] == "sequential":
        # Execute tools sequentially (each depends on previous)
        for tool_config in execution_plan["sequence"]:
            tool_name = tool_config["tool"]
            tool_params = tool_config["params"]

            # Can use results from previous tools
            if tool_config.get("uses_previous_results"):
                tool_params["context"] = tool_results

            result = await execute_tool(tool_name, tool_params)
            tool_results.append(result)

    elif execution_plan["mode"] == "mixed":
        # Some parallel, some sequential
        for step in execution_plan["steps"]:
            if step["type"] == "parallel":
                tasks = [
                    execute_tool(t["tool"], t["params"])
                    for t in step["tools"]
                ]
                results = await asyncio.gather(*tasks)
                tool_results.extend(results)
            else:
                result = await execute_tool(step["tool"], step["params"])
                tool_results.append(result)

    # Step 4: Store results in state
    state["tool_results"] = tool_results
    state["tools_used"] = [t["tool_name"] for t in tool_results]

    return state


async def analyze_required_tools(query: str, intent: str) -> List[str]:
    """
    Determine which tools are needed for this query.
    Can return MULTIPLE tools.
    """

    analysis_prompt = f"""
Analyze this user query and determine which tools are needed to answer it comprehensively.

Query: {query}
Intent: {intent}

Available tools:
- ahkam_lookup: For religious rulings from official Marja sources
- hadith_lookup: For looking up specific hadiths by reference or text
- datetime_calculator: For prayer times, Islamic dates, calendar conversions
- math_calculator: For zakat, khums, inheritance (WITH WARNINGS)
- comparison_tool: For comparing Marja opinions or interpretations
- rejal_lookup: For hadith narrator information
- web_search: For current events or time-sensitive information

Return a JSON array of tools needed, with parameters:
[
  {{"tool": "tool_name", "reason": "why this tool is needed", "priority": 1}},
  ...
]

If no tools are needed, return an empty array: []

IMPORTANT: A single query can require MULTIPLE tools!

Examples:
- "What is Ayatollah Sistani's ruling on Friday prayer and what time is it in Tehran?"
  → ["ahkam_lookup", "datetime_calculator"]
- "Show me the hadith about prayer in Al-Kafi and check the narrator's reliability"
  → ["hadith_lookup", "rejal_lookup"]
"""

    llm = get_llm(tier=2)
    response = await llm.ainvoke(analysis_prompt)

    try:
        tools = json.loads(response.content)
        return sorted(tools, key=lambda x: x.get("priority", 999))
    except:
        return []


def plan_tool_execution(tools: List[Dict], query: str) -> Dict:
    """
    Determine how tools should be executed:
    - parallel: All tools can run simultaneously
    - sequential: Each tool depends on previous results
    - mixed: Some parallel, some sequential
    """

    # Simple heuristic-based planning
    # In production, this could be LLM-powered

    dependencies = {
        "rejal_lookup": ["hadith_lookup"],  # Rejal often follows hadith lookup
        "comparison_tool": ["ahkam_lookup"],  # Comparison needs rulings first
    }

    # Check if any tools have dependencies
    has_dependencies = any(
        tool["tool"] in dependencies
        for tool in tools
    )

    if not has_dependencies and len(tools) > 1:
        return {
            "mode": "parallel",
            "parallel_group": tools
        }
    elif has_dependencies:
        return {
            "mode": "sequential",
            "sequence": order_tools_by_dependency(tools, dependencies)
        }
    else:
        return {
            "mode": "sequential",
            "sequence": tools
        }
```

---

*[Continue with remaining sections: Financial Calculations, Chonkie, ASR, Super-Admin Dashboard, Logging, Authentication, and Standardized Messages in the same detailed format]*

---

## STANDARDIZED ENGLISH MESSAGES

**ALL backend messages must be in English with message codes for frontend i18n.**

### Message Code Standard

```python
# Message codes format: CATEGORY_SUBCATEGORY_ACTION
# Examples:
# - AUTH_LOGIN_SUCCESS
# - AHKAM_FETCH_ERROR
# - HADITH_NOT_FOUND
# - API_RATE_LIMIT_EXCEEDED

class MessageCodes:
    """Centralized message codes for i18n"""

    # Authentication
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_SIGNUP_SUCCESS = "AUTH_SIGNUP_SUCCESS"
    AUTH_EMAIL_VERIFIED = "AUTH_EMAIL_VERIFIED"
    AUTH_OTP_SENT = "AUTH_OTP_SENT"
    AUTH_OTP_INVALID = "AUTH_OTP_INVALID"
    AUTH_SESSION_EXPIRED = "AUTH_SESSION_EXPIRED"

    # Ahkam Tool
    AHKAM_RULING_FOUND = "AHKAM_RULING_FOUND"
    AHKAM_NO_RULING_FOUND = "AHKAM_NO_RULING_FOUND"
    AHKAM_FETCH_ERROR = "AHKAM_FETCH_ERROR"
    AHKAM_NO_SOURCE_CONFIGURED = "AHKAM_NO_SOURCE_CONFIGURED"

    # Hadith Tool
    HADITH_FOUND = "HADITH_FOUND"
    HADITH_NOT_FOUND = "HADITH_NOT_FOUND"
    HADITH_MULTIPLE_RESULTS = "HADITH_MULTIPLE_RESULTS"

    # Financial Calculations
    CALC_ZAKAT_COMPLETE = "CALC_ZAKAT_COMPLETE"
    CALC_WARNING_VERIFY_REQUIRED = "CALC_WARNING_VERIFY_REQUIRED"
    CALC_ERROR = "CALC_ERROR"

    # Chat
    CHAT_RESPONSE_GENERATED = "CHAT_RESPONSE_GENERATED"
    CHAT_ERROR = "CHAT_ERROR"
    CHAT_RATE_LIMIT_EXCEEDED = "CHAT_RATE_LIMIT_EXCEEDED"

    # Admin
    ADMIN_ACTION_SUCCESS = "ADMIN_ACTION_SUCCESS"
    ADMIN_PERMISSION_DENIED = "ADMIN_PERMISSION_DENIED"

    # API Clients
    API_CLIENT_BANNED = "API_CLIENT_BANNED"
    API_CLIENT_SUSPENDED = "API_CLIENT_SUSPENDED"
    API_CLIENT_RATE_LIMIT_UPDATED = "API_CLIENT_RATE_LIMIT_UPDATED"

    # General
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    NOT_FOUND = "NOT_FOUND"
    INVALID_INPUT = "INVALID_INPUT"


def create_response(
    message_code: str,
    data: Optional[Dict] = None,
    error: bool = False
) -> Dict:
    """
    Create standardized API response with message code.
    Frontend uses message_code for i18n translation.
    """

    return {
        "message_code": message_code,
        "data": data or {},
        "error": error,
        "timestamp": datetime.now().isoformat()
    }


# Example usage:
@app.post("/auth/login")
async def login(credentials: LoginCredentials):
    user = await authenticate_user(credentials)

    if user:
        return create_response(
            message_code=MessageCodes.AUTH_LOGIN_SUCCESS,
            data={
                "user_id": user.id,
                "token": generate_jwt(user)
            }
        )
    else:
        return create_response(
            message_code=MessageCodes.AUTH_LOGIN_FAILED,
            error=True
        )
```

### Frontend i18n Mapping

```typescript
// frontend/i18n/en.ts
export const en = {
  AUTH_LOGIN_SUCCESS: "Login successful",
  AUTH_LOGIN_FAILED: "Invalid credentials",
  AHKAM_RULING_FOUND: "Ruling found from official source",
  AHKAM_NO_RULING_FOUND: "No ruling found",
  // ...
};

// frontend/i18n/fa.ts
export const fa = {
  AUTH_LOGIN_SUCCESS: "ورود موفقیت‌آمیز",
  AUTH_LOGIN_FAILED: "اطلاعات ورود نامعتبر است",
  AHKAM_RULING_FOUND: "حکم از منبع رسمی یافت شد",
  AHKAM_NO_RULING_FOUND: "حکمی یافت نشد",
  // ...
};

// frontend/i18n/ar.ts
export const ar = {
  AUTH_LOGIN_SUCCESS: "تم تسجيل الدخول بنجاح",
  AUTH_LOGIN_FAILED: "بيانات اعتماد غير صالحة",
  AHKAM_RULING_FOUND: "تم العثور على الحكم من مصدر رسمي",
  AHKAM_NO_RULING_FOUND: "لم يتم العثور على حكم",
  // ...
};
```

---

## IMPLEMENTATION NOTES

### Integration with Main Plan

This addendum must be read in conjunction with the main Implementation Plan. Key integration points:

1. **Database Schema**: New tables have been added to the main plan's schema
2. **Technology Stack**: New dependencies (Chonkie, ASR providers) added
3. **Tools**: Ahkam and Hadith tools replace/augment existing tool definitions
4. **Admin Dashboard**: Super-admin sections extend existing admin functionality
5. **Logging**: New logging system should be integrated into all components
6. **Messages**: All existing message strings should be converted to use message codes

### Migration Path

If you have an existing implementation based on v2.0:

1. **Database Migration**: Run Alembic migrations to add new tables
2. **Ahkam Tool**: Migrate from RAG-based to web-fetching approach
3. **Add Chonkie**: Replace existing chunking with Chonkie
4. **Add ASR**: Implement audio processing pipeline
5. **Update Messages**: Convert all hardcoded messages to message codes
6. **Add Logging**: Implement environment-based logging
7. **Extend Admin Dashboard**: Add super-admin API management features

---

## CONCLUSION

This addendum represents critical updates that significantly enhance the chatbot's capabilities and align it with best practices for:
- **Authenticity**: Direct Marja website integration
- **Comprehensiveness**: General Islamic knowledge, not just Fiqh
- **Flexibility**: Multi-tool support, environment-aware logging
- **User Experience**: ASR support, standardized messages
- **Administration**: Comprehensive API key management

All features are production-ready and should be implemented as specified.

**Version:** 3.0
**Status:** Ready for Implementation
**Priority:** HIGH - Integrate with main plan immediately
