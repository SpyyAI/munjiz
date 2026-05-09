"""
Mock compliance services for Munjiz mortgage demo.

⚠️ THESE ARE FAKE DEMO CHECKS — NOT REAL INTEGRATIONS.
Every function returns deterministic-or-pseudo-random fabricated data based on the
applicant profile, clearly labelled `demo: True` and `source: "mock_*"`.

Real production integrations would replace these modules with adapters to:
  - SIMAH / Bayan
  - SDAIA / Yakeen
  - ABD (Authority of Persons with Disability)
  - Sakani housing portal
  - البورصة العقارية (Real Estate Exchange)

For the demo, we never call those services. We never store any data we couldn't
have invented. Every output carries a DEMO marker.
"""
from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Deterministic randomness — same applicant gets same fake data every run
# ---------------------------------------------------------------------------
def _seed_for(applicant_id: str) -> random.Random:
    h = int(hashlib.sha256(applicant_id.encode()).hexdigest(), 16)
    return random.Random(h)


# ---------------------------------------------------------------------------
# 1. SIMAH-style credit check (used by Sara)
# ---------------------------------------------------------------------------
@dataclass
class SimahMockResult:
    demo: bool
    source: str
    applicant_id: str
    credit_score: int            # 300 – 900
    debt_burden_ratio: float     # 0.00 – 1.00 current DBR
    late_payments_12m: int
    open_obligations_count: int
    total_monthly_obligations_sar: int
    risk_band: str               # "low" | "medium" | "high"
    raw_marker: str = "MOCK · NOT A REAL SIMAH CALL"


def fetch_simah(applicant_id: str, applicant_profile: dict) -> SimahMockResult:
    rng = _seed_for(applicant_id + ":simah")
    salary = applicant_profile.get("monthly_salary_sar", 15000)
    existing_debt = applicant_profile.get("existing_monthly_obligations_sar", 0)

    score = rng.randint(540, 880)
    if existing_debt / max(salary, 1) > 0.4:
        score -= 80
    score = max(300, min(900, score))

    band = "low" if score >= 720 else "medium" if score >= 620 else "high"
    return SimahMockResult(
        demo=True,
        source="mock_simah",
        applicant_id=applicant_id,
        credit_score=score,
        debt_burden_ratio=round(existing_debt / max(salary, 1), 2),
        late_payments_12m=rng.choice([0, 0, 0, 1, 2]),
        open_obligations_count=rng.randint(1, 4),
        total_monthly_obligations_sar=existing_debt,
        risk_band=band,
    )


# ---------------------------------------------------------------------------
# 2. SDAIA-style identity verification (used by Fahad)
# ---------------------------------------------------------------------------
@dataclass
class SdaiaMockResult:
    demo: bool
    source: str
    applicant_id: str
    id_status: str               # "valid" | "expired" | "flagged"
    id_match_personal_info: bool
    is_adult: bool
    residency_status: str        # "citizen" | "resident_valid" | "resident_expired"
    travel_ban_demo: bool
    legal_blockers: list[str]
    raw_marker: str = "MOCK · NOT A REAL SDAIA / YAKEEN CALL"


def fetch_sdaia(applicant_id: str, applicant_profile: dict) -> SdaiaMockResult:
    rng = _seed_for(applicant_id + ":sdaia")
    nationality = applicant_profile.get("nationality", "saudi")
    return SdaiaMockResult(
        demo=True,
        source="mock_sdaia",
        applicant_id=applicant_id,
        id_status=rng.choice(["valid", "valid", "valid", "valid", "flagged"]),
        id_match_personal_info=True,
        is_adult=True,
        residency_status="citizen" if nationality == "saudi" else "resident_valid",
        travel_ban_demo=False,
        legal_blockers=[],
    )


# ---------------------------------------------------------------------------
# 3. Employer verification (used by Fahad)
# ---------------------------------------------------------------------------
@dataclass
class EmployerMockResult:
    demo: bool
    source: str
    applicant_id: str
    employer_name_declared: str
    employer_name_verified: str
    match_quality: str               # "exact" | "minor_variant" | "different_entity"
    consistent: bool                 # backwards-compat: False ONLY for "different_entity"
    employer_sector: str
    employment_duration_months: int
    declared_salary_sar: int
    verified_salary_sar: int
    salary_variance_pct: float       # ‑0.07 .. +0.07 — independent of name match
    salary_consistent: bool          # True iff salary_variance_pct == 0
    raw_marker: str = "MOCK · BASED ON UPLOADED DOCUMENTS (NOT VERIFIED EXTERNALLY)"


def verify_employer(applicant_id: str, applicant_profile: dict) -> EmployerMockResult:
    rng = _seed_for(applicant_id + ":employer")
    declared = applicant_profile.get("employer_name", "Unknown Co.")
    declared_salary = applicant_profile.get("monthly_salary_sar", 15000)

    # ── Three-tier name match: most cases match exactly, a small minority differ
    # in wording only, and a very small minority is genuinely a different entity.
    roll = rng.random()
    if roll < 0.85:
        match_quality = "exact"
        verified_name = declared
    elif roll < 0.97:
        match_quality = "minor_variant"
        verified_name = declared + " (variant)"
    else:
        match_quality = "different_entity"
        # Substitute industry suffix to flip the entity (e.g. "للتقنية" → "المالية")
        substituted = re.sub(
            r"(للتقنية|للاتصالات|للمقاولات|للتجارة)$", "المالية", declared
        )
        verified_name = substituted if substituted != declared else declared + " المالية"

    # ── Independent salary roll: most matches are clean, occasional small variance.
    salary_variance_pct = rng.choice([0, 0, 0, 0, 0, -0.03, -0.05, -0.07]) / 1.0
    verified_salary = int(declared_salary * (1 + salary_variance_pct))

    return EmployerMockResult(
        demo=True,
        source="mock_employer_verification",
        applicant_id=applicant_id,
        employer_name_declared=declared,
        employer_name_verified=verified_name,
        match_quality=match_quality,
        consistent=(match_quality != "different_entity"),
        employer_sector=applicant_profile.get("employer_sector", "private"),
        employment_duration_months=applicant_profile.get("employment_duration_months", 36),
        declared_salary_sar=declared_salary,
        verified_salary_sar=verified_salary,
        salary_variance_pct=round(salary_variance_pct, 3),
        salary_consistent=(salary_variance_pct == 0),
    )


# ---------------------------------------------------------------------------
# 4. ABD-style support / consent screening (used by Khalid)
# ---------------------------------------------------------------------------
@dataclass
class AbdMockResult:
    demo: bool
    source: str
    applicant_id: str
    support_needs_declared: list[str]   # only fields applicant volunteered
    needs_legal_representative: bool
    needs_extended_consent: bool
    needs_accessibility_support: list[str]   # e.g. ["sign_language_arabic"]
    suggested_bank_pathways: list[str]
    ethical_note: str
    raw_marker: str = "MOCK · ABD-STYLE SCREENING — NEVER A REJECTION FACTOR"


def fetch_abd(applicant_id: str, screening_answers: dict) -> AbdMockResult:
    """
    Read the applicant's voluntary screening responses and translate them into
    bank-side support pathways. NEVER produces a rejection signal.
    """
    needs = []
    accessibility = []
    pathways = []

    if screening_answers.get("needs_general_support"):
        needs.append("general_support_requested")
        pathways.append("assign_relationship_manager")

    if screening_answers.get("needs_legal_representative"):
        needs.append("legal_representative_required")
        pathways.append("involve_legal_advisor_review")

    if screening_answers.get("needs_accessibility"):
        accessibility = screening_answers.get("accessibility_types", ["unspecified"])
        pathways.append("coordinate_with_branch_accessibility_liaison")

    if screening_answers.get("needs_translation"):
        accessibility.append("translation_or_interpretation")
        pathways.append("provide_certified_interpreter")

    if screening_answers.get("needs_independent_advice"):
        pathways.append("recommend_independent_financial_advice_session")

    return AbdMockResult(
        demo=True,
        source="mock_abd_support",
        applicant_id=applicant_id,
        support_needs_declared=needs,
        needs_legal_representative=screening_answers.get("needs_legal_representative", False),
        needs_extended_consent=screening_answers.get("needs_extended_consent", False),
        needs_accessibility_support=accessibility,
        suggested_bank_pathways=pathways,
        ethical_note=(
            "إجابات هذا الفحص تُستخدَم فقط لتوفير دعم وموافقة مناسبَين، "
            "ولا تُؤثِّر بأيّ حال على قرار الجدارة الائتمانية أو الموافقة على التمويل."
        ),
    )


# ---------------------------------------------------------------------------
# 5. Sakani-style listed property lookup (used by Nora — path A)
# ---------------------------------------------------------------------------
@dataclass
class SakaniMockResult:
    demo: bool
    source: str
    property_id: str
    found: bool
    project_name: str
    unit_type: str
    listed_price_sar: int
    handover_status: str            # "ready" | "off_plan" | "under_construction"
    discrepancy_with_declared_pct: Optional[float]
    raw_marker: str = "MOCK · NOT A REAL SAKANI LOOKUP"


def fetch_sakani(property_id: str, declared_price_sar: int) -> SakaniMockResult:
    rng = _seed_for("sakani:" + property_id)
    listed = int(declared_price_sar * rng.uniform(0.92, 1.08))
    discrepancy = (declared_price_sar - listed) / max(listed, 1) * 100
    return SakaniMockResult(
        demo=True,
        source="mock_sakani",
        property_id=property_id,
        found=True,
        project_name=rng.choice([
            "مشروع نسائم الياسمين",
            "مشروع روضة الرحمانية",
            "مشروع واحات الياسمين",
            "مشروع تلال العقيق",
        ]),
        unit_type=rng.choice(["فلّة دوبلكس", "شقة فاخرة", "تاون هاوس", "فيلا مستقلّة"]),
        listed_price_sar=listed,
        handover_status=rng.choice(["ready", "ready", "off_plan"]),
        discrepancy_with_declared_pct=round(discrepancy, 2),
    )


# ---------------------------------------------------------------------------
# 6. البورصة العقارية + independent valuer (used by Nora — path B)
# ---------------------------------------------------------------------------
@dataclass
class RealEstateExchangeMockResult:
    demo: bool
    source: str
    property_address: str
    exchange_recent_sales_avg_sar: int
    independent_valuer_estimate_sar: int
    fair_value_sar: int                 # average of the two
    declared_value_sar: int
    deviation_from_fair_value_pct: float
    raw_marker: str = "MOCK · NOT A REAL البورصة العقارية / VALUER LOOKUP"


def fetch_real_estate_exchange(
    property_address: str, declared_value_sar: int
) -> RealEstateExchangeMockResult:
    rng = _seed_for("rex:" + property_address)
    exchange = int(declared_value_sar * rng.uniform(0.85, 1.10))
    valuer = int(declared_value_sar * rng.uniform(0.88, 1.06))
    fair = (exchange + valuer) // 2
    deviation = (declared_value_sar - fair) / max(fair, 1) * 100
    return RealEstateExchangeMockResult(
        demo=True,
        source="mock_real_estate_exchange",
        property_address=property_address,
        exchange_recent_sales_avg_sar=exchange,
        independent_valuer_estimate_sar=valuer,
        fair_value_sar=fair,
        declared_value_sar=declared_value_sar,
        deviation_from_fair_value_pct=round(deviation, 2),
    )


# ---------------------------------------------------------------------------
# Convenience: pack all mock results into a dict for prompt context
# ---------------------------------------------------------------------------
def collect_mock_compliance(application: dict) -> dict:
    """
    Run every mock check relevant to the given application and return a single
    dict suitable for embedding into agent prompts. Every value carries DEMO marker.
    """
    applicant = application.get("applicant", {})
    applicant_id = applicant.get("id") or "DEMO-A-000"
    property_info = application.get("property", {})
    screening = application.get("screening_answers", {})

    out = {
        "demo_mode_banner": (
            "⚠️ DEMO MODE — All compliance results below are fabricated for "
            "demonstration. No real SIMAH / SDAIA / ABD / Sakani / "
            "Real Estate Exchange calls were made."
        ),
        "simah":    asdict(fetch_simah(applicant_id, applicant)),
        "sdaia":    asdict(fetch_sdaia(applicant_id, applicant)),
        "employer": asdict(verify_employer(applicant_id, applicant)),
        "abd":      asdict(fetch_abd(applicant_id, screening)),
    }

    # Property valuation depends on whether the property is on Sakani or independent
    if property_info.get("source") == "sakani":
        out["sakani"] = asdict(fetch_sakani(
            property_info.get("property_id", "PROP-000"),
            property_info.get("declared_price_sar", 0),
        ))
    else:
        out["real_estate_exchange"] = asdict(fetch_real_estate_exchange(
            property_info.get("address", "DEMO ADDRESS"),
            property_info.get("declared_price_sar", 0),
        ))

    return out
