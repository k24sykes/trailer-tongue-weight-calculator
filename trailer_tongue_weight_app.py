import streamlit as st
import matplotlib.pyplot as plt

st.title("Trailer Tongue Weight Calculator")

st.markdown("""
This tool calculates the tongue weight of a trailer based on component weights and distances from the hitch.
You can optionally include the trailer's own base weight and its center of gravity (CG) location.
""")

# Basic user inputs
num_components = st.number_input("Number of Components (e.g., generators, batteries, toolboxes, etc.)", min_value=1, step=1)

component_weights = []
component_distances = []

for i in range(int(num_components)):
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input(f"Component {i+1} Weight (lbs)", key=f"w{i}", step=10.0, format="%.1f")
    with col2:
        distance = st.number_input(f"Component {i+1} Distance from Hitch (in)", key=f"d{i}", step=1.0, format="%.1f")
    component_weights.append(weight)
    component_distances.append(distance)

# Optional trailer base weight and CG location
st.markdown("### Optional: Trailer Base Weight and CG")
trailer_weight = st.number_input(
    "Trailer Base Weight (lbs)",
    min_value=0.0,
    value=0.0,
    step=10.0,
    format="%.1f",
    help="Weight of the trailer structure itself"
)

trailer_cg = st.number_input(
    "Trailer CG Distance from Hitch (in)",
    min_value=0.0,
    value=0.0,
    step=1.0,
    format="%.1f",
    help="Location of the trailer's own center of gravity"
)

# Include trailer as an additional component if both values are non-zero
if trailer_weight > 0 and trailer_cg > 0:
    component_weights.append(trailer_weight)
    component_distances.append(trailer_cg)
    trailer_info = True
else:
    trailer_info = False

# Calculate tongue weight
total_moment = sum(w * d for w, d in zip(component_weights, component_distances))
total_weight = sum(component_weights)

if total_weight > 0:
    tongue_weight = total_moment / total_weight
    st.success(f"Estimated Tongue Weight: **{tongue_weight:.1f} lbs**")
else:
    st.warning("Please enter non-zero weights to calculate tongue weight.")

# Plotting
st.markdown("### Load Distribution Plot")
fig, ax = plt.subplots(figsize=(8, 2))
for i, (w, d) in enumerate(zip(component_weights, component_distances)):
    label = f"Component {i+1}" if i < num_components else "Trailer Base"
    ax.scatter(d, w, label=label)

ax.axvline(tongue_weight, color='red', linestyle='--', label='Tongue Point')
ax.set_xlabel("Distance from Hitch (in)")
ax.set_ylabel("Weight (lbs)")
ax.set_title("Component Weights and CGs")
ax.legend()
ax.grid(True)

st.pyplot(fig)

# Notes
if trailer_info:
    st.info(f"Trailer weight of **{trailer_weight:.1f} lbs** at **{trailer_cg:.1f} in** was included in the calculation.")
else:
    st.info("Trailer weight was not included (either weight or CG was zero).")
