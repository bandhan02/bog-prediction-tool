\# BOG Rate Prediction \& Management Optimization System



AI-driven boil-off gas prediction and management tool for LNG carriers.  

Built using a Physics-Informed Neural Network (PINN) with MINLP optimization.



\*\*Author:\*\* Bandhan | Lithuanian Maritime Academy | Marine Engineering  

\*\*Status:\*\* Phase 0 — Environment Setup  

\*\*Target MAPE:\*\* < 5% on synthetic voyage dataset



---



\## 🚢 Project Overview

This project predicts Boil-Off Gas (BOG) generation on LNG carriers using a hybrid approach:



\- Physics-based thermodynamics (CoolProp)

\- Machine learning models (XGBoost + PINN)

\- MINLP optimization for BOG management (Pyomo + IPOPT)

\- Interactive dashboard for real-time monitoring (Streamlit + Plotly)



The goal is to build a fully deployable LNG engineering tool that can simulate, predict, and optimize BOG rates during voyages.



---



\## 🧰 Tech Stack



\### \*\*Core Libraries\*\*

\- \*\*CoolProp\*\* — Cryogenic fluid properties  

\- \*\*NumPy / Pandas / SciPy\*\* — Data processing  

\- \*\*Matplotlib / Plotly\*\* — Visualization  

\- \*\*Scikit-learn / XGBoost\*\* — Baseline ML models  

\- \*\*PyTorch\*\* — Physics-Informed Neural Network (PINN)  

\- \*\*Pyomo + IPOPT\*\* — MINLP optimization  

\- \*\*Streamlit\*\* — Dashboard UI  



---



\## Project Structure

/data — synthetic voyage datasets  

/models — trained PINN and XGBoost model files  

/optimization — Pyomo MINLP optimizer  

/dashboard — Streamlit app  

/validation — benchmarking scripts  

/paper — technical paper drafts





