import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🚚 Trailer Tongue Weight Calculator")

# Sidebar layout for inputs
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

# --- CALCULATIONS ---
total_weight = sum(component_weights)
total_moment = sum(w * d for w, d in zip(component_weights, component_distances))

if total_weight > 0 and len(axle_positions) > 0:
    avg_axle_pos = sum(axle_positions) / len(axle_positions)
    tongue_weight = (total_weight * avg_axle_pos - total_moment) / avg_axle_pos
    tongue_pct = tongue_weight / total_weight * 100
else:
    tongue_weight = 0
    tongue_pct = 0

# --- MAIN OUTPUT ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📊 Calculation Output")

    if total_weight > 0 and len(axle_positions) > 0:
        st.success(f"**Estimated Tongue Weight:** {tongue_weight:.1f} lbs")
        st.markdown(f"**Total Load:** {total_weight:.1f} lbs")
        st.markdown(f"**Tongue Weight Percentage:** {tongue_pct:.1f}%")

        if trailer_included:
            st.info(f"Included trailer base: {trailer_weight:.1f} lbs @ {trailer_cg:.1f} in")
        else:
            st.info("Trailer base not included.")

        # Warnings based on percentage
        if tongue_pct < 10:
            st.warning("⚠️ Tongue weight is **too low** (<10%). This may cause trailer sway.")
        elif tongue_pct > 15:
            st.warning("⚠️ Tongue weight is **too high** (>15%). This may overload the hitch or rear axle.")
        else:
            st.success("✅ Tongue weight is within the recommended 10-15% range.")
    else:
        st.warning("Please enter valid weights and axle positions to calculate tongue weight.")

# --- PLOTTING ---
with col2:
    st.markdown("### 📈 Load Distribution Plot")

    fig, ax = plt.subplots(figsize=(10, 3))

    # Plot components
    for i, (w, d) in enumerate(zip(component_weights, component_distances)):
        label = f"Component {i+1}" if i < num_components else "Trailer Base"
        ax.scatter(d, w, color='blue', label=label)
        ax.text(d, w + 50, f"{label}\n{w:.0f} lbs", ha='center', fontsize=8)

    # Plot axles
    for i, ax_pos in enumerate(axle_positions):
        ax.axvline(ax_pos, color='gray', linestyle='--', label=f'Axle {i+1}')
        ax.text(ax_pos, 0, f'Axle {i+1}', rotation=90, va='bottom', ha='center', fontsize=8, color='gray')

    # Plot hitch line
    ax.axvline(0, color='red', linestyle='--', label='Hitch')
    ax.text(0, 0, 'Hitch', rotation=90, va='bottom', ha='right', fontsize=8, color='red')

    ax.set_xlabel("Distance from Hitch (in)")
    ax.set_ylabel("Weight (lbs)")
    ax.set_title("Trailer Load Distribution")
    ax.grid(True)
    ax.set_xlim(left=-10)
    ax.legend(loc='upper right', fontsize=8)
    st.pyplot(fig)
