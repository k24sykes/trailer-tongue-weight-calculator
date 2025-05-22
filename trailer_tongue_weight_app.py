import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import io

st.set_page_config(layout="wide")

# Sidebar Inputs
st.sidebar.title("Tongue Weight Calculator")

# Load
st.sidebar.header("Main Load")
load_weight = st.sidebar.number_input("Load Weight (lbs / kg)", value=11305.0)
load_position = st.sidebar.number_input("Load Position from Hitch (in / mm)", value=139.0)

# Optional trailer
st.sidebar.header("Trailer Info (Optional)")
trailer_weight = st.sidebar.number_input("Trailer Weight (lbs / kg)", value=1500.0)
trailer_cog = st.sidebar.number_input("Trailer Center of Gravity (in / mm)", value=130.0)

# Axles
st.sidebar.header("Axle Configuration")
num_axles = st.sidebar.selectbox("Number of Axles", [1, 2, 3])
axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=100.0 + i * 40)
    axle_positions.append(pos)

# Build position/weight list
positions = [load_position]
weights = [load_weight]
labels = ["Load"]

if trailer_weight > 0:
    positions.append(trailer_cog)
    weights.append(trailer_weight)
    labels.append("Trailer")

positions = np.array(positions)
weights = np.array(weights)
total_weight = np.sum(weights)

# Set up equilibrium equations: [Tongue, Axle1, Axle2, Axle3]
n_unknowns = 1 + num_axles
A = np.zeros((2, n_unknowns))  # 2 equations: force and moment
b = np.zeros(2)

# Force balance
A[0, 0] = 1  # Tongue
A[0, 1:] = 1  # Axles
b[0] = total_weight

# Moment balance about hitch
# Tongue moment is zero
for i, pos in enumerate(axle_positions):
    A[1, i + 1] = pos
b[1] = np.sum(positions * weights)

try:
    solution = np.linalg.solve(A, b)
except np.linalg.LinAlgError:
    st.error("Cannot solve equations. Check that axle positions are unique and inputs are valid.")
    st.stop()

tongue_weight = solution[0]
axle_loads = solution[1:]
tongue_percent = (tongue_weight / total_weight) * 100 if total_weight > 0 else 0

# === Output Layout ===
col1, col2 = st.columns([3, 2])

# === Plot: Linear Distribution ===
with col1:
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.set_title("Linear Load Distribution")
    ax.set_xlabel("Distance from Hitch (in)")
    ax.set_yticks([])

    # Plot loads
    for pos, wt, label in zip(positions, weights, labels):
        ax.plot(pos, 0, 'o', label=f"{label}: {wt:.1f} lbs")
        ax.annotate(f"{label}\n{wt:.1f} lbs", xy=(pos, 0), xytext=(0, 15),
                    textcoords="offset points", ha='center', fontsize=9)

    # Plot axles
    for i, pos in enumerate(axle_positions):
        ax.plot(pos, 0, 's', color=f"C{i+2}", label=f"Axle {i+1}: {axle_loads[i]:.1f} lbs")
        ax.annotate(f"Axle {i+1}\n{axle_loads[i]:.1f} lbs", xy=(pos, 0), xytext=(0, -25),
                    textcoords="offset points", ha='center', fontsize=9)

    ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.45), ncol=3, fontsize=9)
    ax.grid(True)
    st.pyplot(fig)

# === Plot: Axle Load Bar Chart ===
with col2:
    fig2, ax2 = plt.subplots(figsize=(4, 3))
    ax2.barh([f"Axle {i+1}" for i in range(num_axles)], axle_loads, color='skyblue')
    ax2.set_xlabel("Load (lbs)")
    ax2.set_title("Axle Load Distribution")
    st.pyplot(fig2)

# === Text Output ===
st.subheader("Tongue Weight Results")
st.markdown(f"**Total Load:** {total_weight:.1f} lbs")
st.markdown(f"**Tongue Weight:** {tongue_weight:.1f} lbs")
st.markdown(f"**Tongue Weight %:** {tongue_percent:.1f}%")

if tongue_percent < 10:
    st.warning("⚠️ Tongue weight is **below 10%** — risk of sway.")
elif tongue_percent > 15:
    st.warning("⚠️ Tongue weight is **above 15%** — excessive load on hitch.")
else:
    st.success("✅ Tongue weight is within recommended range (10%–15%).")

# === PDF Export ===
st.subheader("Export to PDF")
if st.button("Generate PDF Report"):
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        fig.tight_layout()
        pdf.savefig(fig)
        fig2.tight_layout()
        pdf.savefig(fig2)

    st.download_button(
        label="Download PDF",
        data=buffer.getvalue(),
        file_name="tongue_weight_report.pdf",
        mime="application/pdf"
    )
