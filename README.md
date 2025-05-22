# 🚛 Trailer Tongue Weight Calculator

This web app helps engineers and operators calculate the tongue weight of a bumper-pull trailer with 1 or more loads and any number of axles.

Built with [Streamlit](https://streamlit.io), this tool provides a fast and visual way to estimate whether your tongue weight falls within the recommended 10–15% range of the total trailer weight.

---

## 🔧 Features

- Support for **1 or more machines/loads**.
- Configure **any number of axles** (1–3 or more).
- Visual plot of your trailer layout including:
  - Hitch
  - Load positions
  - Axle positions
  - Tongue weight annotation
- Auto-calculates:
  - Total trailer weight
  - Tongue weight in lbs
  - Tongue weight percentage
  - Warning messages if your tongue weight is out of spec

---

## 🚀 How to Use

1. Go to the live app: [[https://YOUR-APP-LINK-HERE](https://YOUR-APP-LINK-HERE)](https://trailer-tongue-weight-calculator.streamlit.app/)
2. Use the sidebar to:
   - Input the number of loads (machines).
   - Enter weight and hitch distance for each.
   - Input the number of axles and their distances from the hitch.
3. Review the metrics and diagram to assess safety and load balance.

---

## 🧰 Tech Stack

- **Python**
- **Streamlit**
- **Matplotlib**

---

## 📥 Run Locally (Optional)

If you'd rather run this app on your local machine:

1. Clone the repo:

   ```bash
   git clone https://github.com/k24sykes/trailer-tongue-weight-app.git
   cd trailer-tongue-weight-app
