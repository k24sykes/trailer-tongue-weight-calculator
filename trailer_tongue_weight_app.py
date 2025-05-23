import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import tempfile
import os

# Page Setup
st.set_page_config(layout="wide", page_title="Trailer Tongue Weight Calculator")
st.title("🚚 Trailer Tongue Weight Calculator")
st.markdown("""
This calculator estimates trailer tongue weight using static equilibrium.  
**Positive tongue weight** = downward force on the hitch (desired for stability).  
""")

# Sidebar Inputs
st.sidebar.header("🔧 Input Parameters")

trailer_length = st.sidebar.number_input("Trailer Length (in)", value=214)

num_axles = st.sidebar.selectbox("Number of Axles", [1, 2], index=1)
axle_positions = [st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=134 + i*36) for i in range(num_axles)]
axle_avg = sum(axle_positions) / len(axle_positions)

num_loads = st.sidebar.number_input("Number of Loads", min_value=1, max_value=5, value=1)
loads = []
for i in range(num_loads):
    weight = st.sidebar.number_input(f"Load {i+1} Weight (lbs)", value=11305 if i == 0 else 0)
    cg = st.sidebar.number_input(f"Load {i+1} CG from Hitch (in)", value=139 if i == 0 else 100)
    loads.append((weight, cg))

# Optional Trailer Weight
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Optional: Trailer Structure Weight")
trailer_weight = st.sidebar.number_input("Trailer Weight (lbs)", value=0)
trailer_cg = st.sidebar.number_input("Trailer CG from Hitch (in)", value=trailer_length / 2)

# Add trailer weight if given
if trailer_weight > 0:
    loads.append((trailer_weight, trailer_cg))

# Calculations
total_weight = sum(w for w, _ in loads)
total_moment = sum(w * cg for w, cg in loads)

# Tongue force (positive = downward)
raw_tongue_force = (total_moment - total_weight * axle_avg) / axle_avg
tongue_force_display = round(-raw_tongue_force, 2)  # Negate to show downward as positive

tongue_pct = 100 * tongue_force_display / total_weight if total_weight else 0

# Results
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Load", f"{total_weight:.1f} lbs")
    st.metric("Tongue Weight", f"{tongue_force_display:.1f} lbs ({tongue_pct:.1f}%)")

with col2:
    if total_weight == 0:
        st.warning("⚠️ Total trailer load is zero.")
    elif tongue_pct < 10:
        st.warning(f"⚠️ Tongue weight is too low: {tongue_pct:.1f}% (Recommended: 10–15%)")
    elif tongue_pct > 15:
        st.warning(f"⚠️ Tongue weight is too high: {tongue_pct:.1f}% (Recommended: 10–15%)")
    else:
        st.success(f"✅ Tongue weight is within range: {tongue_pct:.1f}%")

# Plot
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(-1.5, 1.5)
ax.get_yaxis().set_visible(False)
ax.set_xlabel("Distance from Hitch (in)")

# Tongue weight dot at 0
ax.plot(0, 0, "ro", label=f"Tongue Weight: {tongue_force_display:.0f} lbs (0 in)")

# Plot real axles
for i, pos in enumerate(axle_positions):
    ax.axvline(pos, color='gray', linestyle='--', label=f"Axle {i+1}: {pos:.0f} in")

# Plot virtual axle (avg)
ax.axvline(axle_avg, color='blue', linestyle=':', label=f"Virtual Axle: {axle_avg:.1f} in")

# Plot loads (dots only, labels in legend)
for i, (w, cg) in enumerate(loads):
    ax.plot(cg, 0, "go", label=f"Load {i+1}: {w:.0f} lbs at {cg:.0f} in")

# Legend beside plot
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
st.pyplot(fig)

# PDF Export
if st.button("📄 Export Results to PDF"):
    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(tmpdir, "plot.png")
        pdf_path = os.path.join(tmpdir, "tongue_weight_report.pdf")

        fig.savefig(image_path, bbox_inches='tight', dpi=300, format='png')

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Trailer Tongue Weight Report", ln=True, align='C')
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Total Load: {total_weight:.1f} lbs", ln=True)
        pdf.cell(200, 10, txt=f"Tongue Weight: {tongue_force_display:.1f} lbs ({tongue_pct:.1f}%)", ln=True)
        pdf.cell(200, 10, txt=f"Axle Midpoint: {axle_avg:.1f} in", ln=True)
        pdf.cell(200, 10, txt="Assumptions:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 10, "- All axles treated as a single point load at average position.\n"
                              "- Loads treated as point forces at CGs.\n"
                              "- Trailer weight & CG are optional.\n"
                              "- Positive tongue weight = downward force at hitch.")
        pdf.image(image_path, x=10, y=None, w=180)
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="tongue_weight_report.pdf", mime="application/pdf")
