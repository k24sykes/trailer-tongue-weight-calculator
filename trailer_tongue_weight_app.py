import streamlit as st
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

st.set_page_config(layout="wide")
st.title("Trailer Tongue Weight Calculator (Simplified Model)")

st.sidebar.header("Inputs")

# Inputs
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=214)
num_axles = st.sidebar.selectbox("Number of Axles", [1, 2], index=1)

axle_positions = []
for i in range(num_axles):
    default_pos = 134 + 36 * i
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=default_pos)
    axle_positions.append(pos)

load_weight = st.sidebar.number_input("Load Weight (lbs)", value=11305)
load_cg = st.sidebar.number_input("Load CG from Hitch (in)", value=139)

trailer_frame_weight = st.sidebar.number_input("Trailer Frame Weight (lbs)", value=0)
trailer_frame_cg = st.sidebar.number_input("Trailer Frame CG from Hitch (in)", value=0)

st.sidebar.markdown("""
**Assumptions:**

- Trailer load is simplified as single vertical force at specified CG.
- Trailer frame weight acts at given CG.
- Axle forces combined into single virtual axle at midpoint of axles.
- Tongue weight is vertical force on hitch (positive = downward).
""")

# Calculate virtual axle midpoint
if num_axles == 1:
    virtual_axle = axle_positions[0]
else:
    virtual_axle = sum(axle_positions) / len(axle_positions)

# Total weight and moment about hitch
total_weight = load_weight + trailer_frame_weight
total_moment = (load_weight * load_cg) + (trailer_frame_weight * trailer_frame_cg)

# Avoid division by zero
if virtual_axle == 0:
    st.error("Virtual axle position cannot be zero.")
    st.stop()

# Calculate axle load (force at virtual axle)
axle_load = total_moment / virtual_axle

# Calculate tongue weight
tongue_weight = total_weight - axle_load

# Sanity check: tongue_weight should be positive (downwards force on hitch)
# If negative, means load CG is behind axle midpoint (unusual)
tongue_weight_positive = abs(tongue_weight)

# Calculate percentage of tongue weight relative to total weight
tongue_pct = 100 * (tongue_weight_positive / total_weight) if total_weight != 0 else 0

# Warnings based on tongue weight percentage
if total_weight == 0:
    st.warning("Total trailer weight is zero.")
elif tongue_weight < 0:
    st.warning("Tongue weight calculated as negative. Load CG may be behind axle midpoint.")
elif tongue_pct < 10:
    st.warning(f"Tongue weight is low: {tongue_pct:.1f}% (Recommended 10-15%)")
elif tongue_pct > 15:
    st.warning(f"Tongue weight is high: {tongue_pct:.1f}% (Recommended 10-15%)")
else:
    st.success(f"Tongue weight is within acceptable range: {tongue_pct:.1f}%")

# Display results
st.subheader("Results")
st.write(f"Total Weight = {total_weight:.1f} lbs")
st.write(f"Virtual Axle Position = {virtual_axle:.1f} in")
st.write(f"Axle Load = {axle_load:.1f} lbs")
st.write(f"Tongue Weight = {tongue_weight_positive:.1f} lbs ({tongue_pct:.1f}%)")

# Plotting
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(-1, 1)
ax.get_yaxis().set_visible(False)
ax.set_xlabel("Distance from Hitch (in)")

# Hitch line
ax.axvline(0, color='black', linestyle='--', label='Hitch (0 in)')

# Load CG
ax.plot(load_cg, 0, "go", label="Load CG")
ax.text(load_cg, 0.3, f"Load\n{load_weight} lbs\n@ {load_cg} in", ha="center", fontsize=8)

# Trailer frame CG if any
if trailer_frame_weight > 0:
    ax.plot(trailer_frame_cg, 0, "ro", label="Trailer Frame CG")
    ax.text(trailer_frame_cg, 0.3, f"Frame\n{trailer_frame_weight} lbs\n@ {trailer_frame_cg} in", ha="center", fontsize=8)

# Axles
for i, pos in enumerate(axle_positions):
    ax.axvline(pos, color='blue', linestyle=':', label=f'Axle {i+1}' if i==0 else None)
    ax.text(pos, -0.3, f"Axle {i+1}\n{pos:.0f} in", ha="center", fontsize=8)

# Virtual axle midpoint
ax.axvline(virtual_axle, color='purple', linestyle='-', label='Virtual Axle Midpoint')
ax.text(virtual_axle, -0.6, f"Virtual Axle\n{virtual_axle:.1f} in", ha="center", fontsize=8, color='purple')

ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=4)

st.pyplot(fig)

# --- PDF Export ---

def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Trailer Tongue Weight Calculation", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Trailer Length: {trailer_length} in", ln=True)
    pdf.cell(0, 8, f"Number of Axles: {num_axles}", ln=True)
    for i, pos in enumerate(axle_positions):
        pdf.cell(0, 8, f"Axle {i+1} Position: {pos} in", ln=True)
    pdf.cell(0, 8, f"Load Weight: {load_weight} lbs", ln=True)
    pdf.cell(0, 8, f"Load CG: {load_cg} in from hitch", ln=True)
    pdf.cell(0, 8, f"Trailer Frame Weight: {trailer_frame_weight} lbs", ln=True)
    pdf.cell(0, 8, f"Trailer Frame CG: {trailer_frame_cg} in from hitch", ln=True)
    pdf.ln(10)

    pdf.cell(0, 8, f"Total Weight: {total_weight:.1f} lbs", ln=True)
    pdf.cell(0, 8, f"Virtual Axle Position: {virtual_axle:.1f} in", ln=True)
    pdf.cell(0, 8, f"Axle Load: {axle_load:.1f} lbs", ln=True)
    pdf.cell(0, 8, f"Tongue Weight: {tongue_weight_positive:.1f} lbs ({tongue_pct:.1f}%)", ln=True)
    pdf.ln(10)

    # Add plot as image to PDF
    # Save plot to bytes buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='PNG', bbox_inches='tight')
    buf.seek(0)
    pdf.image(buf, x=10, y=None, w=pdf.w - 20)  # Leave margin

    pdf_output = "trailer_tongue_weight_report.pdf"
    pdf.output(pdf_output)
    return pdf_output

if st.button("Export PDF Report"):
    pdf_file = export_pdf()
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF", f, file_name=pdf_file)

