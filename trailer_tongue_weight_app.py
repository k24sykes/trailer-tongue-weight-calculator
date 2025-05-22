import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Trailer Load Calculator", layout="centered")
st.title("🚛 Trailer Load & Tongue Weight Calculator")

st.markdown("This tool calculates trailer tongue weight and axle loads using moment balance. "
            "Useful for designing trailers or loading equipment properly.")

# --- Inputs ---
with st.sidebar:
    st.header("Trailer Setup")

    trailer_length = st.number_input("Trailer Length (inches)", min_value=1.0, value=240.0, step=1.0)
    num_axles = st.selectbox("Number of Axles", [1, 2, 3])
    axle_spacing = st.number_input("Spacing Between Axles (inches)", min_value=0.0, value=34.0)

    tongue_pos = 0.0  # Assume hitch is at front (x=0)

    st.subheader("Trailer Base Weight (Optional)")
    trailer_weight = st.number_input("Trailer Weight (lbs)", min_value=0.0, value=0.0)
    trailer_cg = st.number_input("Trailer CG from Front (inches)", min_value=0.0, max_value=trailer_length, value=trailer_length / 2)

    st.subheader("Assume Tongue Weight % (for 2–3 axles)")
    assumed_tongue_pct = st.slider("Assumed Tongue Weight %", 0, 25, 10)

st.subheader("Load Inputs")
num_loads = st.number_input("Number of Loads", min_value=0, max_value=10, value=2)

loads = []
for i in range(int(num_loads)):
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input(f"Load {i+1} Weight (lbs)", key=f"weight_{i}", min_value=0.0, value=1000.0)
    with col2:
        position = st.number_input(f"Load {i+1} CG Position (in)", key=f"pos_{i}", min_value=0.0, max_value=trailer_length, value=(trailer_length / 4) * (i+1))
    loads.append((weight, position))

# Compute axle positions
if num_axles == 1:
    axle_positions = [trailer_length - 20]  # Single axle near rear
elif num_axles == 2:
    center = trailer_length - 34  # 34" from rear
    axle_positions = [center - axle_spacing / 2, center + axle_spacing / 2]
else:
    center = trailer_length - 50  # 50" from rear
    axle_positions = [center - axle_spacing, center, center + axle_spacing]

# --- Calculation Function ---
def compute_tongue_and_axle_loads(loads, trailer_weight, trailer_cg, axle_positions, tongue_pos=0, assumed_tongue_pct=None):
    loads_copy = loads.copy()
    if trailer_weight > 0 and trailer_cg > 0:
        loads_copy.append((trailer_weight, trailer_cg))

    total_weight = sum(w for w, _ in loads_copy)
    total_moment = sum(w * x for w, x in loads_copy)
    n = len(axle_positions)

    if n == 0 or total_weight == 0:
        return 0, [], total_weight

    if n == 1:
        A = np.array([
            [1, 1],
            [axle_positions[0], tongue_pos]
        ])
        b = np.array([total_weight, total_moment])
        solution = np.linalg.solve(A, b)
        axle_loads = [solution[0]]
        tongue_weight = solution[1]
        return tongue_weight, axle_loads, total_weight

    if n == 2:
        if assumed_tongue_pct is not None:
            tongue_weight = assumed_tongue_pct * total_weight / 100
            b_new = np.array([total_weight - tongue_weight, total_moment - tongue_weight * tongue_pos])
            A = np.array([
                [1, 1],
                [axle_positions[0], axle_positions[1]]
            ])
            axle_loads = np.linalg.solve(A, b_new)
            return tongue_weight, axle_loads.tolist(), total_weight
        else:
            tongue_weight = 0
            b_new = np.array([total_weight, total_moment])
            A = np.array([
                [1, 1],
                [axle_positions[0], axle_positions[1]]
            ])
            axle_loads = np.linalg.solve(A, b_new)
            return tongue_weight, axle_loads.tolist(), total_weight

    if n == 3:
        if assumed_tongue_pct is not None:
            tongue_weight = assumed_tongue_pct * total_weight / 100
            b_new = np.array([total_weight - tongue_weight, total_moment - tongue_weight * tongue_pos])
            A = np.array([
                [1, 1, 1],
                [axle_positions[0], axle_positions[1], axle_positions[2]]
            ])
            axle_loads, *_ = np.linalg.lstsq(A, b_new, rcond=None)
            return tongue_weight, axle_loads.tolist(), total_weight
        else:
            return 0, [0]*3, total_weight

# --- Calculate ---
tongue_weight, axle_loads, total_weight = compute_tongue_and_axle_loads(
    loads, trailer_weight, trailer_cg, axle_positions, tongue_pos=0, assumed_tongue_pct=assumed_tongue_pct
)

tongue_pct = 100 * tongue_weight / total_weight if total_weight > 0 else 0

# --- Display Results ---
st.subheader("Results")
st.metric("Total Weight", f"{total_weight:.1f} lbs")
st.metric("Tongue Weight", f"{tongue_weight:.1f} lbs ({tongue_pct:.1f}%)")

for i, load in enumerate(axle_loads):
    st.metric(f"Axle {i+1} Load", f"{load:.1f} lbs")

# --- Plot ---
st.subheader("Load Distribution")
fig, ax = plt.subplots(figsize=(8, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(0, 1)
ax.set_xlabel("Trailer Length (inches)")
ax.set_yticks([])

# Draw loads
for w, x in loads:
    ax.plot(x, 0.5, 'ro')
    ax.text(x, 0.55, f'{w:.0f} lbs', ha='center', fontsize=8)

# Draw axle positions
for i, pos in enumerate(axle_positions):
    ax.plot(pos, 0, 'ks', markersize=10)
    ax.text(pos, -0.1, f'Axle {i+1}', ha='center', fontsize=8)

# Draw trailer CG if given
if trailer_weight > 0:
    ax.plot(trailer_cg, 0.6, 'g^', markersize=10)
    ax.text(trailer_cg, 0.65, 'Trailer CG', ha='center', fontsize=8)

# Draw tongue
ax.plot(tongue_pos, 0.5, 'b^', markersize=10)
ax.text(tongue_pos, 0.6, f'Tongue\n{tongue_weight:.0f} lbs', ha='center', fontsize=8, color='blue')

st.pyplot(fig)
