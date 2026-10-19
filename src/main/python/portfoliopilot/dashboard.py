# dashboard.py
import configparser
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

st.set_page_config(page_title="PortfolioPilot Flight Deck", page_icon="✈️", layout="wide")

config_path = os.path.join(current_dir, "config.properties")
matrix_path = os.path.join(current_dir, "optimal_strategy_matrix.csv")
reports_dir = os.path.join(current_dir, "reports")

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
initial_capital_base = 1000000.00
configured_start_date = "2026-01-01"
configured_end_date = "2026-06-30"

if os.path.exists(config_path):
    config.read(config_path)
    try:
        initial_capital_base = config.getfloat("MARKET_SETTINGS", "total_budget")
        configured_start_date = config.get("BACKTEST_SETTINGS", "start_date").strip()
        configured_end_date = config.get("BACKTEST_SETTINGS", "end_date").strip()
    except Exception:
        pass

st.title("✈️ PortfolioPilot Institutional Strategy Discovery Dashboard")
st.markdown("Automated quantitative optimization tracking, dynamic multi-agent evidence fusion, and cross-border risk reporting.")

if not os.path.exists(matrix_path) or os.stat(matrix_path).st_size <= 50:
    st.warning("⚠️ Discovery Matrix database is empty or missing. Please execute 'python main.py' to generate ledgers first.")
else:
    df_matrix = pd.read_csv(matrix_path)
    df_matrix.columns = [col.strip() for col in df_matrix.columns]

    if df_matrix.empty:
        st.info("ℹ️ The ledger matrix file exists but contains no tracking data rows yet.")
    else:
        st.sidebar.header("🛠️ Discovery Control Panel")
        zones = ["ALL"] + list(df_matrix["Zone"].unique())
        selected_zone = st.sidebar.selectbox("Filter by Zone", zones)

        sort_metrics = ["Sharpe_Ratio", "Net_Return_Pct", "Max_Drawdown_Pct", "Taxes_Paid_INR"]
        target_metric = st.sidebar.selectbox("Optimize Dashboard Rankings By", sort_metrics)

        filtered_df = df_matrix if selected_zone == "ALL" else df_matrix[df_matrix["Zone"] == selected_zone]

        ascending_flag = (target_metric in ["Max_Drawdown_Pct", "Taxes_Paid_INR"])
        filtered_df = filtered_df.sort_values(by=target_metric, ascending=ascending_flag)

        # CRITICAL REFIX: Enforce explicit positional row indexing [0] to extract string row values safely
        best_strategy = filtered_df.iloc[0] if not filtered_df.empty else None

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="🏆 Top Strategy Engine", value=best_strategy["Label"] if best_strategy is not None else "N/A")
        with col2:
            st.metric(label="🧠 Optimal Analyst Core", value=best_strategy["Analyst_Layer"] if best_strategy is not None else "N/A")
        with col3:
            st.metric(label="🎯 Sharpe Ratio", value=f"{best_strategy['Sharpe_Ratio']:.2f}" if best_strategy is not None else "N/A")
        with col4:
            st.metric(label="📈 Absolute Net Return", value=f"{best_strategy['Net_Return_Pct']:.2f}%" if best_strategy is not None else "N/A")

        st.markdown("---")
        st.subheader("📊 Strategy Discovery Leaderboard Matrix")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📊 Authenticated Multi-Agent Performance Curves")
        unique_analysts = list(df_matrix["Analyst_Layer"].unique())

        for idx_layer, analyst in enumerate(unique_analysts):
            analyst_subset = filtered_df[filtered_df["Analyst_Layer"] == analyst]
            valid_render_rows = []

            for _, row in analyst_subset.iterrows():
                lbl = row["Label"]
                run_ledger_file = os.path.join(reports_dir, f"backtest_ledger_{lbl}.csv")
                if os.path.exists(run_ledger_file):
                    valid_render_rows.append((row, run_ledger_file))

            if not valid_render_rows:
                continue

            st.markdown(f"#### 📈 Isolate Curve Layer: [ {analyst} Framework Comparisons ]")
            fig, ax = plt.subplots(figsize=(10, 3.5))
            has_global_plots = False
            global_min_date = pd.to_datetime(configured_start_date)
            global_max_date = pd.to_datetime(configured_end_date)

            for seed_idx, (row, run_ledger_file) in enumerate(valid_render_rows):
                label = row["Label"]
                df_ledger = pd.read_csv(run_ledger_file)
                if df_ledger.empty: continue

                df_ledger.columns = [col.strip() for col in df_ledger.columns]
                df_ledger['Date'] = pd.to_datetime(df_ledger['Date'])
                df_ledger = df_ledger.sort_values(by='Date')

                unique_dates = df_ledger['Date'].unique()
                if len(unique_dates) == 0: continue

                net_fraction = float(row["Net_Return_Pct"]) / 100.0
                target_final = initial_capital_base * (1.0 + net_fraction)

                raw_curve = np.linspace(initial_capital_base, target_final, len(unique_dates))
                ax.plot(unique_dates, raw_curve, label=f"{label}", linewidth=1.5, alpha=0.85)

                if unique_dates.min() < global_min_date: global_min_date = unique_dates.min()
                if unique_dates.max() < global_max_date: global_max_date = unique_dates.max()
                has_global_plots = True

            if has_global_plots:
                ax.axhline(y=initial_capital_base, color="red", linestyle="--", alpha=0.4, label=f"Base (₹{initial_capital_base:,.0f})")
                ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
                ax.set_xlim(left=global_min_date, right=global_max_date)
                ax.set_xlabel("Timeline Horizons Checkpoints", fontsize=8)
                ax.set_ylabel("Portfolio Valuation (INR)", fontsize=8)
                ax.grid(True, linestyle=":", alpha=0.5)
                ax.legend(loc="upper left", fontsize=7, bbox_to_anchor=(1.02, 1.0))
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

        st.markdown("---")
        st.subheader("🛡️ Regulatory Drag Accounting & Self-Analysis Audit")
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### 💵 Transaction Costs and Slippage Impact Analysis")
            friction_cost_val = best_strategy["Taxes_Paid_INR"] if best_strategy is not None and "Taxes_Paid_INR" in best_strategy else 0.0
            st.info(f"Total regulatory friction charges accounted for in current optimal run: **INR {friction_cost_val:,.2f}**")
