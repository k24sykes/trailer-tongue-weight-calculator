import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import tempfile
import os

# --- Streamlit Setup ---
st.set_page_config(layout="wide", page_title="Trailer Tongue Weight Calculator")
st.title("🎯 Trailer Tongue Weight Calculator")
st.markdown("""
This app calculates the tongue weight of a trailer using static equilibrium.  
**Assumptions:**
- All axles are treated as one virtual axle at the average position.
- Loads are treated as point forces acting at their CG locations.
- Positive tongue weight indicates downward force on the hitch (this is desirable).
""")

# --- User Inputs ---
colA, colB = st.columns(2)

with colA:
    trailer_length = st.number_input("Total Trailer Length (in)", value=214)
    num_axles = st.selectbox("Number of Axles", [1, 2], index=1)

    axle_positions = []
    for i in range(num_axles):
        pos = st.number_input(f"Axle {i+1} Position from Hitch (in)", value=134 + 36 * i)
        axle_positions.append(pos)
    axle_avg = sum(axle_positions) / len(axle_positions)

with colB:
    num_loads = st.number_input("Number of Loads", min_value=1, max_value=5, value=1)
    loads = []
    for i in range(num_loads):
        weight = st.number_input(f"Load {i+1} Weight (lbs)", value=11305 if i == 0 else 0)
        cg = st.number_input(f"Load {i+1} CG from Hitch (in)", value=139 if i == 0 else 100)
        loads.append((weight, cg))

# --- Tongue Weight Calculation ---
total_weight = sum(w for w, _ in loads)
total_moment = sum(w * cg for w, cg in loads)
tongue_weight = (total_moment - total_weight * axle_avg) / axle_avg
tongue_pct = 100 * tongue_weight / total_weight if total_weight else 0

# --- Status ---
if total_weight == 0:
    st.warning("Total trailer load is zero.")
elif tongue_pct < 10:
    st.warning(f"Tongue weight is too low: {tongue_pct:.1f}% (Recommended: 10–15%)")
elif tongue_pct > 15:
    st.warning(f"Tongue weight is too high: {tongue_pct:.1f}% (Recommended: 10–15%)")
else:
    st.success(f"Tongue weight is within acceptable range: {tongue_pct:.1f}%")

# --- Plotting ---
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(-1, 1)
ax.get_yaxis().set_visible(False)
ax.set_xlabel("Distance from Hitch (in)")

# Hitch
ax.axvline(0, color='black', linestyle='--', label="Hitch")

# Axles
ax.axvline(axle_avg, color='blue', linestyle=':', label="Virtual Axle")
ax.text(axle_avg, -0.3, f"Virtual Axle\n({axle_avg:.1f} in)", ha="center", fontsize=8)

# Loads
for i, (w, cg) in enumerate(loads):
    ax.plot(cg, 0, "go")
    ax.text(cg, 0.2, f"{w} lbs\nLoad {i+1}", ha="center", fontsize=8)

# Move legend below plot
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
st.pyplot(fig)

# --- Results Display ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Load", f"{total_weight:.1f} lbs")
    st.metric("Tongue Weight", f"{tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")

# --- PDF Export ---
if st.button("📄 Export Results to PDF"):
    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(tmpdir, "plot.png")
        pdf_path = os.path.join(tmpdir, "tongue_weight_report.pdf")

        # Save plot properly in binary mode
        fig.savefig(image_path, bbox_inches='tight', dpi=300, format='png')

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Trailer Tongue Weight Report", ln=True, align='C')
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Total Load: {total_weight:.1f} lbs", ln=True)
        pdf.cell(200, 10, txt=f"Tongue Weight: {tongue_weight:.1f} lbs ({tongue_pct:.1f}%)", ln=True)
        pdf.cell(200, 10, txt=f"Virtual Axle Position: {axle_avg:.1f} in", ln=True)
        pdf.cell(200, 10, txt="Assumptions:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 10, "- All axles treated as a single point load at average position.\n"
                              "- Loads treated as point forces at CGs.\n"
                              "- Positive tongue weight indicates downward force at hitch.")
        pdf.image(image_path, x=10, y=None, w=180)
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="tongue_weight_report.pdf", mime="application/pdf")
