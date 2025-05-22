import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import tempfile
from fpdf import FPDF
import os

st.set_page_config(layout="wide")

st.sidebar.header("Trailer Load Inputs")

# Unit toggle
units = st.sidebar.selectbox("Units", ["Imperial (in, lbs)", "Metric (mm, kg)"])
is_metric = "Metric" in units
unit_length = "mm" if is_metric else "in"
unit_weight = "kg" if is_metric else "lbs"

# Conversion factor
length_factor = 25.4 if is_metric else 1
weight_factor = 0.453592 if is_metric else 1

# Axle input
num_axles = st.sidebar.selectbox("Number of Axles", [1, 2, 3])
axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch ({unit_length})", min_value=0.0)
    axle_positions.append(pos / length_factor)
axle_positions = sorted(axle_positions)

# Load inputs
loads = []
load_count = st.sidebar.number_input("Number of Point Loads", min_value=1, max_value=10, value=1)
for i in range(load_count):
    weight = st.sidebar.number_input(f"Load {i+1} Weight ({unit_weight})", min_value=0.0)
    dist = st.sidebar.number_input(f"Load {i+1} Distance from Hitch ({unit_length})", min_value=0.0)
    loads.append((weight / weight_factor, dist / length_factor))

# Optional trailer input
include_trailer = st.sidebar.checkbox("Include Trailer Weight & CG")
if include_trailer:
    trailer_weight = st.sidebar.number_input(f"Trailer Weight ({unit_weight})", min_value=0.0) / weight_factor
    trailer_cg = st.sidebar.number_input(f"Trailer CG from Hitch ({unit_length})", min_value=0.0) / length_factor
    loads.append((trailer_weight, trailer_cg))

# Sum total weight and moment
total_weight = sum(w for w, _ in loads)
total_moment = sum(w * x for w, x in loads)

# Set up equilibrium equations
A = np.zeros((2 + len(axle_positions), len(axle_positions)))
b = np.zeros(2 + len(axle_positions))

# Sum of forces
A[0, :] = 1
b[0] = total_weight

# Sum of moments about hitch
A[1, :] = axle_positions
b[1] = total_moment

# Each variable corresponds to axle load only
for i in range(len(axle_positions)):
    A[2 + i, i] = 1

# Solve using least squares
axle_loads, *_ = np.linalg.lstsq(A, b, rcond=None)

# Calculate tongue weight
tongue_weight = total_weight - sum(axle_loads)
tongue_percentage = (tongue_weight / total_weight) * 100

# Display results
st.title("Tongue Weight Calculator")

col1, col2 = st.columns([2, 1])

# --- Plot layout view ---
with col1:
    fig, ax = plt.subplots(figsize=(10, 2))

    for w, x in loads:
        ax.plot(x, 0, 'o', markersize=10)
        ax.text(x, 0.2, f"{w:.0f} {unit_weight}", ha='center', fontsize=8)

    for i, pos in enumerate(axle_positions):
        ax.axvline(pos, color='gray', linestyle='--')
        ax.text(pos, -0.2, f"Axle {i+1}\n({pos*length_factor:.0f} {unit_length})", ha='center', fontsize=8)

    ax.axvline(0, color='black', linestyle='-', linewidth=2)
    ax.text(0, 0.2, "Hitch", ha='center', fontsize=9, fontweight='bold')

    ax.set_xlim(-10, max(axle_positions + [x for _, x in loads]) + 20)
    ax.set_yticks([])
    ax.set_xlabel(f"Distance from Hitch ({unit_length})")
    ax.set_title("Trailer Load Layout")
    st.pyplot(fig)

# --- Bar chart for axle load distribution ---
with col2:
    fig2, ax2 = plt.subplots(figsize=(3, 2))
    labels = [f"Axle {i+1}" for i in range(len(axle_positions))]
    values = [l for l in axle_loads]
    percent = [v / total_weight * 100 for v in values]

    ax2.barh(labels, percent, color='cornflowerblue')
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Load %")
    ax2.set_title("Axle Load Distribution")
    for i, v in enumerate(percent):
        ax2.text(v + 1, i, f"{v:.1f}%", va='center')

    st.pyplot(fig2)

# --- Results & Warnings ---
st.subheader("Results")
color = 'green' if 10 <= tongue_percentage <= 15 else 'red'
st.markdown(f"**Tongue Weight:** <span style='color:{color}'>{tongue_weight:.1f} {unit_weight} ({tongue_percentage:.1f}%)</span>", unsafe_allow_html=True)

if tongue_percentage < 10:
    st.warning("Tongue weight is too low! This may cause trailer sway.")
elif tongue_percentage > 15:
    st.warning("Tongue weight is too high! This may overload the hitch or tow vehicle.")

# --- Export to PDF ---
if st.button("Export PDF Report"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig.savefig(tmpfile.name)
        layout_img = tmpfile.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig2.savefig(tmpfile.name)
        dist_img = tmpfile.name

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Trailer Load Analysis Results", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, f"Tongue Weight: {tongue_weight:.1f} {unit_weight} ({tongue_percentage:.1f}%)", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, f"Axle Loads: {[f'{v:.1f}' for v in values]} {unit_weight}", ln=True)
    pdf.ln(5)
    pdf.image(layout_img, x=10, y=50, w=180)
    pdf.add_page()
    pdf.image(dist_img, x=10, y=40, w=100)

    pdf_output_path = os.path.join(tempfile.gettempdir(), "trailer_load_report.pdf")
    pdf.output(pdf_output_path)

    with open(pdf_output_path, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name="trailer_load_report.pdf",
            mime="application/pdf"
        )
