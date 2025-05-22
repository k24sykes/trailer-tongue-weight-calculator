import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import tempfile
import os

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Trailer Tongue Weight Calculator")

# --- Sidebar Inputs ---
st.sidebar.title("Trailer Configuration")
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=214)

num_axles = st.sidebar.selectbox("Number of Axles", [1, 2], index=1)
axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position (in from hitch)", value=134 + i*36)
    axle_positions.append(pos)

st.sidebar.markdown("---")

# --- Load Inputs ---
st.sidebar.title("Load Configuration")

use_single_load = st.sidebar.checkbox("Use Single Load Input", value=True)

loads = []

if use_single_load:
    weight = st.sidebar.number_input("Total Trailer Load (lbs)", value=11305)
    cg = st.sidebar.number_input("Center of Gravity from Hitch (in)", value=139)
    loads.append((weight, cg))
else:
    num_loads = st.sidebar.number_input("Number of Load Points", min_value=1, value=1, step=1)
    for i in range(num_loads):
        weight = st.sidebar.number_input(f"Load {i+1} Weight (lbs)", value=1000, key=f"w_{i}")
        pos = st.sidebar.number_input(f"Load {i+1} Position (in from hitch)", value=100, key=f"x_{i}")
        loads.append((weight, pos))

# --- Equilibrium Calculation ---
def solve_reactions(loads, axle_positions):
    total_load = sum(w for w, _ in loads)
    total_moment = sum(w * x for w, x in loads)

    if len(axle_positions) == 1:
        x1 = axle_positions[0]
        R1 = total_moment / x1  # Axle reaction
        RH = total_load - R1
        return RH, [R1]
    
    elif len(axle_positions) == 2:
        x1, x2 = axle_positions
        A = np.array([
            [1, 1],
            [x1, x2]
        ])
        b = np.array([
            total_load,
            total_moment
        ])
        try:
            R = np.linalg.solve(A, b)
            R1, R2 = R
            RH = total_load - R1 - R2
            return RH, [R1, R2]
        except np.linalg.LinAlgError:
            return 0, [0] * len(axle_positions)

# --- Run Calculation ---
tongue_weight, axle_loads = solve_reactions(loads, axle_positions)
total_weight = sum(w for w, _ in loads)
tongue_pct = 100 * tongue_weight / total_weight if total_weight else 0

# --- Warnings ---
if total_weight == 0:
    st.warning("Total trailer load is zero.")
elif tongue_pct < 10:
    st.warning(f"Tongue weight is too low: {tongue_pct:.1f}% (Recommended: 10–15%)")
elif tongue_pct > 15:
    st.warning(f"Tongue weight is too high: {tongue_pct:.1f}% (Recommended: 10–15%)")
else:
    st.success(f"Tongue weight is within acceptable range: {tongue_pct:.1f}%")

# --- Layout ---
col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.set_xlim(0, trailer_length)
    ax.set_ylim(-1, 1)
    ax.get_yaxis().set_visible(False)
    ax.set_xlabel("Distance from Hitch (in)")

    # Hitch
    ax.axvline(0, color='black', linestyle='--', label="Hitch")
    ax.text(0, 0.6, f"Hitch\n{tongue_weight:.0f} lbs", ha="center", fontsize=8)

    # Loads
    for i, (w, x) in enumerate(loads):
        ax.plot(x, 0, "go")
        ax.text(x, 0.2, f"{w} lbs\nLoad {i+1}", ha="center", fontsize=8)

    # Axles
    for i, x in enumerate(axle_positions):
        ax.axvline(x, color="blue", linestyle=":")
        ax.text(x, -0.3, f"Axle {i+1}\n{axle_loads[i]:.0f} lbs", ha="center", fontsize=8)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.4), ncol=3)
    st.pyplot(fig)

with col2:
    st.subheader("Results")
    st.metric("Total Load", f"{total_weight:.1f} lbs")
    st.metric("Tongue Weight", f"{tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")
    if axle_loads:
        st.markdown("### Axle Loads")
        for i, load in enumerate(axle_loads):
            st.write(f"Axle {i+1}: **{load:.1f} lbs**")

# --- Export PDF ---
st.markdown("---")
if st.button("Export as PDF"):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save the plot
        img_path = os.path.join(tmpdir, "plot.png")
        fig.savefig(img_path, bbox_inches="tight")

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, "Trailer Tongue Weight Report", ln=True, align="C")
        pdf.ln(5)
        pdf.cell(200, 10, f"Total Load: {total_weight:.1f} lbs", ln=True)
        pdf.cell(200, 10, f"Tongue Weight: {tongue_weight:.1f} lbs ({tongue_pct:.1f}%)", ln=True)

        for i, load in enumerate(axle_loads):
            pdf.cell(200, 10, f"Axle {i+1} Load: {load:.1f} lbs", ln=True)

        pdf.ln(5)
        pdf.image(img_path, w=180)

        pdf_output_path = os.path.join(tmpdir, "tongue_weight_report.pdf")
        pdf.output(pdf_output_path)

        with open(pdf_output_path, "rb") as f:
            st.download_button(
                label="Download PDF Report",
                data=f,
                file_name="tongue_weight_report.pdf",
                mime="application/pdf"
            )
