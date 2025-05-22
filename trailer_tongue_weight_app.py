import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🚚 Trailer Tongue Weight & Axle Load Calculator")

# Sidebar for input
st.sidebar.header("🔧 Component Setup")
num_components = st.sidebar.number_input("Number of Components", min_value=1, step=1)
component_weights = []
component_distances = []

for i in range(int(num_components)):
    component_weights.append(
        st.sidebar.number_input(f"Component {i+1} Weight (lbs)", step=10.0, format="%.1f", key=f"w{i}")
    )
    component_distances.append(
        st.sidebar.number_input(f"Component {i+1} Distance from Hitch (in)", step=1.0, format="%.1f", key=f"d{i}")
    )

# Optional trailer base weight
st.sidebar.markdown("### 🏗️ Optional: Trailer Base")
trailer_weight = st.sidebar.number_input("Trailer Base Weight (lbs)", min_value=0.0, step=10.0, format="%.1f")
trailer_cg = st.sidebar.number_input("Trailer CG from Hitch (in)", min_value=0.0, step=1.0, format="%.1f")

if trailer_weight > 0 and trailer_cg > 0:
    component_weights.append(trailer_weight)
    component_distances.append(trailer_cg)
    trailer_included = True
else:
    trailer_included = False

# Axle positions
st.sidebar.markdown("### 🚛 Axle Configuration")
num_axles = st.sidebar.number_input("Number of Axles", min_value=1, max_value=4, step=1)
axle_positions = []

for i in range(int(num_axles)):
    pos = st.sidebar.number_input(f"Axle {i+1} Position from Hitch (in)", step=1.0, format="%.1f", key=f"a{i}")
    axle_positions.append(pos)

# --- CALCULATIONS ---
total_weight = sum(component_weights)
total_moment = sum(w * d for w, d in zip(component_weights, component_distances))
avg_axle_pos = sum(axle_positions) / len(axle_positions) if axle_positions else 0

if total_weight > 0 and avg_axle_pos > 0:
    tongue_weight = (total_weight * avg_axle_pos - total_moment) / avg_axle_pos
    tongue_pct = tongue_weight / total_weight * 100
else:
    tongue_weight = 0
    tongue_pct = 0

# --- Axle Load Distribution (simple statics, assuming beam and point loads) ---
def compute_axle_loads(axles, weights, distances):
    if len(axles) == 0:
        return []

    axle_loads = [0.0] * len(axles)

    for w, d in zip(weights, distances):
        # Simple proportional load distribution based on distance to each axle
        total_inv_dist = sum(1 / abs(axle - d) if axle != d else 1e6 for axle in axles)
        for i, axle in enumerate(axles):
            inv_dist = 1 / abs(axle - d) if axle != d else 1e6
            ratio = inv_dist / total_inv_dist
            axle_loads[i] += w * ratio

    return axle_loads

axle_loads = compute_axle_loads(axle_positions, component_weights, component_distances)

# --- DISPLAY OUTPUT ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📊 Results")
    st.markdown(f"**Total Load:** {total_weight:.1f} lbs ({total_weight * 0.4536:.1f} kg)")
    st.markdown(f"**Tongue Weight:** {tongue_weight:.1f} lbs ({tongue_weight * 0.4536:.1f} kg)")
    st.markdown(f"**Tongue Weight %:** {tongue_pct:.1f}%")

    if tongue_pct < 10:
        st.warning("⚠️ Tongue weight is too low (<10%).")
    elif tongue_pct > 15:
        st.warning("⚠️ Tongue weight is too high (>15%).")
    else:
        st.success("✅ Tongue weight is within the 10–15% range.")

    st.markdown("### ⚖️ Axle Loads")
    for i, load in enumerate(axle_loads):
        st.markdown(f"- **Axle {i+1} Load:** {load:.1f} lbs ({load * 0.4536:.1f} kg)")

# --- PLOTTING ---
with col2:
    st.markdown("### 📈 Load Distribution (Linear Layout)")

    fig, ax = plt.subplots(figsize=(10, 2))
    y = 0  # All points on single horizontal line

    # Plot each component
    for i, (w, d) in enumerate(zip(component_weights, component_distances)):
        label = f"Component {i+1}" if i < num_components else "Trailer Base"
        ax.scatter(d, y, color='blue', s=60)
        ax.text(d, y + 0.2, f"{label}\n{w:.0f} lbs\n({w*0.4536:.0f} kg)", ha='center', fontsize=8)

    # Plot axles
    for i, ax_pos in enumerate(axle_positions):
        ax.axvline(ax_pos, color='gray', linestyle='--')
        ax.text(ax_pos, y - 0.4, f"Axle {i+1}", ha='center', fontsize=8, color='gray')

    # Hitch at 0
    ax.axvline(0, color='red', linestyle='--')
    ax.text(0, y - 0.4, "Hitch", ha='right', fontsize=8, color='red')

    ax.set_yticks([])
    ax.set_xlabel("Distance from Hitch (in / mm)")
    ax.set_xlim(left=-10)
    ax.grid(True, axis='x', linestyle=':', color='lightgray')
    st.pyplot(fig)
