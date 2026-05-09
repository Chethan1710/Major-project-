# =============================================================================
# classifier.py — Rule-based battery grade classification
# Smart Battery Reuse Identification System
# =============================================================================

# ─── Thresholds ───────────────────────────────────────────────────────────────

VOLTAGE_GRADE_A   = 3.5   # V — minimum for Grade A
VOLTAGE_GRADE_B   = 2.8   # V — minimum for Grade B (below this → Grade C)

# Defects that indicate structural or thermal failure
CRITICAL_DEFECTS  = {"swelling", "burn_marks"}


# ─── Recommendations by grade ─────────────────────────────────────────────────

_RECOMMENDATIONS = {
    "A": "Battery is healthy. Safe for reuse in standard applications.",
    "B": "Battery is usable with caution. Monitor temperature and capacity closely.",
    "C": "Battery is not fit for reuse. Dispose of safely per local regulations.",
}


# ─── Main classifier ──────────────────────────────────────────────────────────

def classify_battery(voltage: float, defects: list):
    """
    Assign a reuse grade (A / B / C) based on voltage and detected defects.

    Rules (evaluated in priority order)
    ─────────────────────────────────────────────────────────────────────────
    Grade C — Reject
      • Voltage below 2.8 V
      • Any critical defect (swelling or burn marks) with High severity
      • Any critical defect present alongside ≥ 1 other defect
      • Three or more negative defects detected regardless of type

    Grade A — Healthy
      • Voltage ≥ 3.5 V  AND  (Zero negative defects OR significant positive markers)

    Grade B — Caution
      • Voltage ≥ 2.8 V  AND  at most one negative defect
      • (Fallthrough from above)

    Returns
    -------
    grade          : str   — "A", "B", or "C"
    recommendation : str   — plain-language action statement
    """
    # Separate positive markers from actual defects
    positive_markers = {"healthy_capacity", "stable_voltage", "clean_exterior", "thermal_stable"}
    negative_defects = [d for d in defects if d["key"] not in positive_markers]
    pos_count = len([d for d in defects if d["key"] in positive_markers])

    detected_keys  = {d["key"] for d in negative_defects}
    high_sev_keys  = {d["key"] for d in negative_defects if d.get("severity") == "High"}
    defect_count   = len(negative_defects)

    has_critical      = bool(detected_keys & {"swelling", "burn_marks"})
    has_high_critical = bool(high_sev_keys & {"swelling", "burn_marks"})

    # ── Grade C checks ────────────────────────────────────────────────────────
    if voltage < 2.8:
        return "C", f"Voltage at {voltage:.2f} V — critically below safe threshold. Do not reuse."

    if has_high_critical:
        flagged = ", ".join(d["name"] for d in negative_defects if d["key"] in {"swelling", "burn_marks"})
        return "C", f"High-severity critical defect detected ({flagged}). Do not reuse."

    if has_critical and defect_count >= 2:
        return "C", "Critical defect alongside additional faults. Battery rejected."

    if defect_count >= 3:
        return "C", f"{defect_count} negative defects detected. Battery rejected due to cumulative degradation."

    # ── Grade A check ─────────────────────────────────────────────────────────
    if voltage >= 3.5:
        if defect_count == 0:
            return "A", "Battery is healthy. Safe for reuse in standard applications."
        elif pos_count >= 2:
            return "A", f"Voltage healthy ({voltage:.2f}V) and positive health markers present. Battery is safe for reuse."

    # ── Grade B (remaining passing cases) ────────────────────────────────────
    if voltage >= 2.8:
        if defect_count == 0:
            return "B", f"Voltage at {voltage:.2f} V — below Grade A threshold. Usable with caution."
        else:
            defect_names = ", ".join(d["name"] for d in negative_defects)
            return "B", f"Minor defect detected ({defect_names}). Usable with caution."

    return "C", "Battery is not fit for reuse. Dispose of safely per local regulations."
