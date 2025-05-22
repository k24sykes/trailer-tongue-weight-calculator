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

#
