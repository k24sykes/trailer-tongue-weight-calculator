import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import tempfile
import os

st.set_page_config(layout="wide", page_title="Trailer Tongue Weight Calculator")
st.title("📦 Trailer Tongue Weight Calculator with PDF Export")

# Sidebar Inputs
st.sidebar.header("Trailer Inputs")
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=214)
load_weight = st.sidebar.number_input("Load Weight (lbs)", value=11305)
load_cg = st.sidebar.number_input("Load CG from Hitch (in)", value=139)

st.sidebar.markdown("---")
st.sidebar.header("Axle Setup")
axle1 = st.sidebar.number_input("Axle 1 Position (in)", value=134)
axle2 = st.sidebar.number_input("Axle 2 Position (in)", value=170)

# --- Calculations ---
virtual_axle = (axle1 + axle2) / 2
moment_about_axle = load_weight * (load_cg - virtual_axle)
distance_hitch_to_axle = virtual_axle

tongue_force = moment_about_axle / distance_hitch_to_axle
axle_force = load_weight - tongue_force

tongue_weight_display = abs(tongue_force)
tongue_pct = 100 * tongue_weight_display / load_weight if load_weight else 0

# --- Results ---
st.subheader("Results")
st.metric("Tongue Weight", f"{tongue_weight_display:.1f} lbs", f"{tongue_pct:.1f}%")
st.metric("Axle Load", f"{axle_force:.1f} lbs")

if tongue_force < 0:
    st.warning("⚠️ WARNING: Tongue weight is negative — the hitch would lift upward. Load CG may be behind the axle midpoint.")
elif tongue_pct < 10:
    st.info("Tongue weight is below recommended range (10–15%). Consider adjusting load position.")
elif tongue_pct > 15:
    st.info("Tongue weight is above recommended range (10–15%). Consider adjusting load position.")
else:
    st.success("✅ Tongue weight is within recommended range (10–15%).")

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(-1, 1)
ax.get_yaxis().set_visible(False)
ax.set_xlabel("Distance from Hitch (in)")

ax.axvline(0, color='black', linestyle='--', label="Hitch")
ax.plot(load_cg, 0, "go")
ax.text(load_cg, 0.2, f"{load_weight} lbs\nLoad CG", ha="center", fontsize=8)

ax.axvline(axle1, color="blue", linestyle=":")
ax.axvline(axle2, color="blue", linestyle=":")
ax.text(axle1, -0.3, f"A1 ({axle1} in)", ha="center", fontsize=8)
ax.text(axle2, -0.3, f"A2 ({axle2} in)", ha="center", fontsize=8)

ax.axvline(virtual_axle, color="purple", linestyle="--")
ax.text(virtual_axle, -0.6, "Virtual Axle", ha="center", fontsize=8, color="purple")

ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.5), ncol=3)
st.pyplot(fig)

# --- Assumptions Box ---
with st.expander("ℹ️ Assumptions Used in This Model"):
    st.markdown("""
    - The two axles are modeled as a **single virtual axle** placed at their midpoint.
    - The load is treated as a **point load** at its center of gravity.
    - Tongue weight is calculated using **static equilibrium (moment balance)**.
    - A **positive tongue weight** pushes **down** on the hitch.
    - For trailer stability, the CG should be **ahead of the axle midpoint**, otherwise the trailer may tip backward.
    """)

# --- PDF Export ---
if st.button("📄 Export Results to PDF"):
    # Save plot to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        plot_path = tmpfile.name
        fig.savefig(plot_path, bbox_inches='tight')

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Trailer Tongue Weight Report", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Trailer Length: {trailer_length} in", ln=True)
    pdf.cell(200, 10, txt=f"Load Weight: {load_weight:.1f} lbs", ln=True)
    pdf.cell(200, 10, txt=f"Load CG from Hitch: {load_cg:.1f} in", ln=True)
    pdf.cell(200, 10, txt=f"Axle 1 Position: {axle1:.1f} in", ln=True)
    pdf.cell(200, 10, txt=f"Axle 2 Position: {axle2:.1f} in", ln=True)
    pdf.cell(200, 10, txt=f"Virtual Axle: {virtual_axle:.1f} in", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Tongue Weight: {tongue_weight_display:.1f} lbs ({tongue_pct:.1f}%)", ln=True)
    pdf.cell(200, 10, txt=f"Axle Load: {axle_force:.1f} lbs", ln=True)
    pdf.ln(10)

    if tongue_force < 0:
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0, 10, txt="WARNING: Tongue weight is negative. This means the hitch would lift upward — unsafe configuration.")
        pdf.set_text_color(0, 0, 0)

    pdf.image(plot_path, x=10, y=None, w=180)

    # Save final PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
        pdf.output(pdf_file.name)
        st.success("PDF exported successfully.")
        with open(pdf_file.name, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="tongue_weight_report.pdf", mime="application/pdf")

    # Clean up
    os.remove(plot_path)
