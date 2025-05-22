import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- Page config ---
st.set_page_config(layout="wide")
st.sidebar.title("Trailer Load Inputs")

# --- Sidebar Inputs ---
trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=214)
num_axles = st.sidebar.selectbox("Number of Axles", [1, 2, 3], index=1)

axle_positions = []
for i in range(num_axles):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", value=134 + 36 * i)
    axle_positions.append(pos)

trailer_weight = st.sidebar.number_input("Trailer Load Weight (lbs)", value=11305)
trailer_cg = st.sidebar.number_input("Load Center of Gravity from Hitch (in)", value=100)

# --- Helper Function ---
def compute_tongue_and_axle_loads(trailer_weight, trailer_cg, axle_positions):
    n = len(axle_positions)
    total_weight = trailer_weight
    total_moment = trailer_weight * trailer_cg

    if n == 1:
        x = axle_positions[0]
        axle_load = total_moment / x
        tongue_weight = total_weight - axle_load
        return tongue_weight, [axle_load]

    elif n == 2:
        A = np.array([
            [1, 1],
            [axle_positions[0], axle_positions[1]]
        ])
        b = np.array([total_weight, total_moment])
        try:
            axle_loads = np.linalg.solve(A, b)
            tongue_weight = total_weight - np.sum(axle_loads)
            return tongue_weight, axle_loads.tolist()
        except np.linalg.LinAlgError:
            return 0, [0, 0]

    else:  # 3 axles
        # Only calculate tongue weight using total moment and total weight
        avg_axle_pos = sum(axle_positions) / n
        axle_load_est = total_moment / avg_axle_pos
        tongue_weight = total_weight - axle_load_est
        return tongue_weight, []

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

    # Trailer load
    ax.plot(trailer_cg, 0, "go")
    ax.text(trailer_cg, 0.2, f"{trailer_weight} lbs\nLoad", ha="center", fontsize=8)

    # Axles
    for i, x in enumerate(axle_positions):
        ax.axvline(x, color="blue", linestyle=":")
        if i < len(axle_loads):
            ax.text(x, -0.3, f"Axle {i+1}\n{axle_loads[i]:.0f} lbs", ha="center", fontsize=8)
        else:
            ax.text(x, -0.3, f"Axle {i+1}", ha="center", fontsize=8)

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
