import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import io

st.set_page_config(layout="wide")
st.sidebar.title("Trailer Load Input")

# --- Sidebar Inputs ---
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=200)
tongue_pos = st.sidebar.number_input("Tongue Position from Hitch (in)", value=0.0)
trailer_weight = st.sidebar.number_input("Trailer Weight (lbs) — optional", value=0)
trailer_cg = st.sidebar.number_input("Trailer CoG from Hitch (in) — optional", value=0)

num_axles = st.sidebar.selectbox("Number of Axles", [1, 2, 3], index=1)
axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=100 + 30 * i)
    axle_positions.append(pos)

num_loads = st.sidebar.number_input("Number of Additional Loads", min_value=0, max_value=10, value=1)
loads = []
for i in range(num_loads):
    weight = st.sidebar.number_input(f"Load {i+1} Weight (lbs)", value=1000, key=f"w{i}")
    position = st.sidebar.number_input(f"Load {i+1} Position from Hitch (in)", value=100, key=f"p{i}")
    loads.append((weight, position))

# --- Load Calculation ---
def compute_tongue_and_axle_loads(loads, trailer_weight, trailer_cg, axle_positions, tongue_pos=0.0):
    all_loads = loads.copy()
    if trailer_weight > 0:
        all_loads.append((trailer_weight, trailer_cg))

    total_weight = sum(w for w, _ in all_loads)
    if total_weight == 0 or len(axle_positions) == 0:
        return 0.0, [], 0.0

    if len(axle_positions) == 1:
        A = np.array([
            [1, 1],
            [axle_positions[0], tongue_pos]
        ])
        b = np.array([total_weight, sum(w * x for w, x in all_loads)])
        solution = np.linalg.solve(A, b)
        axle_loads = [solution[0]]
        tongue_weight = solution[1]
        return tongue_weight, axle_loads, total_weight

    elif len(axle_positions) == 2:
        a1, a2 = axle_positions
        moment_about_a1 = sum(w * (x - a1) for w, x in all_loads)
        A = np.array([[a2 - a1, -a1]])
        b = np.array([moment_about_a1])
        solution = np.linalg.lstsq(A, b, rcond=None)[0]
        r2, tongue_weight = solution
        r1 = total_weight - r2 - tongue_weight
        axle_loads = [r1, r2]
        return tongue_weight, axle_loads, total_weight

    elif len(axle_positions) == 3:
        avg_axle_pos = sum(axle_positions) / 3
        total_moment = sum(w * x for w, x in all_loads)
        tongue_weight = (total_weight * avg_axle_pos - total_moment) / avg_axle_pos
        return tongue_weight, None, total_weight

# --- Run Calculation ---
tongue_weight, axle_loads, total_weight = compute_tongue_and_axle_loads(
    loads, trailer_weight, trailer_cg, axle_positions, tongue_pos
)

tongue_pct = 100 * tongue_weight / total_weight if total_weight > 0 else 0

# --- Warnings ---
if total_weight == 0:
    st.warning("Total load weight is zero. Please input loads or trailer weight.")
elif tongue_pct < 10:
    st.warning(f"Tongue weight is too low: {tongue_pct:.1f}% (Recommended: 10–15%)")
elif tongue_pct > 15:
    st.warning(f"Tongue weight is too high: {tongue_pct:.1f}% (Recommended: 10–15%)")
else:
    st.success(f"Tongue weight is in acceptable range: {tongue_pct:.1f}%")

# --- Layout Columns ---
col1, col2 = st.columns([2, 1])

# --- Trailer Diagram Plot ---
with col1:
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.set_xlim(0, trailer_length)
    ax.set_ylim(-1, 1)
    ax.get_yaxis().set_visible(False)
    ax.set_xlabel("Trailer Length from Hitch (in)")

    ax.axvline(tongue_pos, color="black", linestyle="--", label="Tongue")

    for i, (w, x) in enumerate(loads):
        ax.plot(x, 0, "ro")
        ax.text(x, 0.15, f"{w} lbs", ha="center", fontsize=8)
        ax.text(x, -0.15, f"Load {i+1}", ha="center", fontsize=7)

    if trailer_weight > 0 and trailer_cg > 0:
        ax.plot(trailer_cg, 0, "go")
        ax.text(trailer_cg, 0.25, f"{trailer_weight} lbs\n(Trailer)", ha="center", fontsize=7)

    for i, x in enumerate(axle_positions):
        ax.axvline(x, color="blue", linestyle=":")
        if axle_loads and i < len(axle_loads):
            ax.text(x, -0.4, f"Axle {i+1}\n{axle_loads[i]:.0f} lbs", ha="center", fontsize=8)
        else:
            ax.text(x, -0.4, f"Axle {i+1}", ha="center", fontsize=8)

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.65), ncol=4)
    st.pyplot(fig)

# --- Bar Chart of Axle Loads ---
with col2:
    st.subheader("Axle Load Sharing")
    if axle_loads:
        labels = [f"Axle {i+1}" for i in range(len(axle_loads))]
        fig2, ax2 = plt.subplots()
        ax2.barh(labels, axle_loads, color="skyblue")
        ax2.set_xlabel("Load (lbs)")
        st.pyplot(fig2)
    else:
        st.info("No axle load breakdown available for 3 axles.")

# --- Export to PDF ---
def create_pdf(tongue_weight, tongue_pct, axle_loads):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Tongue Weight Calculator Results", ln=True, align="C")
    pdf.ln()

    pdf.cell(200, 10, txt=f"Total Weight: {total_weight:.1f} lbs", ln=True)
    pdf.cell(200, 10, txt=f"Tongue Weight: {tongue_weight:.1f} lbs ({tongue_pct:.1f}%)", ln=True)
    pdf.ln()
    if axle_loads:
        for i, load in enumerate(axle_loads):
            pdf.cell(200, 10, txt=f"Axle {i+1} Load: {load:.1f} lbs", ln=True)
    else:
        pdf.cell(200, 10, txt="Axle loads not shown for 3-axle configuration", ln=True)

    # Plot images
    buf1 = io.BytesIO()
    fig.savefig(buf1, format="png", bbox_inches="tight")
    buf1.seek(0)
    pdf.image(buf1, x=10, y=pdf.get_y(), w=190)
    pdf.ln(65)

    if axle_loads:
        buf2 = io.BytesIO()
        fig2.savefig(buf2, format="png", bbox_inches="tight")
        buf2.seek(0)
        pdf.image(buf2, x=10, y=pdf.get_y(), w=190)

    return pdf.output(dest="S").encode("latin-1")

if st.button("Export Results to PDF"):
    pdf_data = create_pdf(tongue_weight, tongue_pct, axle_loads)
    st.download_button(
        label="Download PDF",
        data=pdf_data,
        file_name="tongue_weight_report.pdf",
        mime="application/pdf",
    )
