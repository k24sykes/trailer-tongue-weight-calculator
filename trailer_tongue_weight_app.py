import streamlit as st
import matplotlib.pyplot as plt

# --- Sidebar Inputs ---
st.sidebar.title("Trailer Configuration")

num_weights = st.sidebar.number_input("Number of Loads", min_value=1, step=1, value=1)
weights = []
st.sidebar.markdown("#### Load Positions")
for i in range(num_weights):
    W = st.sidebar.number_input(f"Load {i+1} Weight (lbs)", value=2000, step=100)
    X = st.sidebar.number_input(f"Load {i+1} Distance from Hitch (in)", value=100, step=10)
    weights.append((W, X))

num_axles = st.sidebar.number_input("Number of Axles", min_value=1, step=1, value=2)
axles = []
st.sidebar.markdown("#### Axle Positions")
for i in range(num_axles):
    XA = st.sidebar.number_input(f"Axle {i+1} Position (in)", value=180 + i * 48, step=10)
    axles.append(XA)

# --- Calculation ---
def calculate_tongue_weight(weights, axles):
    total_weight = sum(W for W, _ in weights)
    total_moment = sum(W * X for W, X in weights)
    avg_axle_location = sum(axles) / len(axles)
    RA = total_moment / avg_axle_location
    tongue_weight = total_weight - RA
    tongue_weight_pct = (tongue_weight / total_weight) * 100
    return round(tongue_weight, 2), round(tongue_weight_pct, 2), avg_axle_location, total_weight

tongue_wt, tongue_pct, avg_axle, total_wt = calculate_tongue_weight(weights, axles)

# --- Results Output ---
st.title("📏 Trailer Tongue Weight Calculator")
st.markdown("This tool calculates the **tongue weight** and visualizes load distribution for any trailer setup.")

st.metric("Total Trailer Weight", f"{total_wt} lbs")
st.metric("Tongue Weight", f"{tongue_wt} lbs")
st.metric("Tongue % of Total", f"{tongue_pct}%")

if tongue_pct < 9:
    st.warning("⚠️ Tongue weight is too **low** — risk of trailer sway.")
elif tongue_pct > 15:
    st.warning("⚠️ Tongue weight is too **high** — risk of overloading the tow vehicle.")
else:
    st.success("✅ Tongue weight is within the recommended 10–15% range.")

# --- Plotting ---
fig, ax = plt.subplots(figsize=(10, 2.8))
trailer_length = max(max(axles) + 20, max(X for _, X in weights) + 20)

# Draw trailer base
ax.plot([0, trailer_length], [0, 0], 'k-', linewidth=2)

# Hitch
ax.plot(0, 0, 'ro')
ax.text(0, 0.15, 'Hitch\n(0 in)', ha='center', fontsize=8, color='r')

# Loads
for i, (W, X) in enumerate(weights):
    ax.plot(X, 0, 'bo')
    ax.text(X, 0.15, f'Load {i+1}\n({W} lbs)', ha='center', fontsize=8, color='b')

# Axles
for i, XA in enumerate(axles):
    ax.plot(XA, 0, 'gs')
    ax.text(XA, -0.2, f'Axle {i+1}\n({XA} in)', ha='center', fontsize=8, color='g')

# Tongue annotation
annotation_x = min(axles) / 2
ax.annotate(f'Tongue Weight:\n{tongue_wt} lbs ({tongue_pct}%)',
            xy=(0, 0), xytext=(annotation_x, 0.4),
            ha='center', fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="red", lw=1),
            arrowprops=dict(arrowstyle='->', color='red'))

ax.set_ylim(-0.4, 0.6)
ax.set_xlim(-10, trailer_length)
ax.axis('off')

plt.title("Trailer Load Layout", pad=20)
plt.tight_layout()
plt.subplots_adjust(bottom=0.25)
st.pyplot(fig)
