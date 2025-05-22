import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📦 Trailer Tongue Weight Calculator")

# Sidebar inputs
st.sidebar.header("🔧 Component Setup")

# Component inputs
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

# Add trailer as a "component" if both fields are valid
if trailer_weight > 0 and trailer_cg > 0:
    component_weights.append(trailer_weight)
    component_distances.append(trailer_cg)
    trailer_included = True
else:
    trailer_included = False

# Axle input
st.sidebar.markdown("### 🚛 Axle Configuration")
num_axles = st.sidebar.number_input("Number of Axles", min_value=1, max_value=4, step=1)
axle_positions = []

for i in range(int(num_axles)):
    axle_pos = st.sidebar.number_input(f"Axle {i+1} Distance from Hitch (in)", step=1.0, format="%.1f", key=f"a{i}")
    axle_positions.append(axle_pos)

# Calculate total load and CG
total_weight = sum(component_weights)
total_moment = sum(w * d for w, d in zip(component_weights, component_distances))

# Reaction calculation (assuming all axles act as a single support point)
if len(axle_positions) > 0:
    avg_axle_pos = sum(axle_positions) / len(axle_positions)
    tongue_weight = total_weight - (total_moment - total_weight * avg_axle_pos) / (0 if avg_axle_pos == 0 else avg_axle_pos)
else:
    tongue_weight = 0

# Main display
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📊 Calculation Output")

    if total_weight > 0 and len(axle_positions) > 0:
        st.success(f"**Estimated Tongue Weight:** {tongue_weight:.1f} lbs")
        st.markdown(f"**Total Load:** {total_weight:.1f} lbs")
        if trailer_included:
            st.info(f"Included trailer base: {trailer_weight:.1f} lbs @ {trailer_cg:.1f} in")
        else:
            st.info("Trailer base not included.")
    else:
        st.warning("Please input valid component weights and axle locations.")

with col2:
    st.markdown("### 🖼️ Load Distribution")

    fig, ax = plt.subplots(figsize=(10, 2))

    for i, (w, d) in enumerate(zip(component_weights, component_distances)):
        label = f"Component {i+1}" if i < num_components else "Trailer Base"
        ax.scatter(d, w, label=label, s=100)

    for i, ax_pos in enumerate(axle_positions):
        ax.axvline(ax_pos, color='gray', linestyle='--', label=f'Axle {i+1}')

    ax.axvline(x=0, color='red', linestyle='--', label='Hitch')
    ax.set_xlabel("Distance from Hitch (in)")
    ax.set_ylabel("Weight (lbs)")
    ax.legend(loc='upper right')
    ax.grid(True)
    st.pyplot(fig)
