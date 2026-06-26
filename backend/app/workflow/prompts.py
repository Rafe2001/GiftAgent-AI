"""
All LLM prompt templates for the gift recommendation workflow.
Centralised here for easy tuning and review.
"""

SIGNAL_EXTRACTION_SYSTEM = """You are an expert at analysing professional profiles to extract gifting signals.
You identify interests, hobbies, professional passions, and personality traits that can inform thoughtful gift choices.
You are careful, nuanced, and avoid making assumptions about sensitive personal attributes."""

SIGNAL_EXTRACTION_PROMPT = """Analyse the following professional contact profile and extract gifting signals.

CONTACT PROFILE:
- Name: {name}
- Role: {role}
- Company: {company}
- Location: {location}
- Headline: {headline}
- About: {about}

EXPERIENCE:
{experience}

RECENT POSTS:
{recent_posts}

RECENT COMMENTS:
{recent_comments}

ENGAGED TOPICS:
{engaged_topics}

RELATIONSHIP CONTEXT:
- Type: {relationship_type}
- Last interaction: {last_interaction}
- Business goal: {business_goal}

GIFT CONTEXT:
- Occasion: {occasion}
- Budget: {currency} {budget_min} - {budget_max}
- Country: {country}

Extract the following as JSON:
{{
    "strong_signals": ["list of clear, well-supported interests and traits that can guide gift selection"],
    "weak_signals": ["list of possible but less certain interests — inferred with lower confidence"],
    "signals_to_avoid": ["list of sensitive areas that MUST NOT be used for gift selection — e.g. religion, politics, health, family status, ethnicity, gender assumptions"]
}}

RULES:
1. Strong signals must be directly supported by posts, comments, topics, or experience.
2. Weak signals can be reasonable inferences but must be flagged as assumptions.
3. NEVER infer religion, politics, health conditions, family status, ethnicity, sexual orientation, or other sensitive attributes.
4. Focus on professional interests, hobbies, sports, books, technology, food/drink preferences (only if explicitly mentioned).
5. Consider the professional relationship type when weighing signals.
6. Return ONLY valid JSON."""

# ---

SIGNAL_FILTER_SYSTEM = """You are a safety reviewer for a corporate gifting system.
Your job is to review extracted profile signals and remove any that could be:
- Based on sensitive personal attributes (religion, politics, health, ethnicity, gender, family)
- Overly personal or inappropriate for a professional relationship
- Based on assumptions not supported by the data
You are strict and conservative."""

SIGNAL_FILTER_PROMPT = """Review these extracted gifting signals for safety and appropriateness.

STRONG SIGNALS:
{strong_signals}

WEAK SIGNALS:
{weak_signals}

SIGNALS TO AVOID:
{signals_to_avoid}

RELATIONSHIP TYPE: {relationship_type}

Review each signal and return filtered signals as JSON:
{{
    "strong_signals": ["only signals that are safe, appropriate, and well-supported"],
    "weak_signals": ["only signals that are safe, clearly flagged as assumptions"],
    "signals_to_avoid": ["updated list including any signals you removed and why"],
    "removed_signals": ["list any signals you removed with reason"]
}}

RULES:
1. Remove any signal based on religion, politics, health, family, ethnicity, or gender.
2. Remove any signal too personal for a {relationship_type} relationship.
3. Keep professional interests, clearly stated hobbies, and safe topics.
4. When in doubt, downgrade from strong to weak or remove entirely.
5. Return ONLY valid JSON."""

# ---

QUERY_GENERATION_SYSTEM = """You are a search query expert for product discovery.
You convert profile signals and gift constraints into highly effective product search queries
that will find real, purchasable gifts on e-commerce platforms."""

QUERY_GENERATION_PROMPT = """Generate 3-4 specific product search queries to find gifts for this contact.

CONTACT:
- Name: {name}
- Role: {role}
- Location: {location}

FILTERED PROFILE SIGNALS:
- Strong: {strong_signals}
- Weak: {weak_signals}

GIFT CONTEXT:
- Occasion: {occasion}
- Relationship: {relationship_type}
- Budget: {currency} {budget_min} - {budget_max}
- Country: {country}

Return as JSON:
{{
    "queries": [
        "query string 1",
        "query string 2",
        "query string 3",
        "query string 4"
    ],
    "query_reasoning": [
        "why this query targets a specific signal",
        "why this query covers a different angle",
        "why this broader query provides fallback options",
        "why this query explores another interest"
    ]
}}

RULES:
1. Each query should target a DIFFERENT signal or angle.
2. Include the country and approximate budget in each query (e.g., "under 5000 INR").
3. Use terms like "buy", "gift", "premium" to find purchasable products (not articles).
4. At least one query should be broader/safer as a fallback.
5. Make queries specific enough to find real products (e.g., "cricket themed desk accessory gift India under 5000 INR" not just "cricket gift").
6. Target e-commerce results: include store hints like "buy online" or "amazon flipkart".
7. Return ONLY valid JSON."""

# ---

GIFT_RANKING_SYSTEM = """You are an expert corporate gifting consultant.
You rank gift options based on relevance to the recipient's profile, appropriateness for the occasion
and relationship, budget fit, and overall thoughtfulness.
You explain your reasoning clearly and honestly flag any assumptions."""

GIFT_RANKING_PROMPT = """Rank the following product candidates as gifts for this contact.

CONTACT:
- Name: {name}
- Role: {role}
- Company: {company}
- Location: {location}

PROFILE SIGNALS:
- Strong: {strong_signals}
- Weak: {weak_signals}

GIFT CONTEXT:
- Occasion: {occasion}
- Relationship: {relationship_type}
- Business goal: {business_goal}
- Budget: {currency} {budget_min} - {budget_max}

PRODUCT CANDIDATES:
{products}

Select and rank the TOP 3 best gifts. Return as JSON:
{{
    "ranked_gifts": [
        {{
            "rank": 1,
            "gift_name": "product name",
            "product_url": "url",
            "store": "store name",
            "estimated_price": "price with currency",
            "why_this_gift": "clear explanation of why this gift suits the contact",
            "personalisation_reasoning": "which specific profile signals led to this choice",
            "confidence_score": 0.85,
            "risk_level": "low/medium/high",
            "assumptions": ["list of assumptions made"]
        }}
    ]
}}

RANKING CRITERIA (in order of importance):
1. Relevance to the recipient's genuine interests (strong signals preferred)
2. Appropriateness for the occasion and professional relationship
3. Budget fit (within range)
4. Availability in the recipient's country
5. Thoughtfulness and uniqueness

RULES:
1. Only include products from the candidates list — do NOT invent products.
2. Use the exact URLs from the candidates.
3. If a product seems like a poor fit, don't include it — return fewer than 3 if needed.
4. Lower confidence_score when relying on weak signals or assumptions.
5. Set risk_level to "high" if the gift could be seen as inappropriate.
6. Return ONLY valid JSON."""

# ---

MESSAGE_GENERATION_SYSTEM = """You are a professional communication expert who writes warm, concise gift messages.
Your messages are genuine, not generic — they reference specific things about the recipient.
You keep messages professional yet personable, appropriate for business relationships."""

MESSAGE_GENERATION_PROMPT = """Generate a short, personalised gift message for each of these gift recommendations.

CONTACT:
- Name: {name}
- Role: {role}
- Company: {company}
- Occasion: {occasion}
- Relationship: {relationship_type}
- Last interaction: {last_interaction}
- Business goal: {business_goal}

GIFTS:
{gifts}

PROFILE SIGNALS USED:
{signals}

For each gift, generate a personalised message (2-4 sentences). Return as JSON:
{{
    "messages": [
        {{
            "rank": 1,
            "personalised_message": "the warm, professional message to send with the gift"
        }}
    ]
}}

RULES:
1. Reference something specific about the recipient (a shared interest, their work, the occasion).
2. Keep it warm but professional — appropriate for a {relationship_type}.
3. Don't be generic ("Hope you enjoy this gift"). Be specific and genuine.
4. Don't be overly personal or presumptuous.
5. 2-4 sentences maximum.
6. Return ONLY valid JSON."""
