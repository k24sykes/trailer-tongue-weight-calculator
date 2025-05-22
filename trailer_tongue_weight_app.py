import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

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

# Load weight and CG
load_weight = st.sidebar.number_input("Load Weight (lbs)", value=11305)
load_cg = st.sidebar.number_input("Load Center of Gravity from Hitch (in)", value=139)

# Optional Trailer weight and CG
add_trailer_weight = st.sidebar.checkbox("Add Trailer Empty Weight and CG", value=False)
if add_trailer_weight:
    trailer_weight = st.sidebar.number_input("Trailer Empty Weight (lbs)", value=3500)
    trailer_cg = st.sidebar.number_input("Trailer Empty CG from Hitch (in)", value=90)
else:
    trailer_weight = 0
    trailer_cg = 0

# --- Helper Functions ---
def combined_cg(w1, x1, w2, x2):
    """Calculate combined center of gravity for two weights."""
    if w1 + w2 == 0:
        return 0
    return (w1 * x1 + w2 * x2) / (w1 + w2)

def compute_tongue_and_axle_loads(total_weight, total_cg, axle_positions):
    W = total_weight
    x_cg = total_cg
    x_axles = axle_positions
    n = len(x_axles)

    if n == 1:
        x1 = x_axles[0]
        A1 = W * x_cg / x1
        T = W - A1
        return T, [A1]

    elif n == 2:
        x1, x2 = x_axles
        A = np.array([
            [1, 1],
            [x1, x2]
        ])
        b = np.array([W, W * x_cg])
        axle_loads = np.linalg.solve(A, b)
        T = W - axle_loads.sum()
        return T, axle_loads.tolist()

# --- Calculations ---
total_weight = load_weight + trailer_weight
total_cg = combined_cg(load_weight, load_cg, trailer_weight, trailer_cg)

tongue_weight, axle_loads = compute_tongue_and_axle_loads(total_weight, total_cg, axle_positions)
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

    # Combined CG point
    ax.plot(total_cg, 0, "go")
    ax.text(total_cg, 0.2, f"{total_weight} lbs\nTotal CG", ha="center", fontsize=8)

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

        y_offset = height - 160 - 20 * len(axle_positions)
        c.drawString(50, y_offset, f"Load Weight: {load_weight} lbs")
        c.drawString(50, y_offset - 20, f"Load CG from Hitch: {load_cg} in")

        if add_trailer_weight:
            c.drawString(50, y_offset - 50, f"Trailer Empty Weight: {trailer_weight} lbs")
            c.drawString(50, y_offset - 70, f"Trailer Empty CG from Hitch: {trailer_cg} in")

        c.drawString(50, y_offset - 100, f"Total Weight: {total_weight} lbs")
        c.drawString(50, y_offset - 120, f"Total CG from Hitch: {total_cg:.1f} in")

        c.drawString(50, y_offset - 150, f"Tongue Weight: {tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")

        c.drawString(50, y_offset - 180, "Axle Loads:")
        y_pos = y_offset - 200
        for i, load in enumerate(axle_loads):
            c.drawString(70, y_pos, f"Axle {i+1}: {load:.1f} lbs")
            y_pos -= 20

        # Save the matplotlib figure to a bytes buffer as PNG
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        img = ImageReader(img_buffer)

        max_img_width = 400
        img_width, img_height = fig.get_size_inches()
        dpi = fig.dpi
        px_width, px_height = img_width * dpi, img_height * dpi
        aspect = px_height / px_width
        pdf_img_width = max_img_width
        pdf_img_height = max_img_width * aspect

        img_x = width - pdf_img_width - 50
        img_y = 50

        c.drawImage(img, img_x, img_y, width=pdf_img_width, height=pdf_img_height)

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
