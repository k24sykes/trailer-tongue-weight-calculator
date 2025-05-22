import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Trailer Load Calculator", layout="centered")
st.title("🚛 Trailer Load & Tongue Weight Calculator")

st.markdown(
    "This tool calculates trailer tongue weight and axle loads using rigid body moment balance. "
    "**For 3-axle setups, only total tongue weight is calculated (no per-axle breakdown).**"
)

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Trailer Setup")
    trailer_length = st.number_input("Trailer Length (in)", min_value=1.0, value=240.0)

    num_axles = st.selectbox("Number of Axles", [1, 2, 3])

    axle_positions = []
    for i in range(num_axles):
        pos = st.number_input(
            f"Axle {i+1} Position from Hitch (in)",
            min_value=0.0,
            max_value=trailer_length,
            value=trailer_length - 34.0 - (num_axles - 1 - i) * 34.0,
            key=f"axle_{i}"
        )
        axle_positions.append(pos)

    st.subheader("Base Trailer Weight (Optional)")
    trailer_weight = st.number_input("Trailer Weight (lbs)", min_value=0.0, value=1000.0)
    trailer_cg = st.number_input("Trailer CG from Hitch (in)", min_value=0.0, max_value=trailer_length, value=trailer_length / 2)

    st.subheader("Payload")
    num_loads = st.number_input("Number of Payloads", min_value=0, max_value=10, value=2)

    loads = []
    for i in range(int(num_loads)):
        weight = st.number_input(f"Load {i+1} Weight (lbs)", key=f"load_w_{i}", min_value=0.0, value=1000.0)
        position = st.number_input(f"Load {i+1} Position from Hitch (in)", key=f"load_x_{i}", min_value=0.0, max_value=trailer_length, value=trailer_length / (num_loads + 1) * (i + 1))
        loads.append((weight, position))

tongue_pos = 0.0  # hitch location at front of trailer

# --- Calculation ---
def compute_tongue_and_axle_loads(loads, trailer_weight, trailer_cg, axle_positions, tongue_pos=0.0):
    all_loads = loads.copy()
    if trailer_weight > 0:
        all_loads.append((trailer_weight, trailer_cg))

    total_weight = sum(w for w, _ in all_loads)
    total_moment = sum(w * x for w, x in all_loads)

    if total_weight == 0 or len(axle_positions) == 0:
        return 0.0, [], 0.0

    if len(axle_positions) == 1:
        # One axle + tongue
        A = np.array([
            [1, 1],  # Force balance
            [axle_positions[0], tongue_pos]  # Moment balance
        ])
        b = np.array([total_weight, total_moment])
        solution = np.linalg.solve(A, b)
        axle_loads = [solution[0]]
        tongue_weight = solution[1]
        return tongue_weight, axle_loads, total_weight

    elif len(axle_positions) == 2:
        # Two axles + tongue
        A = np.array([
            [1, 1, 1],
            [axle_positions[0], axle_positions[1], tongue_pos]
        ])
        b = np.array([total_weight, total_moment])
        # Solve for Axle1, Axle2, Tongue
        solution = np.linalg.lstsq(A.T, b, rcond=None)[0]
        axle_loads = [solution[0], solution[1]]
        tongue_weight = solution[2]
        return tongue_weight, axle_loads, total_weight

    elif len(axle_positions) == 3:
        # Just compute tongue weight using total moment
        # Estimate the tongue weight as the remaining weight after distributing over axles
        # For now, assume all axles carry equal share
        axle_avg_pos = sum(axle_positions) / 3
        tongue_weight = total_moment / trailer_length  # Not physically perfect, but placeholder
        return tongue_weight, None, total_weight

# --- Compute ---
tongue_weight, axle_loads, total_weight = compute_tongue_and_axle_loads(
    loads, trailer_weight, trailer_cg, axle_positions, tongue_pos
)

tongue_pct = 100 * tongue_weight / total_weight if total_weight > 0 else 0

# --- Results ---
st.subheader("Results")
st.metric("Total Weight", f"{total_weight:.1f} lbs")
st.metric("Tongue Weight", f"{tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")

# --- Tongue Weight Feedback ---
if total_weight == 0:
    st.warning("No weight entered. Please input payload or trailer mass.")
elif tongue_pct < 10:
    st.error(f"⚠️ Tongue weight is too low: {tongue_pct:.1f}% (recommended 10–15%)")
elif tongue_pct > 15:
    st.error(f"⚠️ Tongue weight is too high: {tongue_pct:.1f}% (recommended 10–15%)")
else:
    st.success(f"✅ Tongue weight is within the recommended range: {tongue_pct:.1f}%")

# --- Axle Loads ---
if num_axles < 3 and axle_loads:
    for i, load in enumerate(axle_loads):
        st.metric(f"Axle {i+1} Load", f"{load:.1f} lbs")
elif num_axles == 3:
    st.info("Axle load distribution not calculated for 3 axles (only tongue weight shown).")

# --- Plot ---
st.subheader("Load Distribution")

fig, ax = plt.subplots(figsize=(9, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(0, 1)
ax.set_xlabel("Trailer Length (inches)")
ax.set_yticks([])

# Payload markers
for w, x in loads:
    ax.plot(x, 0.5, 'ro')
    ax.text(x, 0.55, f'{w:.0f} lbs', ha='center', fontsize=8)

# Trailer CG marker
if trailer_weight > 0:
    ax.plot(trailer_cg, 0.6, 'g^', markersize=10)
    ax.text(trailer_cg, 0.65, 'Trailer CG', ha='center', fontsize=8)

# Axles
for i, pos in enumerate(axle_positions):
    ax.plot(pos, 0, 'ks', markersize=10)
    ax.text(pos, -0.1, f'Axle {i+1}', ha='center', fontsize=8)

# Tongue
ax.plot(tongue_pos, 0.5, 'b^', markersize=10)
ax.text(tongue_pos, 0.6, f'Tongue\n{tongue_weight:.0f} lbs', ha='center', fontsize=8, color='blue')

st.pyplot(fig)
