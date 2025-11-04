"""
Math calculator service for Islamic financial calculations.

CRITICAL: All financial calculations MUST include mandatory warnings.
"""

from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class MathService:
    """
    Service for Islamic financial calculations.

    CRITICAL WARNING: All calculations include mandatory disclaimers
    advising users to verify with their Marja's official office.

    Supported calculations:
    - Zakat (charity)
    - Khums (one-fifth tax)
    - Inheritance distribution
    """

    def __init__(self):
        """Initialize Math service."""
        pass

    def get_financial_warning(self) -> str:
        """
        Get mandatory warning for all financial calculations.

        CRITICAL: This warning MUST be displayed with every calculation.
        """
        return """
⚠️⚠️⚠️ CRITICAL WARNING ⚠️⚠️⚠️

This calculation is provided for GENERAL GUIDANCE ONLY and may contain errors.

YOU MUST verify this calculation with:
1. Your Marja's official office or website
2. A qualified Islamic financial advisor
3. The latest fatwas from your Marja

Important considerations that may affect the calculation:
- Local inflation rates
- Country-specific exemptions
- Personal circumstances
- Recent fatwa updates
- Currency exchange rates
- Asset valuations

DO NOT rely on this calculation alone for paying Zakat, Khums, or distributing inheritance.

For accurate calculations, please consult:
- Your Marja's official office
- Islamic financial advisor
- Latest published fatwas
"""

    async def calculate_zakat(
        self,
        total_wealth: float,
        currency: str = "USD",
        nisab_value: Optional[float] = None,
    ) -> dict:
        """
        Calculate Zakat (charity).

        CRITICAL: Includes mandatory warning.

        Args:
            total_wealth: Total wealth in specified currency
            currency: Currency code (USD, EUR, IRR, etc.)
            nisab_value: Nisab threshold (optional, uses default if not provided)

        Returns:
            Zakat calculation with mandatory warning
        """
        logger.info(
            "zakat_calculation_requested",
            total_wealth=total_wealth,
            currency=currency,
        )

        # Nisab is approximately 85 grams of gold
        # Default value: ~$5,000 USD (adjust based on current gold prices)
        if nisab_value is None:
            nisab_value = 5000.0  # TODO: Fetch current gold price

        # Zakat rate: 2.5%
        zakat_rate = 0.025

        # Check if wealth exceeds Nisab
        if total_wealth < nisab_value:
            zakat_amount = 0
            is_liable = False
        else:
            zakat_amount = total_wealth * zakat_rate
            is_liable = True

        return {
            "calculation_type": "zakat",
            "total_wealth": total_wealth,
            "currency": currency,
            "nisab_threshold": nisab_value,
            "is_liable_for_zakat": is_liable,
            "zakat_amount": round(zakat_amount, 2),
            "zakat_rate": f"{zakat_rate * 100}%",
            "warning": self.get_financial_warning(),
            "verification_required": True,
            "disclaimer": "This is an approximation. Actual Zakat may vary based on asset types, debts, and specific circumstances.",
        }

    async def calculate_khums(
        self,
        annual_income: float,
        annual_expenses: float,
        currency: str = "USD",
    ) -> dict:
        """
        Calculate Khums (one-fifth tax).

        CRITICAL: Includes mandatory warning.

        Args:
            annual_income: Total income for the year
            annual_expenses: Total necessary expenses for the year
            currency: Currency code

        Returns:
            Khums calculation with mandatory warning
        """
        logger.info(
            "khums_calculation_requested",
            annual_income=annual_income,
            currency=currency,
        )

        # Khums is calculated on surplus income
        surplus = max(0, annual_income - annual_expenses)

        # Khums rate: 20% (one-fifth)
        khums_rate = 0.20

        khums_amount = surplus * khums_rate

        return {
            "calculation_type": "khums",
            "annual_income": annual_income,
            "annual_expenses": annual_expenses,
            "surplus": round(surplus, 2),
            "currency": currency,
            "khums_amount": round(khums_amount, 2),
            "khums_rate": f"{khums_rate * 100}%",
            "warning": self.get_financial_warning(),
            "verification_required": True,
            "disclaimer": "Khums calculation varies by Marja. Some Marjas have different rulings on expenses, exemptions, and calculation date. MUST verify with your Marja.",
        }

    async def calculate_inheritance(
        self,
        estate_value: float,
        heirs: dict,
        currency: str = "USD",
    ) -> dict:
        """
        Calculate Islamic inheritance distribution.

        CRITICAL: Includes mandatory warning and strong verification requirement.

        Args:
            estate_value: Total value of the estate
            heirs: Dictionary of heirs with their relationships
                   e.g., {"sons": 2, "daughters": 1, "wife": 1}
            currency: Currency code

        Returns:
            Inheritance distribution with CRITICAL warning
        """
        logger.info(
            "inheritance_calculation_requested",
            estate_value=estate_value,
            heirs=heirs,
        )

        # This is a HIGHLY simplified calculation
        # Real inheritance is VERY complex and varies by school of thought

        warning = self.get_financial_warning()
        extra_warning = """
🚨 INHERITANCE CALCULATION IS EXTREMELY COMPLEX 🚨

Islamic inheritance law (Fara'id) is one of the most complex areas of Islamic jurisprudence.

This calculation is EXTREMELY SIMPLIFIED and should NOT be used for actual distribution.

MANDATORY REQUIREMENTS:
1. Consult a qualified Islamic scholar BEFORE distribution
2. Verify with your Marja's official fatwa
3. Consider local laws and regulations
4. Account for debts, funeral expenses, and will (up to 1/3)

Factors that affect distribution:
- Number and type of heirs
- Presence of multiple generations
- Gender of heirs
- Whether deceased has surviving parents
- Whether deceased has surviving spouse
- Debts and obligations
- Funeral expenses
- Valid will (up to 1/3 of estate)

DO NOT DISTRIBUTE WITHOUT PROFESSIONAL GUIDANCE.
"""

        return {
            "calculation_type": "inheritance",
            "estate_value": estate_value,
            "currency": currency,
            "heirs": heirs,
            "distribution": {
                "notice": "Simplified calculation only - NOT for actual use",
            },
            "warning": warning,
            "extra_warning": extra_warning,
            "verification_required": True,
            "requires_scholar_consultation": True,
            "disclaimer": "This is a PLACEHOLDER. Real inheritance calculation requires expert consultation and varies significantly by Marja and circumstances.",
        }

    async def simple_calculation(
        self,
        expression: str,
    ) -> dict:
        """
        Perform simple mathematical calculation.

        For non-financial calculations (e.g., "What is 5 * 10?")

        Args:
            expression: Math expression

        Returns:
            Calculation result
        """
        logger.info(
            "simple_calculation_requested",
            expression=expression[:50],
        )

        try:
            # SECURITY: Use safe evaluation (don't use eval!)
            # TODO: Implement safe math expression parser
            # For now, return placeholder

            return {
                "calculation_type": "simple",
                "expression": expression,
                "result": "Calculation not implemented",
                "note": "Simple calculations coming soon",
            }

        except Exception as e:
            logger.error(
                "calculation_failed",
                expression=expression[:50],
                error=str(e),
            )
            return {
                "calculation_type": "simple",
                "expression": expression,
                "error": str(e),
            }
