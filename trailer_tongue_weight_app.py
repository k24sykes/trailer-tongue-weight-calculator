import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide", page_title="Trailer Tongue Weight Calculator")

st.title("📦 Trailer Tongue Weight Calculator")

# Sidebar inputs
st.sidebar.header("Trailer Inputs")

trailer_length = st.sidebar.number_input("Trailer Length from Hitch (in)", value=214)
load_weight = st.sidebar.number_input("Load Weight (lbs)", value=11305)
load_cg = st.sidebar.number_input("Load CG from Hitch (in)", value=139)

st.sidebar.markdown("---")
st.sidebar.header("Axle Setup")

axle1 = st.sidebar.number_input("Axle 1 Position (in)", value=134)
axle2 = st.sidebar.number_input("Axle 2 Position (in)", value=170)

# --- Calculations ---
virtual_axle = (axle1 + axle2) / 2
moment_about_axle = load_weight * (load_cg - virtual_axle)
distance_hitch_to_axle = virtual_axle

tongue_force = moment_about_axle / distance_hitch_to_axle
axle_force = load_weight - tongue_force

# Show tongue force as positive for display
tongue_weight_display = abs(tongue_force)
tongue_pct = 100 * tongue_weight_display / load_weight if load_weight else 0

# --- Warnings & Info ---
st.subheader("Results")
st.metric("Tongue Weight", f"{tongue_weight_display:.1f} lbs", f"{tongue_pct:.1f}%")
st.metric("Axle Load", f"{axle_force:.1f} lbs")
if tongue_force < 0:
    st.warning("⚠️ Negative tongue weight indicates the trailer would lift at the hitch! Recheck CG or axle position.")

# --- Plotting ---
fig, ax = plt.subplots(figsize=(10, 3))
ax.set_xlim(0, trailer_length)
ax.set_ylim(-1, 1)
ax.get_yaxis().set_visible(False)
ax.set_xlabel("Distance from Hitch (in)")

# Hitch
ax.axvline(0, color='black', linestyle='--', label="Hitch")

# Load CG
ax.plot(load_cg, 0, "go")
ax.text(load_cg, 0.2, f"{load_weight} lbs\nLoad CG", ha="center", fontsize=8)

# Axles
ax.axvline(axle1, color="blue", linestyle=":")
ax.axvline(axle2, color="blue", linestyle=":")
ax.text(axle1, -0.3, f"A1 ({axle1} in)", ha="center", fontsize=8)
ax.text(axle2, -0.3, f"A2 ({axle2} in)", ha="center", fontsize=8)

# Virtual axle
ax.axvline(virtual_axle, color="purple", linestyle="--")
ax.text(virtual_axle, -0.6, "Virtual Axle", ha="center", fontsize=8, color="purple")

ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.5), ncol=3)
st.pyplot(fig)

# --- Assumptions Note ---
with st.expander("ℹ️ Assumptions Used in This Model"):
    st.markdown("""
    - This model assumes **two axles are replaced by a single virtual axle** located at their midpoint.
    - Load is treated as a **single point mass** applied at its center of gravity.
    - **Static equilibrium (moments and vertical forces)** are used to solve for the tongue and axle forces.
    - Tongue weight is **always shown as positive**, but a warning is issued if it would cause upward force (lifting).
    - Does not account for dynamic effects, uneven loading, or real axle spreads.
    """)
