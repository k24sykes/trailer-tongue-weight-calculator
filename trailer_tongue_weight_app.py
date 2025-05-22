import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import base64
from io import BytesIO

st.set_page_config(layout="wide")
st.sidebar.title("Trailer Load Input")

# --- Input Section ---
st.sidebar.markdown("### Trailer Info")
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=200)
trailer_weight = st.sidebar.number_input("Trailer Weight (lbs) *(Optional)*", value=0)
trailer_cg = st.sidebar.number_input("Trailer CoG from Hitch (in) *(Optional)*", value=0)

st.sidebar.markdown("---")
num_axles = st.sidebar.selectbox("Number of Axles", [1, 2, 3], index=1)
axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=100 + 30 * i)
    axle_positions.append(pos)

st.sidebar.markdown("---")
num_loads = st.sidebar.number_input("Number of Additional Loads", min_value=1, max_value=10, value=1)
loads = []
for i in range(num_loads):
    weight = st.sidebar.number_input(f"Load {i+1} Weight (lbs)", value=1000, key=f"w{i}")
    position = st.sidebar.number_input(f"Load {i+1} Position from Hitch (in)", value=100, key=f"p{i}")
    loads.append((weight, position))

# --- Helper Function ---
def compute_tongue_and_axle_loads(loads, trailer_weight, trailer_cg, axle_positions):
    if trailer_weight > 0:
        loads.append((trailer_weight, trailer_cg))

    total_weight = sum(w for w, _ in loads)
    total_moment = sum(w * x for w, x in loads)
    n = len(axle_positions)

    A = np.zeros((2, n + 1))  # [T, R1, R2, ...]
    b = np.zeros(2)

    # Sum of vertical forces = 0
    A[0, 0] = 1  # Tongue weight
    A[0, 1:] = 1  # Axle reactions
    b[0] = total_weight

    # Sum of moments about hitch = 0
    A[1, 1:] = axle_positions  # Moment arms for axle reactions
    b[1] = total_moment

    try:
        solution = np.linalg.solve(A, b)
        tongue_weight = solution[0]
        axle_loads = solution[1:]
    except np.linalg.LinAlgError:
        tongue_weight = 0
        axle_loads = [0] * n

    return tongue_weight, axle_loads, total_weight

# --- Computation ---
tongue_weight, axle_loads, total_weight = compute_tongue_and_axle_loads(
    loads[:], trailer_weight, trailer_cg, axle_positions
)
tongue_pct = 100 * tongue_weight / total_weight if total_weight else 0

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

    ax.axvline(0, color="black", linestyle="--", label="Hitch (0 in)")

    for i, (w, x) in enumerate(loads):
        ax.plot(x, 0, "ro")
        ax.text(x, 0.1 + 0.05 * (i % 3), f"{w} lbs", ha="center", fontsize=8)
        ax.text(x, -0.15, f"Load {i+1}", ha="center", fontsize=7)

    if trailer_weight > 0:
        ax.plot(trailer_cg, 0, "go")
        ax.text(trailer_cg, 0.25, f"{trailer_weight} lbs\n(Trailer)", ha="center", fontsize=7)

    for i, (x, load) in enumerate(zip(axle_positions, axle_loads)):
        ax.axvline(x, color="blue", linestyle=":")
        ax.text(x, -0.4, f"Axle {i+1}\n{load:.0f} lbs", ha="center", fontsize=8)

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

# --- PDF Export ---
st.markdown("---")
st.subheader("Export Results to PDF")

def create_pdf(tongue_weight, tongue_pct, axle_loads):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Trailer Load Calculation Results", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Tongue Weight: {tongue_weight:.1f} lbs", ln=True)
    pdf.cell(200, 10, txt=f"Tongue Weight Percentage: {tongue_pct:.1f}%", ln=True)
    pdf.ln(5)
    for i, load in enumerate(axle_loads):
        pdf.cell(200, 10, txt=f"Axle {i+1} Load: {load:.1f} lbs", ln=True)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="trailer_results.pdf">📄 Download PDF</a>'

if st.button("Generate PDF"):
    pdf_link = create_pdf(tongue_weight, tongue_pct, axle_loads)
    st.markdown(pdf_link, unsafe_allow_html=True)
