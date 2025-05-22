import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import io

st.set_page_config(layout="wide")
st.sidebar.title("Trailer Load Input")

# --- Input Section ---
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=200)
trailer_weight = st.sidebar.number_input("Trailer Weight (lbs)", value=0)
trailer_cg = st.sidebar.number_input("Trailer CoG from Hitch (in)", value=0)

num_axles = st.sidebar.selectbox("Number of Axles", [1, 2, 3], index=1)
axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=100 + 30 * i)
    axle_positions.append(pos)

num_loads = st.sidebar.number_input("Number of Additional Loads", min_value=1, max_value=10, value=1)
loads = []
for i in range(num_loads):
    weight = st.sidebar.number_input(f"Load {i+1} Weight (lbs)", value=1000, key=f"w{i}")
    position = st.sidebar.number_input(f"Load {i+1} Position from Hitch (in)", value=100, key=f"p{i}")
    loads.append((weight, position))

# --- Helper Functions ---
def compute_tongue_and_axle_loads(loads, trailer_weight, trailer_cg, axle_positions):
    # Add trailer as a load if weight is specified
    if trailer_weight > 0:
        loads.append((trailer_weight, trailer_cg))

    total_weight = sum(w for w, _ in loads)
    total_moment = sum(w * x for w, x in loads)

    # Moment balance about the hitch to find tongue weight
    tongue_weight = total_moment / trailer_length

    # Distribute the rest of the load to axles based on position and moment balance
    axle_loads = []
    axle_moments = [abs(x - trailer_length / 2) for x in axle_positions]
    total_moment_arm = sum(1 / (m + 1e-6) for m in axle_moments)  # Prevent div by zero

    distributed_weight = total_weight - tongue_weight
    for m in axle_moments:
        load_share = (1 / (m + 1e-6)) / total_moment_arm
        axle_loads.append(distributed_weight * load_share)

    return tongue_weight, axle_loads, total_weight

# --- Computation ---
tongue_weight, axle_loads, total_weight = compute_tongue_and_axle_loads(
    loads[:], trailer_weight, trailer_cg, axle_positions
)
tongue_pct = 100 * tongue_weight / total_weight

# --- Warnings ---
if tongue_pct < 10:
    st.warning(f"Tongue weight is too low: {tongue_pct:.1f}% (Recommended: 10–15%)")
elif tongue_pct > 15:
    st.warning(f"Tongue weight is too high: {tongue_pct:.1f}% (Recommended: 10–15%)")
else:
    st.success(f"Tongue weight is in acceptable range: {tongue_pct:.1f}%")

# --- Layout ---
col1, col2 = st.columns([2, 1])

# --- Plot (2D Layout) ---
with col1:
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.set_xlim(0, trailer_length)
    ax.set_ylim(-1, 1)
    ax.get_yaxis().set_visible(False)
    ax.set_xlabel("Trailer Length from Hitch (in)")

    # Hitch marker
    ax.axvline(0, color="black", linestyle="--", label="Hitch (0 in)")

    # Plot loads
    for i, (w, x) in enumerate(loads):
        ax.plot(x, 0, "ro")
        ax.text(x, 0.1 + 0.05 * (i % 3), f"{w} lbs", ha="center", fontsize=8)
        ax.text(x, -0.15, f"Load {i+1}", ha="center", fontsize=7)

    # Trailer CoG
    if trailer_weight > 0:
        ax.plot(trailer_cg, 0, "go")
        ax.text(trailer_cg, 0.25, f"{trailer_weight} lbs\n(Trailer)", ha="center", fontsize=7)

    # Axles
    for i, (x, load) in enumerate(zip(axle_positions, axle_loads)):
        ax.axvline(x, color="blue", linestyle=":")
        ax.text(x, -0.4, f"Axle {i+1}\n{load:.0f} lbs", ha="center", fontsize=8)

    # Legend
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.65), ncol=4)
    st.pyplot(fig)

# --- Axle Load Distribution Bar Chart ---
with col2:
    st.subheader("Axle Load Sharing")
    labels = [f"Axle {i+1}" for i in range(len(axle_loads))]
    fig2, ax2 = plt.subplots()
    ax2.barh(labels, axle_loads, color="skyblue")
    ax2.set_xlabel("Load (lbs)")
    st.pyplot(fig2)

# --- Export to PDF ---
if st.button("Export Results to PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Tongue Weight Calculator Results", ln=True, align="C")
    pdf.ln()

    pdf.cell(200, 10, txt=f"Total Weight: {total_weight:.1f} lbs", ln=True)
    pdf.cell(200, 10, txt=f"Tongue Weight: {tongue_weight:.1f} lbs ({tongue_pct:.1f}%)", ln=True)
    pdf.ln()
    for i, load in enumerate(axle_loads):
        pdf.cell(200, 10, txt=f"Axle {i+1} Load: {load:.1f} lbs", ln=True)

    # Save figures to buffer
    buf1 = io.BytesIO()
    fig.savefig(buf1, format="png", bbox_inches="tight")
    buf1.seek(0)
    pdf.image(buf1, x=10, y=pdf.get_y(), w=190)
    pdf.ln(65)

    buf2 = io.BytesIO()
    fig2.savefig(buf2, format="png", bbox_inches="tight")
    buf2.seek(0)
    pdf.image(buf2, x=10, y=pdf.get_y(), w=190)

    st.download_button("Download PDF", data=pdf.output(dest="S").encode("latin-1"),
                       file_name="tongue_weight_report.pdf", mime="application/pdf")
