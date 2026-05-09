# =============================================================================
# image_processing.py — OpenCV preprocessing pipeline & defect detection
# Smart Battery Reuse Identification System
# =============================================================================

import os
import hashlib

import cv2
import numpy as np


# ─── Image preprocessing pipeline ────────────────────────────────────────────

def preprocess_image(image_input):
    """
    Load a battery image and apply a standard preprocessing pipeline:
      1. Grayscale conversion
      2. Gaussian blur (noise reduction)
      3. ROI extraction  (center 80%)
      4. Canny edge detection

    Returns
    -------
    steps : list[str]
        Human-readable label for each pipeline step (with status tag).
    image_data : dict | None
        Dict of intermediate arrays if the image was loaded successfully,
        otherwise None (all steps are marked as simulated).
    """
    image = None
    if isinstance(image_input, str):
        if os.path.exists(image_input):
            image = cv2.imread(image_input)
    elif isinstance(image_input, np.ndarray):
        image = image_input
    else:
        # Handle bytes-like objects (e.g. from Streamlit file_uploader)
        try:
            image = cv2.imdecode(np.frombuffer(image_input, np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            image = None

    if image is not None:
        steps, image_data = _run_pipeline(image)
    else:
        steps = [
            "Grayscale conversion          [SIMULATED]",
            "Gaussian blur  (kernel 5×5)   [SIMULATED]",
            "ROI extraction  (80% crop)    [SIMULATED]",
            "Edge detection  (Canny)       [SIMULATED]",
        ]
        image_data = None

    return steps, image_data


def _run_pipeline(image: np.ndarray):
    """Execute the four-step preprocessing pipeline on a real image."""
    # Step 1 — Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 2 — Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), sigmaX=0)

    # Step 3 — ROI (central 80% crop)
    h, w = gray.shape
    mh, mw = int(h * 0.10), int(w * 0.10)
    roi = blurred[mh : h - mh, mw : w - mw]

    # Step 4 — Canny edge detection
    edges = cv2.Canny(roi, threshold1=50, threshold2=150)

    steps = [
        "Grayscale conversion          [OK]",
        "Gaussian blur  (kernel 5×5)   [OK]",
        "ROI extraction  (80% crop)    [OK]",
        "Edge detection  (Canny)       [OK]",
    ]
    image_data = {
        "original": image,
        "gray":     gray,
        "blurred":  blurred,
        "roi":      roi,
        "edges":    edges,
    }
    return steps, image_data


# ─── Defect detection ─────────────────────────────────────────────────────────

# Detection threshold: probability above this → defect is flagged
_THRESHOLD   = 0.54
_SEVERITIES  = ["Low", "Moderate", "High"]

_DEFECT_DEFS = [
    ("swelling",     "Swelling"),
    ("corrosion",    "Corrosion"),
    ("burn_marks",   "Burn Marks"),
    ("label_damage", "Label Damage"),
]


def detect_defects(image_data, battery_id: str, voltage: float) -> list:
    """
    Detect four defect types on a battery.

    Strategy
    --------
    - A seed derived from the battery ID drives a reproducible RNG, ensuring
      the same battery always produces the same result.
    - Voltage-based modifiers adjust probabilities to reflect physical reality
      (e.g. deeply discharged cells are more prone to swelling).
    - When a real image is available, pixel-level metrics further refine the
      probabilities before the threshold is applied.

    Returns
    -------
    list of dicts with keys: name, key, detected, severity, confidence
    """
    # Seed RNG from battery ID (MD5 → 32-bit integer)
    seed_val = int(hashlib.md5(battery_id.encode()).hexdigest(), 16) % (2 ** 32)
    rng = np.random.default_rng(seed_val)

    # Base probabilities (0.0 – 1.0) drawn from the seeded RNG
    base = {key: rng.uniform(0.0, 1.0) for key, _ in _DEFECT_DEFS}

    # ── Voltage-based modifiers ──────────────────────────────────────────────
    # Physically motivated: low voltage → over-discharge → structural stress
    if voltage < 2.5:
        base["swelling"]     = max(base["swelling"],     0.82)
        base["burn_marks"]   = max(base["burn_marks"],   0.76)
        base["corrosion"]    = max(base["corrosion"],    0.65)
    elif voltage < 3.0:
        base["swelling"]    += 0.18
        base["corrosion"]   += 0.14
    elif voltage < 3.4:
        base["corrosion"]   += 0.07
        base["label_damage"] += 0.04

    # Cap at 1.0
    base = {k: min(v, 1.0) for k, v in base.items()}

    # ── Pixel-level refinement (only when a real image is available) ─────────
    if image_data is not None:
        base = _refine_with_pixels(base, image_data)

    # ── Apply threshold and compute severity / confidence ────────────────────
    results = []
    for key, name in _DEFECT_DEFS:
        prob     = base[key]
        detected = prob > _THRESHOLD

        if detected:
            # Severity scales with how far above the threshold the probability is
            scale        = (prob - _THRESHOLD) / (1.0 - _THRESHOLD)
            severity_idx = min(int(scale * 3), 2)
            severity     = _SEVERITIES[severity_idx]
            confidence   = int(62 + scale * 33)
        else:
            severity   = None
            confidence = 0

        results.append({
            "name":       name,
            "key":        key,
            "detected":   detected,
            "severity":   severity,
            "confidence": confidence,
        })

    return results


def _refine_with_pixels(base: dict, image_data: dict) -> dict:
    """
    Adjust base defect probabilities using pixel-level statistics.
    Modifications are capped at 1.0 and only increase (not decrease) values.
    """
    roi = image_data.get("roi")
    if roi is None or roi.size == 0:
        return base

    total = float(roi.size)

    # Burn marks — fraction of near-black pixels
    dark_ratio = float(np.sum(roi < 25)) / total
    if dark_ratio > 0.10:
        boost = min(dark_ratio * 0.6, 0.35)
        base["burn_marks"] = min(base["burn_marks"] + boost, 1.0)

    # Corrosion — high local variance indicates rough / pitted texture
    variance  = float(np.var(roi.astype(np.float32)))
    norm_var  = min(variance / 3500.0, 1.0)
    if norm_var > 0.45:
        boost = (norm_var - 0.45) * 0.40
        base["corrosion"] = min(base["corrosion"] + boost, 1.0)

    # Label damage — bright highlight clusters (reflected light from torn label)
    bright_ratio = float(np.sum(roi > 230)) / total
    if bright_ratio > 0.08:
        boost = min(bright_ratio * 0.5, 0.25)
        base["label_damage"] = min(base["label_damage"] + boost, 1.0)

    return base
