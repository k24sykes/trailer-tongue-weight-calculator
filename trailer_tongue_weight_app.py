import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import tempfile
import os

# --- Page config ---
st.set_page_config(layout="wide")
st.sidebar.title("Trailer Load Inputs")

# --- Sidebar Inputs ---
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=214)
num_axles = st.sidebar.selectbox("Number of Axles", [1, 2], index=1)

axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=134 + 36 * i)
    axle_positions.append(pos)

# Payload inputs
load_weight = st.sidebar.number_input("Payload Weight (lbs)", value=11305)
load_cg = st.sidebar.number_input("Payload CG from Hitch (in)", value=139)

# Optional trailer base weight and CG
include_trailer = st.sidebar.checkbox("Include Trailer Weight & CG", value=True)
trailer_weight = trailer_cg = 0
if include_trailer:
    trailer_weight = st.sidebar.number_input("Trailer Weight (lbs)", value=3500)
    trailer_cg = st.sidebar.number_input("Trailer CG from Hitch (in)", value=90)

# --- Tongue and Axle Load Calculation ---
def compute_tongue_and_axle_loads(load_weight, load_cg, trailer_weight, trailer_cg, axle_positions):
    W1 = load_weight
    x1 = load_cg
    W2 = trailer_weight
    x2 = trailer_cg

    total_weight = W1 + W2
    if total_weight == 0:
        return 0.0, [], 0.0, 0.0

    total_moment = W1 * x1 + W2 * x2
    total_cg = total_moment / total_weight

    if len(axle_positions) == 1:
        x = axle_positions[0]
        axle_load = total_weight * total_cg / x
        tongue_weight = total_weight - axle_load
        return tongue_weight, [axle_load], total_weight, total_cg

    elif len(axle_positions) == 2:
        x1_axle, x2_axle = axle_positions
        A = np.array([
            [1, 1],
            [x1_axle, x2_axle]
        ])
        b = np.array([
            total_weight,
            total_weight * total_cg
        ])
        axle_loads = np.linalg.solve(A, b)
        tongue_weight = total_weight - np.sum(axle_loads)
        return tongue_weight, axle_loads.tolist(), total_weight, total_cg

    else:
        return 0.0, [], total_weight, total_cg

# --- Run Calculation ---
tongue_weight, axle_loads, total_weight, total_cg = compute_tongue_and_axle_loads(
    load_weight, load_cg, trailer_weight, trailer_cg, axle_positions
)

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

    # Payload CG
    ax.plot(load_cg, 0.2, "go")
    ax.text(load_cg, 0.35, f"Payload\n{load_weight} lbs", ha="center", fontsize=8)

    # Trailer CG (if used)
    if include_trailer and trailer_weight > 0:
        ax.plot(trailer_cg, -0.2, "ro")
        ax.text(trailer_cg, -0.35, f"Trailer\n{trailer_weight} lbs", ha="center", fontsize=8)

    # Axles
    for i, x in enumerate(axle_positions):
        ax.axvline(x, color="blue", linestyle=":")
        if i < len(axle_loads):
            ax.text(x, -0.6, f"Axle {i+1}\n{axle_loads[i]:.0f} lbs", ha="center", fontsize=8)
        else:
            ax.text(x, -0.6, f"Axle {i+1}", ha="center", fontsize=8)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.8), ncol=3)
    st.pyplot(fig)

with col2:
    st.subheader("Results")
    st.metric("Total Load", f"{total_weight:.1f} lbs")
    st.metric("Tongue Weight", f"{tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")
    st.metric("Combined CG", f"{total_cg:.1f} in")
    if axle_loads:
        st.markdown("### Axle Loads")
        for i, load in enumerate(axle_loads):
            st.write(f"Axle {i+1}: **{load:.1f} lbs**")

# --- Export to PDF ---
if st.button("Export to PDF"):
    with tempfile.TemporaryDirectory() as tmpdir:
        plot_path = os.path.join(tmpdir, "plot.png")
        pdf_path = os.path.join(tmpdir, "report.pdf")

        # Save the plot image
        fig.savefig(plot_path, bbox_inches='tight')

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Trailer Load Report", ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Total Load: {total_weight:.1f} lbs", ln=True)
        pdf.cell(200, 10, txt=f"Tongue Weight: {tongue_weight:.1f} lbs ({tongue_pct:.1f}%)", ln=True)
        pdf.cell(200, 10, txt=f"Combined CG: {total_cg:.1f} in from hitch", ln=True)
        pdf.ln(5)

        for i, x in enumerate(axle_positions):
            txt = f"Axle {i+1} at {x} in — Load: {axle_loads[i]:.1f} lbs" if i < len(axle_loads) else f"Axle {i+1} at {x} in"
            pdf.cell(200, 10, txt=txt, ln=True)

        pdf.ln(10)
        pdf.image(plot_path, x=10, w=190)
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF Report", f, file_name="trailer_load_report.pdf")
