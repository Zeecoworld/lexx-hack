"""
Rule-based NLP engine for RightsDesk.

No external API, no API key, no network call — everything here is plain
Python keyword matching and templated responses. This trades some of the
flexibility of an LLM for something that is fast, free, fully offline, and
100% predictable for a live demo.
"""
import re

DISCLAIMER = "This is general information, not legal advice — for a real dispute, speak to a lawyer or your state's legal aid office."

# ---------------------------------------------------------------------------
# 1. "Ask a question" — keyword classifier + templated guidance
# ---------------------------------------------------------------------------

CATEGORIES = {
    "tenancy_deposit": {
        "keywords": ["deposit", "caution fee", "won't return", "keep my money", "refund my deposit"],
        "weight": 2,
        "reply": (
            "A landlord withholding your deposit without a valid reason (unpaid rent, "
            "proven damage beyond normal wear) is a common tenancy dispute.\n\n"
            "Next steps:\n"
            "1. Re-read your tenancy agreement for the deposit/caution-fee clause.\n"
            "2. Put your request in writing (email or letter) and keep a copy.\n"
            "3. Take dated photos of the property's condition if you have them.\n"
            "4. If ignored, report to your state's Tenancy/Rent Tribunal or Small Claims Court — "
            "many claims like this don't need a lawyer."
        ),
    },
    "tenancy_eviction": {
        "keywords": ["evict", "quit notice", "kicked out", "landlord wants me out", "vacate"],
        "weight": 2,
        "reply": (
            "In Nigeria, a landlord generally can't remove you without proper notice — the length "
            "depends on your tenancy type (monthly, yearly) and must go through the courts, not "
            "self-help eviction (locking you out, seizing property).\n\n"
            "Next steps:\n"
            "1. Check what notice period your tenancy agreement requires.\n"
            "2. Ask for any eviction notice in writing.\n"
            "3. Do not leave under threat alone — a landlord needs a court order to physically evict you.\n"
            "4. Contact a tenants' rights desk or lawyer if you feel pressured."
        ),
    },
    "tenancy_general": {
        "keywords": ["landlord", "rent", "tenant", "lease", "apartment", "agent fee", "repairs"],
        "weight": 1,
        "reply": (
            "Tenancy issues (rent, repairs, notice, deposits) are usually governed by your state's "
            "Tenancy Law and your written agreement.\n\n"
            "Next steps:\n"
            "1. Reread your tenancy agreement for the exact clause that applies.\n"
            "2. Document everything in writing with your landlord or agent.\n"
            "3. Keep receipts, photos, and dated messages as evidence.\n"
            "4. Escalate to your state's Tenancy Tribunal if it isn't resolved directly."
        ),
    },
    "consumer_refund": {
        "keywords": ["refund", "faulty", "defective", "refuse to refund", "won't refund", "return my money"],
        "weight": 2,
        "reply": (
            "Under Nigeria's consumer-protection framework (enforced by the FCCPC), you generally have "
            "a right to a repair, replacement, or refund for goods that are faulty or not as described.\n\n"
            "Next steps:\n"
            "1. Ask the seller for their refund/return policy in writing.\n"
            "2. Keep your receipt and any proof the product is faulty (photos, video).\n"
            "3. If refused, file a complaint with the FCCPC (Federal Competition and Consumer "
            "Protection Commission) online.\n"
            "4. For higher-value items, small claims court is also an option."
        ),
    },
    "consumer_general": {
        "keywords": ["store", "product", "warranty", "receipt", "consumer", "purchase", "bought"],
        "weight": 1,
        "reply": (
            "As a consumer you're generally entitled to goods and services that match what was "
            "advertised, and to redress when they don't.\n\n"
            "Next steps:\n"
            "1. Keep proof of purchase and any advertising claims made.\n"
            "2. Raise the issue with the seller in writing first.\n"
            "3. Escalate to the FCCPC if the seller won't resolve it.\n"
            "4. Check if a consumer association in your state can help mediate."
        ),
    },
    "labour_unpaid": {
        "keywords": ["unpaid", "hasn't paid", "haven't been paid", "salary", "owed me", "not paid my"],
        "weight": 2,
        "reply": (
            "Under the Labour Act, an employer is required to pay agreed wages on time; persistent "
            "non-payment is a serious breach of your employment contract.\n\n"
            "Next steps:\n"
            "1. Request the unpaid amount in writing, with dates it was due.\n"
            "2. Keep your employment contract, payslips, and any messages about the delay.\n"
            "3. Escalate to the Ministry of Labour and Employment (NECA/state labour office) if unresolved.\n"
            "4. For persistent breaches, resignation with a claim for owed wages is also an option — "
            "get advice first."
        ),
    },
    "labour_termination": {
        "keywords": ["fired", "terminated", "sacked", "let go", "dismissed"],
        "weight": 2,
        "reply": (
            "Termination should generally follow your contract's notice period or pay in lieu of "
            "notice, and shouldn't be for a discriminatory or retaliatory reason.\n\n"
            "Next steps:\n"
            "1. Ask for the reason for termination in writing.\n"
            "2. Check your contract's notice period and entitlements (leave, final pay).\n"
            "3. Keep all termination correspondence.\n"
            "4. Contact the Ministry of Labour or a labour lawyer if you believe it was unfair."
        ),
    },
    "labour_general": {
        "keywords": ["employer", "employment", "boss", "overtime", "leave", "resignation", "work"],
        "weight": 1,
        "reply": (
            "Most day-to-day workplace disputes trace back to what's in your employment contract "
            "and the Labour Act's baseline protections.\n\n"
            "Next steps:\n"
            "1. Reread your employment contract for the clause in question.\n"
            "2. Raise the issue with HR or your employer in writing.\n"
            "3. Document dates, amounts, and any responses you get.\n"
            "4. Contact the Ministry of Labour and Employment if it isn't resolved internally."
        ),
    },
    "contract_signing": {
        "keywords": ["nda", "non-disclosure", "non compete", "sign", "asked to sign", "before an interview"],
        "weight": 1,
        "reply": (
            "You're not obligated to sign any document — including an NDA — without reading it "
            "fully and understanding what it restricts, especially before you're even hired.\n\n"
            "Next steps:\n"
            "1. Ask for a copy to review before signing (a reasonable request has a right to say no).\n"
            "2. Check what it restricts: only company secrets, or also your ability to work elsewhere?\n"
            "3. Watch for open-ended time limits or overly broad non-compete language.\n"
            "4. If unsure, have someone else read it, or ask for the clause to be narrowed."
        ),
    },
}

FALLBACK_REPLY = (
    "I couldn't match that to a specific tenancy, consumer, or labour issue — try describing it a "
    "bit more (for example: what happened, and who's involved).\n\n"
    "Some things I can help with:\n"
    "1. A landlord/tenant dispute (rent, deposit, eviction, repairs).\n"
    "2. A consumer issue (refunds, faulty goods, warranties).\n"
    "3. A workplace issue (unpaid salary, termination, contracts).\n"
    "4. A document you're being asked to sign (NDA, contract clauses)."
)


def classify_question(text):
    text_l = text.lower()
    best_key, best_score = None, 0
    for key, cat in CATEGORIES.items():
        score = sum(cat["weight"] for kw in cat["keywords"] if kw in text_l)
        if score > best_score:
            best_key, best_score = key, score
    return best_key, best_score


def answer_question(text):
    key, score = classify_question(text)
    if not key or score == 0:
        return FALLBACK_REPLY
    return CATEGORIES[key]["reply"] + "\n\n" + DISCLAIMER


# ---------------------------------------------------------------------------
# 2. "Check a document" — regex/keyword clause-risk detector
# ---------------------------------------------------------------------------

CLAUSE_PATTERNS = [
    (r"\bautomatically renew|auto-renew|auto renew", "medium",
     "Auto-renewal clauses can lock you into another term if you miss the cancellation window — check how much notice you must give to opt out."),
    (r"\bwaive[sd]?\b.{0,40}\bright", "high",
     "This gives up a right you'd otherwise have — make sure you understand exactly what you're waiving before signing."),
    (r"\bunlimited liability|\bno limit(ation)? of liability|\bindemnif", "high",
     "You could be on the hook for costs or damages with no cap — this is worth negotiating or getting reviewed."),
    (r"\bsole discretion\b", "medium",
     "Giving the other party unilateral decision-making power here leaves you little recourse if they act unfavourably."),
    (r"\bwithout (prior )?notice\b", "medium",
     "Being terminated, charged, or changed \"without notice\" leaves you no time to react — check if this can be balanced with a notice period."),
    (r"\bnon-compete|non compete|restrict.{0,20}(from working|employment)", "medium",
     "Non-compete language can limit your ability to work elsewhere — check the time period and geographic scope for how broad it is."),
    (r"\bpenalt(y|ies)|liquidated damages|forfeit", "medium",
     "Penalty or forfeiture clauses can be costly if you break a term — check the amount and what triggers it."),
    (r"\bperpetuity|indefinite(ly)? period|no expiry", "medium",
     "An obligation with no end date (often in confidentiality clauses) can bind you far longer than expected."),
    (r"\bconfidential(ity)?\b", "low",
     "A standard confidentiality clause — reasonable in most agreements, but check what information it actually covers."),
    (r"\bgoverning law\b|\bjurisdiction\b", "low",
     "This sets which country/state's laws and courts apply — worth noting if you and the other party are in different places."),
    (r"\bentire agreement\b", "low",
     "This means promises made outside the written contract (verbally, by email) may not be enforceable — get anything important in writing."),
]

RISK_ORDER = {"high": 0, "medium": 1, "low": 2}


def _split_clauses(text):
    # Split on sentence-ish boundaries and newlines, keep non-trivial chunks.
    parts = re.split(r"(?<=[.;])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def analyze_document(text):
    clauses = _split_clauses(text)
    seen_patterns = set()
    items = []
    for clause in clauses:
        for pattern, risk, why in CLAUSE_PATTERNS:
            if pattern in seen_patterns:
                continue
            if re.search(pattern, clause, re.IGNORECASE):
                excerpt = clause if len(clause) <= 140 else clause[:137] + "…"
                items.append({"excerpt": excerpt, "risk": risk, "why": why})
                seen_patterns.add(pattern)
                break  # one flag per clause is enough

    items.sort(key=lambda i: RISK_ORDER.get(i["risk"], 3))
    if not items:
        return [{
            "excerpt": "No high-risk patterns detected in this text.",
            "risk": "low",
            "why": "This is a keyword-based scan, not a full legal review — always read the whole document yourself or have a lawyer check anything important.",
        }]
    return items[:8]
