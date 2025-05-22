import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

trailer_weight = st.sidebar.number_input("Trailer Load Weight (lbs)", value=11305)
trailer_cg = st.sidebar.number_input("Load Center of Gravity from Hitch (in)", value=139)

# --- Helper Function ---
def compute_tongue_and_axle_loads(trailer_weight, trailer_cg, axle_positions):
    W = trailer_weight
    x_cg = trailer_cg
    x_axles = axle_positions
    n = len(x_axles)

    if n == 1:
        x1 = x_axles[0]
        A1 = W * x_cg / x1
        T = W - A1
        return T, [A1]

    elif n == 2:
        x1, x2 = x_axles
        T = W * (1 - 2 * x_cg / (x1 + x2))
        A1 = A2 = (W - T) / 2
        return T, [A1, A2]

# --- Calculations ---
tongue_weight, axle_loads = compute_tongue_and_axle_loads(trailer_weight, trailer_cg, axle_positions)
total_weight = trailer_weight
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

    # Trailer load CG
    ax.plot(trailer_cg, 0, "go")
    ax.text(trailer_cg, 0.2, f"{trailer_weight} lbs\nLoad CG", ha="center", fontsize=8)

    # Axles
    for i, x in enumerate(axle_positions):
        ax.axvline(x, color="blue", linestyle=":")
        if i < len(axle_loads):
            ax.text(x, -0.3, f"Axle {i+1}\n{axle_loads[i]:.0f} lbs", ha="center", fontsize=8)
        else:
            ax.text(x, -0.3, f"Axle {i+1}", ha="center", fontsize=8)

    # Tongue weight marker at hitch
    ax.plot(0, 0, "ro")
    ax.text(0, -0.5, f"Tongue\n{tongue_weight:.0f} lbs", ha="center", fontsize=8, color='red')

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.5), ncol=4)
    st.pyplot(fig)

with col2:
    st.subheader("Results")
    st.metric("Total Load", f"{total_weight:.1f} lbs")
    st.metric("Tongue Weight", f"{tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")
    if axle_loads:
        st.markdown("### Axle Loads")
        for i, load in enumerate(axle_loads):
            st.write(f"Axle {i+1}: **{load:.1f} lbs**")

    # --- PDF Export ---
    def generate_pdf():
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Trailer Load Calculation Report")

        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"Trailer Length from Hitch: {trailer_length} in")
        c.drawString(50, height - 100, f"Number of Axles: {num_axles}")
        for i, x in enumerate(axle_positions):
            c.drawString(70, height - 120 - 20 * i, f"Axle {i+1} Position from Hitch: {x} in")

        c.drawString(50, height - 160, f"Trailer Load Weight: {trailer_weight} lbs")
        c.drawString(50, height - 180, f"Load Center of Gravity from Hitch: {trailer_cg} in")

        c.drawString(50, height - 220, f"Tongue Weight: {tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")

        c.drawString(50, height - 250, "Axle Loads:")
        y_pos = height - 270
        for i, load in enumerate(axle_loads):
            c.drawString(70, y_pos, f"Axle {i+1}: {load:.1f} lbs")
            y_pos -= 20

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_pdf()
    st.download_button(
        label="Download PDF Report",
        data=pdf_buffer,
        file_name="trailer_load_report.pdf",
        mime="application/pdf"
    )
