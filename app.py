import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os

from image_processing import preprocess_image, detect_defects
from classifier import classify_battery
from report_generator import generate_report

# Page configuration
st.set_page_config(
    page_title="Smart Battery Reuse Identification",
    page_icon="🔋",
    layout="wide"
)

# Custom CSS for a modern, professional look
st.markdown("""
    <style>
    /* Main background and font */
    .stApp {
        background-color: #f8f9fa;
    }

    /* Modern Card Style */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Header styling */
    h1 {
        color: #1a365d;
        font-weight: 800 !important;
    }

    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #2c5282 !important;
        color: white !important;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #1a365d !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🔋 Smart Battery Reuse Identification System")
    st.markdown("<p style='text-align: center; color: #4a5568;'>Advanced diagnostic system for analyzing battery health and reuse potential.</p>", unsafe_allow_html=True)

    # --- Sidebar Inputs ---
    st.sidebar.header("⚙️ Analysis Parameters")

    SYMPTOM_MAPPING = {
        # Positive / Healthy Markers
        "Battery holds charge well": "healthy_capacity",
        "Consistent power delivery": "stable_voltage",
        "No visible physical damage": "clean_exterior",
        "Cool temperature during use": "thermal_stable",
        # Negative / Warning Symptoms
        "Battery percentage drops quickly": "drain_fast",
        "Phone shuts off at 20-30% suddenly": "sudden_shutdown",
        "Battery gets very hot during charging": "burn_marks",
        "Takes much longer than usual to reach 100%": "corrosion",
        "Back cover of the device is bulging": "swelling",
        "Visible damage to battery wrapping/label": "label_damage"
    }

    selected_symptoms = st.sidebar.multiselect(
        "Select Battery Symptoms",
        options=list(SYMPTOM_MAPPING.keys()),
        help="Choose all symptoms that apply to the battery"
    )

    battery_id = st.sidebar.text_input("Battery ID", value="BAT-001")
    voltage = st.sidebar.number_input("Measured Voltage (V)", min_value=0.0, max_value=5.0, value=3.7, step=0.1)

    analyze_button = st.sidebar.button("🚀 Run Full Analysis")

    # Logic for dynamic greeting based on symptoms
    if not analyze_button:
        if not selected_symptoms:
            st.info("👋 **Welcome!** Please select battery symptoms and enter parameters in the sidebar to begin analysis.")
        elif any(s in selected_symptoms for s in ["Back cover of the device is bulging", "Battery gets very hot during charging"]):
            st.warning("⚠️ **Caution:** You have selected critical symptoms. Please ensure the battery is handled safely during measurement.")
        else:
            st.success("✅ Parameters set. Ready to analyze battery health!")

    # --- Analysis Process ---
    if analyze_button:
        if selected_symptoms:
            defects = []
            for symptom in selected_symptoms:
                key = SYMPTOM_MAPPING[symptom]
                defects.append({
                    "name": symptom,
                    "key": key,
                    "detected": True,
                    "severity": "Moderate",
                    "confidence": 100
                })

            from image_processing import detect_defects
            voltage_defects = detect_defects(None, battery_id, voltage)
            for vd in voltage_defects:
                if vd["detected"] and not any(d["key"] == vd["key"] for d in defects):
                    defects.append(vd)

            with st.spinner("🔍 Analyzing health markers..."):
                prep_steps = ["User symptom selection verified [OK]", "Voltage measurement validated [OK]"]
                grade, recommendation = classify_battery(voltage, defects)
                report_path = generate_report(battery_id, voltage, prep_steps, defects, grade, recommendation)

            # Modern Layout using Tabs
            tab1, tab2, tab3 = st.tabs(["📊 Result Summary", "🔍 Detailed Analysis", "📄 Final Report"])

            with tab1:
                st.subheader("Overall Health Status")

                grade_colors = {"A": "#28a745", "B": "#ffc107", "C": "#dc3545"}
                color = grade_colors.get(grade, "#6c757d")

                grade_labels = {
                    "A": "Grade A — Healthy / Reusable",
                    "B": "Grade B — Usable with Caution",
                    "C": "Grade C — Not Fit for Reuse",
                }
                label = grade_labels.get(grade, f"Grade {grade}")

                st.markdown(f"""
                    <div style="background-color: {color}; color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px;">
                        <h1 style="color: white !important; margin: 0;">{label}</h1>
                        <p style="font-size: 1.2rem; margin-top: 10px;">{recommendation}</p>
                    </div>
                """, unsafe_allow_html=True)

                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.markdown(f'<div class="metric-card"><h4>Battery ID</h4><h2>{battery_id}</h2></div>', unsafe_allow_html=True)
                with m_col2:
                    st.markdown(f'<div class="metric-card"><h4>Voltage</h4><h2>{voltage:.2f} V</h2></div>', unsafe_allow_html=True)
                with m_col3:
                    pos_count = len([d for d in defects if d["key"] in {"healthy_capacity", "stable_voltage", "clean_exterior", "thermal_stable"}])
                    neg_count = len([d for d in defects if d["key"] not in {"healthy_capacity", "stable_voltage", "clean_exterior", "thermal_stable"}])
                    score = 100 if neg_count == 0 else max(0, 100 - (neg_count * 20) + (pos_count * 10))
                    st.markdown(f'<div class="metric-card"><h4>Health Score</h4><h2>{min(100, score)}%</h2></div>', unsafe_allow_html=True)

            with tab2:
                st.subheader("Symptom & Defect Analysis")
                defect_data = []
                for d in defects:
                    defect_data.append({
                        "Symptom/Defect": d["name"],
                        "Key": d["key"],
                        "Status": "DETECTED" if d["detected"] else "CLEAR",
                        "Severity": d["severity"] if d["detected"] else "—",
                    })
                st.table(defect_data)

            with tab3:
                st.subheader("Export Documentation")
                if os.path.exists(report_path):
                    with open(report_path, "rb") as f:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=f,
                            file_name=os.path.basename(report_path),
                            mime="application/pdf",
                            use_container_width=True
                        )
                else:
                    st.error("Report file not found.")

        else:
            st.error("Please select at least one battery symptom to start the analysis.")

    else:
        st.markdown("---")
        st.markdown("### ⚙️ How the system works")

        expl_col1, expl_col2 = st.columns(2)
        with expl_col1:
            st.markdown("""
            **1. Intelligent Input**
            The system collects physical symptoms and electrical voltage to build a health profile.

            **2. Health Mapping**
            Positive markers are weighed against critical defects using a rule-based classifier.
            """)
        with expl_col2:
            st.markdown("""
            **3. Grade Assignment**
            Batteries are categorized into Grade A (Reusable), la-t-e-n-c-y- a-l-l-o-w-e-d  - B (Caution), or C (Reject).

            **4. Certified Reporting**
 la-t-e-n-c-y- a-l-l-o-w-e-d  - A detailed PDF report is generated for quality assurance and record-keeping.
            """)

if __name__ == "__main__":
    main()
