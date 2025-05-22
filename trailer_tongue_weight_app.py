import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import tempfile
import os

# --- Page config ---
st.set_page_config(layout="wide", page_title="Trailer Tongue Weight Calculator")
st.title("🚛 Trailer Tongue Weight Calculator")

# --- Sidebar Inputs ---
st.sidebar.header("Trailer Parameters")
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=214)

# Axle inputs (simplified to virtual midpoint)
axle1 = st.sidebar.number_input("Front Axle Position from Hitch (in)", value=134)
axle2 = st.sidebar.number_input("Rear Axle Position from Hitch (in)", value=170)

# Virtual axle midpoint
virtual_axle = (axle1 + axle2) / 2

# Load inputs
st.sidebar.header("Load Parameters")
load_weight = st.sidebar.number_input("Load Weight (lbs)", value=11305)
load_cg = st.sidebar.number_input("Load CG from Hitch (in)", value=139)

# Optional trailer frame weight
st.sidebar.header("Optional Trailer Weight")
trailer_frame_weight = st.sidebar.number_input("Trailer Frame Weight (lbs)", value=0)
trailer_frame_cg = st.sidebar.number_input("Trailer Frame CG from Hitch (in)", value=0)

# --- Combine loads ---
total_weight = load_weight + trailer_frame_weight
total_moment = (load_weight * load_cg) + (trailer_frame_weight * trailer_frame_cg)
distance_axle_to_hitch = virtual_axle

# --- Tongue weight calculation ---
if distance_axle_to_hitch != 0:
    tongue_force = total_moment / distance_axle_to_hitch
else:
    tongue_force = 0

tongue_force = round(tongue_force, 2)
tongue_pct = 100 * tongue_force / total_weight if total_weight else 0

# --- Warnings and messages ---
st.subheader("Results")
st.metric("Total Weight", f"{total_weight:.1f} lbs")
st.metric("Tongue Weight", f"{tongue_force:.1f} lbs ({tongue_pct:.1f}%)")

if tongue_force < 0:
    st.warning("⚠️ WARNING: Hitch is experiencing an **upward** force (negative tongue weight). Load CG may be behind the axle midpoint.")
else:
    st.success("✅ Hitch is loaded correctly with **downward** tongue force.")

# --- Assumptions Display ---
with st.expander("ℹ️ Modeling Assumptions", expanded=True):
    st.markdown("""
- Axles are modeled as a single **virtual axle** located at the midpoint between the two actual axles.
- The load and trailer weight are modeled as point loads located at their respective CGs.
- All forces are assumed to act **vertically** (no dynamic or wind loading).
- Positive tongue weight means the hitch is pushing **down**.
""")

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(-1, 1)
ax.get_yaxis().set_visible(False)
ax.set_xlabel("Distance from Hitch (in)")

# Hitch
ax.axvline(0, color='black', linestyle='--', label="Hitch")
ax.text(0, 0.6, "Hitch", ha="center", fontsize=8)

# Load CG
ax.plot(load_cg, 0, "go", label="Load CG")
ax.text(load_cg, 0.3, f"{load_weight} lbs", ha="center", fontsize=8)

# Trailer CG if present
if trailer_frame_weight > 0:
    ax.plot(trailer_frame_cg, 0, "ro", label="Trailer Frame CG")
    ax.text(trailer_frame_cg, -0.3, f"{trailer_frame_weight} lbs", ha="center", fontsize=8)

# Virtual axle
ax.axvline(virtual_axle, color="blue", linestyle=":", label="Virtual Axle")
ax.text(virtual_axle, -0.5, "Virtual Axle", ha="center", fontsize=8)

ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4)
st.pyplot(fig)

# --- PDF Export ---
st.subheader("📄 Export Results")
if st.button("Generate PDF Report"):
    # Save the plot to a temporary file
    tmpdir = tempfile.mkdtemp()
    plot_path = os.path.join(tmpdir, "plot.png")
    fig.savefig(plot_path, bbox_inches="tight")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Trailer Tongue Weight Report", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Trailer Length: {trailer_length} in", ln=True)
    pdf.cell(0, 10, f"Virtual Axle at: {virtual_axle} in", ln=True)
    pdf.cell(0, 10, f"Load: {load_weight} lbs at {load_cg} in", ln=True)
    if trailer_frame_weight > 0:
        pdf.cell(0, 10, f"Trailer Frame: {trailer_frame_weight} lbs at {trailer_frame_cg} in", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, f"Total Weight: {total_weight:.1f} lbs", ln=True)
    pdf.cell(0, 10, f"Tongue Weight: {tongue_force:.1f} lbs ({tongue_pct:.1f}%)", ln=True)

    # Add plot
    pdf.image(plot_path, x=10, y=None, w=180)

    # Save PDF
    pdf_path = os.path.join(tmpdir, "tongue_weight_report.pdf")
    pdf.output(pdf_path)

    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download PDF", f, file_name="tongue_weight_report.pdf")

