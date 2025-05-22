import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import io

st.set_page_config(layout="wide")

st.sidebar.title("Tongue Weight Calculator")

# Load inputs
st.sidebar.header("Load Info")
load_weight = st.sidebar.number_input("Load Weight (lbs / kg)", value=1000.0)
load_position = st.sidebar.number_input("Load Position from Hitch (in / mm)", value=100.0)

# Optional trailer weight
st.sidebar.header("Optional Trailer Info")
trailer_weight = st.sidebar.number_input("Trailer Weight (lbs / kg)", value=0.0)
trailer_cog = st.sidebar.number_input("Trailer Center of Gravity (in / mm)", value=0.0)

# Axle inputs
st.sidebar.header("Axle Positions")
num_axles = st.sidebar.selectbox("Number of Axles", [1, 2, 3])
axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in / mm)", value=100.0 + i * 40)
    axle_positions.append(pos)

# Combine all loads
positions = [load_position]
weights = [load_weight]
labels = ["Load"]

if trailer_weight > 0:
    positions.append(trailer_cog)
    weights.append(trailer_weight)
    labels.append("Trailer")

# Convert to numpy arrays
positions = np.array(positions)
weights = np.array(weights)

# Force/moment equations: solve for reactions at axles
A = np.zeros((2, num_axles))
b = np.zeros(2)

# Total vertical load balance
A[0, :] = 1
b[0] = np.sum(weights)

# Moment balance around hitch
for i in range(num_axles):
    A[1, i] = axle_positions[i]
b[1] = np.sum(positions * weights)

# Solve for axle loads
axle_loads = np.linalg.lstsq(A.T, b, rcond=None)[0]

# Compute tongue weight
total_weight = np.sum(weights)
total_moment = np.sum(positions * weights)
tongue_weight = total_weight - np.sum(axle_loads)

tongue_percent = tongue_weight / total_weight * 100 if total_weight > 0 else 0

# Layout
col1, col2 = st.columns([3, 2])

# Plot 1: Positions and weights
with col1:
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.set_title("Load Distribution")
    ax.set_xlabel("Distance from Hitch (in)")
    ax.set_yticks([])
    
    # Plot points
    for i, (pos, w, label) in enumerate(zip(positions, weights, labels)):
        ax.plot(pos, 0, 'o', label=f"{label}: {w:.1f} lbs")
        ax.annotate(f"{label}\n{w:.1f} lbs", (pos, 0), textcoords="offset points", xytext=(0, 10), ha='center')

    # Plot axles
    for i, pos in enumerate(axle_positions):
        ax.plot(pos, 0, 's', label=f"Axle {i+1}: {axle_loads[i]:.1f} lbs", color=f"C{i+2}")
        ax.annotate(f"Axle {i+1}\n{axle_loads[i]:.1f} lbs", (pos, 0), textcoords="offset points", xytext=(0, -25), ha='center')

    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.6), ncol=3)
    ax.grid(True)
    st.pyplot(fig)

# Plot 2: Axle load bar chart
with col2:
    fig2, ax2 = plt.subplots(figsize=(4, 3))
    ax2.barh([f"Axle {i+1}" for i in range(num_axles)], axle_loads, color='skyblue')
    ax2.set_xlabel("Load (lbs)")
    ax2.set_title("Axle Load Distribution")
    st.pyplot(fig2)

# Tongue weight results
st.subheader("Tongue Weight Results")
st.markdown(f"**Total Weight:** {total_weight:.1f} lbs")
st.markdown(f"**Tongue Weight:** {tongue_weight:.1f} lbs")
st.markdown(f"**Tongue Weight %:** {tongue_percent:.1f}%")

if tongue_percent < 10:
    st.warning("Warning: Tongue weight is less than 10% of total weight.")
elif tongue_percent > 15:
    st.warning("Warning: Tongue weight is greater than 15% of total weight.")
else:
    st.success("Tongue weight is within acceptable range (10%-15%).")

# PDF export
st.subheader("Export Results")
if st.button("Generate PDF Report"):
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        fig.tight_layout()
        pdf.savefig(fig)
        fig2.tight_layout()
        pdf.savefig(fig2)

    st.download_button(
        label="Download PDF",
        data=pdf_buffer.getvalue(),
        file_name="tongue_weight_report.pdf",
        mime="application/pdf"
    )
