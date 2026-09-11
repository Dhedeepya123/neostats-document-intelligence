from __future__ import annotations

import re
from typing import Any


DEFAULT_TOLERANCE = 0.01


def get_field_value(
    fields: dict[str, Any],
    aliases: list[str],
) -> Any:
    """
    Return the first available value from the supplied field aliases.

    Gemini may use slightly different field names depending on the
    document. This helper keeps validation tolerant of those names.
    """
    for alias in aliases:
        if alias in fields:
            field = fields[alias]

            if isinstance(field, dict):
                return field.get("value")

            return field

    return None


def to_number(value: Any) -> float | None:
    """
    Convert common financial representations into numbers.

    Supports:
    - integers/floats
    - numeric strings
    - comma-separated values
    - currency symbols
    - parentheses for negative values
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        text = value.strip()

        if not text:
            return None

        # Treat common missing-value markers as unavailable.
        if text.lower() in {
            "null",
            "none",
            "n/a",
            "na",
            "-",
            "—",
            "–",
        }:
            return None

        negative = False

        if text.startswith("(") and text.endswith(")"):
            negative = True
            text = text[1:-1].strip()

        # Remove common currency symbols and separators.
        text = (
            text.replace(",", "")
            .replace("₹", "")
            .replace("$", "")
            .replace("RM", "")
            .replace("£", "")
            .replace("€", "")
            .strip()
        )

        # Keep digits, decimal point and minus sign.
        text = re.sub(r"[^0-9.\-]", "", text)

        if not text or text in {"-", ".", "-."}:
            return None

        try:
            number = float(text)
        except ValueError:
            return None

        return -number if negative else number

    return None


def calculate_variance(
    calculated_value: float | None,
    reported_value: float | None,
) -> float | None:
    if calculated_value is None or reported_value is None:
        return None

    return abs(calculated_value - reported_value)


def check_values(
    name: str,
    formula: str,
    operands: dict[str, Any],
    calculated_value: float | None,
    reported_value: float | None,
    tolerance: float,
) -> dict[str, Any]:
    """
    Create a standard validation check.

    PASS:
        Both values exist and their difference is within tolerance.

    FAIL:
        Both values exist but differ beyond tolerance.

    NOT_APPLICABLE:
        Required values are missing.
    """
    variance = calculate_variance(
        calculated_value,
        reported_value,
    )

    if calculated_value is None or reported_value is None:
        status = "NOT_APPLICABLE"
    elif variance <= tolerance:
        status = "PASS"
    else:
        status = "FAIL"

    return {
        "name": name,
        "formula": formula,
        "operands": operands,
        "calculated_value": calculated_value,
        "reported_value": reported_value,
        "variance": variance,
        "status": status,
    }


def create_not_applicable_check(
    name: str,
    formula: str,
    operands: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "formula": formula,
        "operands": operands,
        "calculated_value": None,
        "reported_value": None,
        "variance": None,
        "status": "NOT_APPLICABLE",
    }


# ============================================================
# INVOICE VALIDATION
# ============================================================

def validate_invoice(
    extracted_data: dict,
    tolerance: float,
) -> list[dict[str, Any]]:
    fields = extracted_data.get("fields", {})
    line_items = extracted_data.get("line_items", [])

    checks: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # 1. Line item quantity × unit price = line total
    # --------------------------------------------------------

    for index, item in enumerate(line_items, start=1):
        if not isinstance(item, dict):
            continue

        quantity = to_number(item.get("quantity"))
        unit_price = to_number(item.get("unit_price"))
        line_total = to_number(item.get("line_total"))

        if (
            quantity is None
            and unit_price is None
            and line_total is None
        ):
            continue

        calculated_line_total = (
            quantity * unit_price
            if quantity is not None and unit_price is not None
            else None
        )

        description = item.get("description") or f"Line item {index}"

        checks.append(
            check_values(
                name=f"Invoice: Line item total - {description}",
                formula="quantity × unit_price ≈ line_total",
                operands={
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                },
                calculated_value=calculated_line_total,
                reported_value=line_total,
                tolerance=tolerance,
            )
        )

    # --------------------------------------------------------
    # 2. Sum of line items = subtotal
    # --------------------------------------------------------

    subtotal = to_number(
        get_field_value(
            fields,
            [
                "subtotal",
                "sub_total",
                "invoice_subtotal",
                "net_amount",
                "taxable_amount",
                "gst_taxable_amount",
            ],
        )
    )

    line_totals: list[float] = []

    for item in line_items:
        if not isinstance(item, dict):
            continue

        line_total = to_number(item.get("line_total"))

        if line_total is not None:
            line_totals.append(line_total)

    calculated_subtotal = (
        sum(line_totals)
        if line_totals
        else None
    )

    checks.append(
        check_values(
            name="Invoice: Line items equal subtotal",
            formula="sum(line_item_totals) ≈ subtotal",
            operands={
                "line_item_totals": line_totals,
                "subtotal": subtotal,
            },
            calculated_value=calculated_subtotal,
            reported_value=subtotal,
            tolerance=tolerance,
        )
    )

    # --------------------------------------------------------
    # 3. Taxable amount + tax = total
    # --------------------------------------------------------

    taxable_amount = to_number(
        get_field_value(
            fields,
            [
                "gst_taxable_amount",
                "taxable_amount",
                "taxable_value",
                "taxable_subtotal",
            ],
        )
    )

    tax_amount = to_number(
        get_field_value(
            fields,
            [
                "gst_amount",
                "tax_amount",
                "tax",
                "total_tax",
                "vat_amount",
            ],
        )
    )

    invoice_total = to_number(
        get_field_value(
            fields,
            [
                "grand_total",
                "total",
                "invoice_total",
                "total_amount",
                "amount_due",
                "total_due",
                "net_total",
            ],
        )
    )

    calculated_tax_total = (
        taxable_amount + tax_amount
        if taxable_amount is not None and tax_amount is not None
        else None
    )

    checks.append(
        check_values(
            name="Invoice: Taxable amount plus tax",
            formula="taxable_amount + tax ≈ total",
            operands={
                "taxable_amount": taxable_amount,
                "tax": tax_amount,
                "total": invoice_total,
            },
            calculated_value=calculated_tax_total,
            reported_value=invoice_total,
            tolerance=tolerance,
        )
    )

    # --------------------------------------------------------
    # 4. Payment - total = change
    # --------------------------------------------------------

    payment_amount = to_number(
        get_field_value(
            fields,
            [
                "card_payment",
                "cash_payment",
                "payment_amount",
                "amount_paid",
                "paid_amount",
                "total_paid",
            ],
        )
    )

    change_amount = to_number(
        get_field_value(
            fields,
            [
                "change",
                "change_amount",
                "balance_returned",
            ],
        )
    )

    calculated_change = (
        payment_amount - invoice_total
        if payment_amount is not None and invoice_total is not None
        else None
    )

    checks.append(
        check_values(
            name="Invoice: Payment less total equals change",
            formula="payment - total ≈ change",
            operands={
                "payment": payment_amount,
                "total": invoice_total,
                "change": change_amount,
            },
            calculated_value=calculated_change,
            reported_value=change_amount,
            tolerance=tolerance,
        )
    )

    # --------------------------------------------------------
    # 5. Subtotal + tax - discount = total
    # --------------------------------------------------------

    discount = to_number(
        get_field_value(
            fields,
            [
                "discount",
                "discount_amount",
                "total_discount",
                "invoice_discount",
            ],
        )
    )

    calculated_invoice_total = (
        subtotal + tax_amount - (discount or 0)
        if subtotal is not None and tax_amount is not None
        else None
    )

    checks.append(
        check_values(
            name="Invoice: Subtotal plus tax less discount",
            formula="subtotal + tax - discount ≈ total",
            operands={
                "subtotal": subtotal,
                "tax": tax_amount,
                "discount": discount,
                "total": invoice_total,
            },
            calculated_value=calculated_invoice_total,
            reported_value=invoice_total,
            tolerance=tolerance,
        )
    )

    return checks


# ============================================================
# BALANCE SHEET VALIDATION
# ============================================================

def validate_balance_sheet(
    extracted_data: dict,
    tolerance: float,
) -> list[dict[str, Any]]:
    fields = extracted_data.get("fields", {})

    checks: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # Gemini commonly extracts financial statement values as:
    #
    # total_assets_31_mar_17
    # total_assets_31_mar_16
    #
    # total_capital_and_liabilities_31_mar_17
    # total_capital_and_liabilities_31_mar_16
    #
    # Validate each period independently.
    # --------------------------------------------------------

    asset_periods: set[str] = set()
    liability_periods: set[str] = set()

    for key in fields:
        if key.startswith("total_assets_"):
            period = key[len("total_assets_"):]
            if period:
                asset_periods.add(period)

        if key.startswith("total_capital_and_liabilities_"):
            period = key[
                len("total_capital_and_liabilities_"):
            ]
            if period:
                liability_periods.add(period)

    common_periods = sorted(
        asset_periods.intersection(liability_periods)
    )

    # --------------------------------------------------------
    # Period-specific validation
    # --------------------------------------------------------

    if common_periods:
        for period in common_periods:
            total_assets = to_number(
                get_field_value(
                    fields,
                    [
                        f"total_assets_{period}",
                    ],
                )
            )

            total_capital_and_liabilities = to_number(
                get_field_value(
                    fields,
                    [
                        f"total_capital_and_liabilities_{period}",
                    ],
                )
            )

            checks.append(
                check_values(
                    name=(
                        "Balance sheet: Assets equal capital "
                        f"and liabilities ({period})"
                    ),
                    formula=(
                        "total_assets ≈ "
                        "total_capital_and_liabilities"
                    ),
                    operands={
                        "period": period,
                        "total_assets": total_assets,
                        "total_capital_and_liabilities":
                            total_capital_and_liabilities,
                    },
                    calculated_value=total_assets,
                    reported_value=total_capital_and_liabilities,
                    tolerance=tolerance,
                )
            )

        return checks

    # --------------------------------------------------------
    # Generic fallback
    # --------------------------------------------------------

    total_assets = to_number(
        get_field_value(
            fields,
            [
                "total_assets",
                "assets_total",
            ],
        )
    )

    total_capital_and_liabilities = to_number(
        get_field_value(
            fields,
            [
                "total_capital_and_liabilities",
                "total_liabilities_and_equity",
                "total_liabilities_and_capital",
            ],
        )
    )

    if (
        total_assets is not None
        or total_capital_and_liabilities is not None
    ):
        checks.append(
            check_values(
                name=(
                    "Balance sheet: Assets equal capital "
                    "and liabilities"
                ),
                formula=(
                    "total_assets ≈ "
                    "total_capital_and_liabilities"
                ),
                operands={
                    "total_assets": total_assets,
                    "total_capital_and_liabilities":
                        total_capital_and_liabilities,
                },
                calculated_value=total_assets,
                reported_value=total_capital_and_liabilities,
                tolerance=tolerance,
            )
        )
    else:
        checks.append(
            create_not_applicable_check(
                name=(
                    "Balance sheet: Assets equal capital "
                    "and liabilities"
                ),
                formula=(
                    "total_assets ≈ "
                    "total_capital_and_liabilities"
                ),
                operands={
                    "total_assets": None,
                    "total_liabilities": None,
                    "total_equity": None,
                    "total_capital": None,
                },
            )
        )

    return checks


# ============================================================
# PROFIT & LOSS VALIDATION
# ============================================================

def validate_profit_and_loss(
    extracted_data: dict,
    tolerance: float,
) -> list[dict[str, Any]]:
    fields = extracted_data.get("fields", {})

    def get_periods(prefixes: list[str]) -> list[str]:
        periods: set[str] = set()

        for key in fields:
            for prefix in prefixes:
                if key.startswith(prefix + "_"):
                    period = key[len(prefix) + 1:]

                    if period:
                        periods.add(period)

        return sorted(periods)

    def period_value(
        prefixes: list[str],
        period: str,
    ) -> Any:
        for prefix in prefixes:
            aliases = [
                f"{prefix}_{period}",
                prefix,
            ]

            value = get_field_value(
                fields,
                aliases,
            )

            if value is not None:
                return value

        return None

    periods = get_periods(
        [
            "income_interest_earned",
            "income_other_income",
            "total_income",
            "expenditure_interest_expended",
            "expenditure_operating_expenses",
            "expenditure_provisions_and_contingencies",
            "total_expenditure",
            "net_profit_for_the_year",
            "less_minority_interest",
            "consolidated_profit_for_the_year_attributable_to_group",
            "balance_in_profit_and_loss_account_brought_forward",
            "total_profit",
            "total_appropriations",
        ]
    )

    checks: list[dict[str, Any]] = []

    if not periods:
        periods = [""]

    for period in periods:
        suffix = f" ({period})" if period else ""

        # ----------------------------------------------------
        # 1. Total income
        # ----------------------------------------------------

        interest_earned = to_number(
            period_value(
                [
                    "income_interest_earned",
                    "interest_earned",
                ],
                period,
            )
        )

        other_income = to_number(
            period_value(
                [
                    "income_other_income",
                    "other_income",
                ],
                period,
            )
        )

        total_income = to_number(
            period_value(
                [
                    "total_income",
                ],
                period,
            )
        )

        calculated_income = (
            interest_earned + other_income
            if interest_earned is not None
            and other_income is not None
            else None
        )

        checks.append(
            check_values(
                name=(
                    "P&L: Total income reconciliation"
                    f"{suffix}"
                ),
                formula=(
                    "interest_earned + other_income "
                    "≈ total_income"
                ),
                operands={
                    "period": period or None,
                    "interest_earned": interest_earned,
                    "other_income": other_income,
                    "total_income": total_income,
                },
                calculated_value=calculated_income,
                reported_value=total_income,
                tolerance=tolerance,
            )
        )

        # ----------------------------------------------------
        # 2. Total expenditure
        # ----------------------------------------------------

        interest_expended = to_number(
            period_value(
                [
                    "expenditure_interest_expended",
                    "interest_expended",
                ],
                period,
            )
        )

        operating_expenses = to_number(
            period_value(
                [
                    "expenditure_operating_expenses",
                    "operating_expenses",
                ],
                period,
            )
        )

        provisions = to_number(
            period_value(
                [
                    "expenditure_provisions_and_contingencies",
                    "provisions_and_contingencies",
                    "provisions",
                ],
                period,
            )
        )

        total_expenditure = to_number(
            period_value(
                [
                    "total_expenditure",
                ],
                period,
            )
        )

        expenditure_values = [
            interest_expended,
            operating_expenses,
            provisions,
        ]

        calculated_expenditure = (
            sum(expenditure_values)
            if all(
                value is not None
                for value in expenditure_values
            )
            else None
        )

        checks.append(
            check_values(
                name=(
                    "P&L: Total expenditure reconciliation"
                    f"{suffix}"
                ),
                formula=(
                    "interest_expended + operating_expenses + "
                    "provisions_and_contingencies "
                    "≈ total_expenditure"
                ),
                operands={
                    "period": period or None,
                    "interest_expended": interest_expended,
                    "operating_expenses": operating_expenses,
                    "provisions_and_contingencies":
                        provisions,
                    "total_expenditure": total_expenditure,
                },
                calculated_value=calculated_expenditure,
                reported_value=total_expenditure,
                tolerance=tolerance,
            )
        )

        # ----------------------------------------------------
        # 3. Income - expenditure = net profit
        # ----------------------------------------------------

        net_profit_for_year = to_number(
            period_value(
                [
                    "net_profit_for_the_year",
                ],
                period,
            )
        )

        calculated_net_profit = (
            total_income - total_expenditure
            if total_income is not None
            and total_expenditure is not None
            else None
        )

        checks.append(
            check_values(
                name=(
                    "P&L: Income less expenditure equals "
                    f"net profit{suffix}"
                ),
                formula=(
                    "total_income - total_expenditure "
                    "≈ net_profit_for_the_year"
                ),
                operands={
                    "period": period or None,
                    "total_income": total_income,
                    "total_expenditure": total_expenditure,
                    "reported_net_profit":
                        net_profit_for_year,
                },
                calculated_value=calculated_net_profit,
                reported_value=net_profit_for_year,
                tolerance=tolerance,
            )
        )

        # ----------------------------------------------------
        # 4. Net profit attributable to group
        # ----------------------------------------------------

        minority_interest = to_number(
            period_value(
                [
                    "less_minority_interest",
                    "minority_interest",
                ],
                period,
            )
        )

        attributable_profit = to_number(
            period_value(
                [
                    (
                        "consolidated_profit_for_the_year_"
                        "attributable_to_group"
                    ),
                    "net_profit_attributable_to_group",
                ],
                period,
            )
        )

        profit_before_minority = (
            net_profit_for_year
            if net_profit_for_year is not None
            else calculated_net_profit
        )

        calculated_attributable_profit = (
            profit_before_minority - minority_interest
            if profit_before_minority is not None
            and minority_interest is not None
            else None
        )

        checks.append(
            check_values(
                name=(
                    "P&L: Net profit attributable to group"
                    f"{suffix}"
                ),
                formula=(
                    "profit_before_minority - "
                    "minority_interest "
                    "≈ attributable_profit"
                ),
                operands={
                    "period": period or None,
                    "profit_before_minority":
                        profit_before_minority,
                    "minority_interest":
                        minority_interest,
                    "net_profit_attributable_to_group":
                        attributable_profit,
                },
                calculated_value=calculated_attributable_profit,
                reported_value=attributable_profit,
                tolerance=tolerance,
            )
        )

        # ----------------------------------------------------
        # 5. Total available for appropriation
        # ----------------------------------------------------

        profit_brought_forward = to_number(
            period_value(
                [
                    (
                        "balance_in_profit_and_loss_account_"
                        "brought_forward"
                    ),
                    "profit_brought_forward",
                    "brought_forward_profit",
                    "profit_brought_forward_from_previous_year",
                ],
                period,
            )
        )

        total_profit = to_number(
            period_value(
                [
                    "total_profit",
                    "total_available",
                    "total_available_for_appropriation",
                    "total_available_for_appropriations",
                ],
                period,
            )
        )

        current_profit = to_number(
            period_value(
                [
                    (
                        "consolidated_profit_for_the_year_"
                        "attributable_to_group"
                    ),
                    "net_profit_for_the_year",
                    "current_profit",
                    "profit_for_current_year",
                    "current_year_profit",
                    "current_profit_for_the_year",
                ],
                period,
            )
        )

        calculated_total_available = (
            current_profit + profit_brought_forward
            if current_profit is not None
            and profit_brought_forward is not None
            else None
        )

        checks.append(
            check_values(
                name=(
                    "P&L: Total available for appropriation"
                    f"{suffix}"
                ),
                formula=(
                    "current_profit + profit_brought_forward "
                    "≈ total_profit"
                ),
                operands={
                    "period": period or None,
                    "current_profit": current_profit,
                    "profit_brought_forward":
                        profit_brought_forward,
                    "total_available": total_profit,
                },
                calculated_value=calculated_total_available,
                reported_value=total_profit,
                tolerance=tolerance,
            )
        )

    return checks


# ============================================================
# CASH FLOW VALIDATION
# ============================================================

def validate_cash_flow(
    extracted_data: dict,
    tolerance: float,
) -> list[dict[str, Any]]:
    fields = extracted_data.get("fields", {})

    checks: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # Identify period-specific fields.
    # --------------------------------------------------------

    prefixes = [
        "net_cash_from_operating_activities",
        "net_cash_from_investing_activities",
        "net_cash_from_financing_activities",
        "net_increase_in_cash",
        "opening_cash_balance",
        "closing_cash_balance",
    ]

    periods: set[str] = set()

    for key in fields:
        for prefix in prefixes:
            if key.startswith(prefix + "_"):
                period = key[len(prefix) + 1:]

                if period:
                    periods.add(period)

    period_list = sorted(periods)

    if not period_list:
        period_list = [""]

    def period_value(
        aliases: list[str],
        period: str,
    ) -> Any:
        expanded_aliases: list[str] = []

        for alias in aliases:
            if period:
                expanded_aliases.append(
                    f"{alias}_{period}"
                )

            expanded_aliases.append(alias)

        return get_field_value(
            fields,
            expanded_aliases,
        )

    for period in period_list:
        suffix = f" ({period})" if period else ""

        # ----------------------------------------------------
        # Operating cash flow
        # ----------------------------------------------------

        operating = to_number(
            period_value(
                [
                    "net_cash_from_operating_activities",
                    "cash_from_operating_activities",
                    "operating_cash_flow",
                    "net_cash_operating",
                ],
                period,
            )
        )

        # ----------------------------------------------------
        # Investing cash flow
        # ----------------------------------------------------

        investing = to_number(
            period_value(
                [
                    "net_cash_from_investing_activities",
                    "cash_from_investing_activities",
                    "investing_cash_flow",
                    "net_cash_investing",
                ],
                period,
            )
        )

        # ----------------------------------------------------
        # Financing cash flow
        # ----------------------------------------------------

        financing = to_number(
            period_value(
                [
                    "net_cash_from_financing_activities",
                    "cash_from_financing_activities",
                    "financing_cash_flow",
                    "net_cash_financing",
                ],
                period,
            )
        )

        # ----------------------------------------------------
        # Foreign exchange / other adjustment
        # ----------------------------------------------------

        foreign_exchange = to_number(
            period_value(
                [
                    "effect_of_exchange_rate_changes",
                    "effect_of_exchange_rate_changes_on_cash",
                    "foreign_exchange_effect",
                    "exchange_rate_effect",
                    "fx_effect",
                ],
                period,
            )
        )

        net_increase = to_number(
            period_value(
                [
                    "net_increase_in_cash",
                    "net_increase_decrease_in_cash",
                    "net_change_in_cash",
                    "increase_decrease_in_cash",
                ],
                period,
            )
        )

        cash_flow_components = [
            operating,
            investing,
            financing,
        ]

        if foreign_exchange is not None:
            cash_flow_components.append(
                foreign_exchange
            )

        calculated_net_increase = (
            sum(cash_flow_components)
            if all(
                value is not None
                for value in cash_flow_components
            )
            else None
        )

        checks.append(
            check_values(
                name=(
                    "Cash flow: Operating + investing + "
                    f"financing equals net increase{suffix}"
                ),
                formula=(
                    "operating + investing + financing "
                    "+ optional FX ≈ net increase"
                ),
                operands={
                    "period": period or None,
                    "operating": operating,
                    "investing": investing,
                    "financing": financing,
                    "foreign_exchange": foreign_exchange,
                    "net_increase": net_increase,
                },
                calculated_value=calculated_net_increase,
                reported_value=net_increase,
                tolerance=tolerance,
            )
        )

        # ----------------------------------------------------
        # Opening + net increase = closing
        # ----------------------------------------------------

        opening_cash = to_number(
            period_value(
                [
                    "opening_cash_balance",
                    "cash_and_cash_equivalents_at_beginning",
                    "cash_at_beginning_of_period",
                    "cash_and_cash_equivalents_beginning",
                    "beginning_cash_balance",
                ],
                period,
            )
        )

        closing_cash = to_number(
            period_value(
                [
                    "closing_cash_balance",
                    "cash_and_cash_equivalents_at_end",
                    "cash_at_end_of_period",
                    "cash_and_cash_equivalents_ending",
                    "ending_cash_balance",
                ],
                period,
            )
        )

        cash_acquired = to_number(
            period_value(
                [
                    "cash_acquired_on_acquisition",
                    "cash_and_cash_equivalents_acquired",
                    "cash_acquired",
                ],
                period,
            )
        )

        other_adjustments = to_number(
            period_value(
                [
                    "other_adjustments",
                    "other_cash_adjustments",
                ],
                period,
            )
        )

        adjustments = 0.0

        if cash_acquired is not None:
            adjustments += cash_acquired

        if other_adjustments is not None:
            adjustments += other_adjustments

        calculated_closing_cash = (
            opening_cash
            + net_increase
            + adjustments
            if opening_cash is not None
            and net_increase is not None
            else None
        )

        checks.append(
            check_values(
                name=(
                    "Cash flow: Opening cash plus net change "
                    f"equals closing cash{suffix}"
                ),
                formula=(
                    "opening_cash + net_increase "
                    "+ optional adjustments ≈ closing_cash"
                ),
                operands={
                    "period": period or None,
                    "opening_cash": opening_cash,
                    "net_increase": net_increase,
                    "cash_acquired": cash_acquired,
                    "other_adjustments":
                        other_adjustments,
                    "closing_cash": closing_cash,
                },
                calculated_value=calculated_closing_cash,
                reported_value=closing_cash,
                tolerance=tolerance,
            )
        )

    return checks


# ============================================================
# MAIN VALIDATION DISPATCHER
# ============================================================

def validate_financial_data(
    document_type: str,
    extracted_data: dict,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """
    Validate extracted financial data according to document type.
    """

    normalized_type = (
        document_type.strip().lower()
    )

    if normalized_type == "invoice":
        checks = validate_invoice(
            extracted_data,
            tolerance,
        )

    elif normalized_type == "balance_sheet":
        checks = validate_balance_sheet(
            extracted_data,
            tolerance,
        )

    elif normalized_type in {
        "profit_and_loss",
        "profit and loss",
        "profit & loss",
    }:
        checks = validate_profit_and_loss(
            extracted_data,
            tolerance,
        )

    elif normalized_type in {
        "cash_flow",
        "cash flow",
        "cash_flow_statement",
        "cash flow statement",
    }:
        checks = validate_cash_flow(
            extracted_data,
            tolerance,
        )

    else:
        checks = []

    return {
        "checks": checks,
    }