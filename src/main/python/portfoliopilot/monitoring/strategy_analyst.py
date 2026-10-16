# monitoring/strategy_analyst.py
import os
import pandas as pd


class SelfAnalysisDecisionEngine:
    def __init__(self, summary_matrix_path: str):
        self.matrix_path = summary_matrix_path

    def discover_optimal_configuration(self, priority_metric: str = "Sharpe_Ratio") -> dict:
        if not os.path.exists(self.matrix_path):
            return {"status": "error", "message": "Metrics tracker file missing."}

        df = pd.read_csv(self.matrix_path)
        if df.empty:
            return {"status": "error", "message": "Metrics database is empty."}
        df.columns = [col.strip() for col in df.columns]

        sorted_matrix = df.sort_values(by=priority_metric, ascending=(priority_metric == "Max_Drawdown_Pct"))

        # FIXED: Corrected invalid pandas index reference assignment
        best_run = sorted_matrix.iloc[0]

        recommendation = {
            "Label": best_run["Label"], "Zone": best_run["Zone"],
            "Strategy": best_run["Strategy"], "Universe": best_run["Universe"], "Analyst": best_run["Analyst_Layer"],
            "Net_Return": f"{best_run['Net_Return_Pct']}%", "Sharpe_Ratio": best_run["Sharpe_Ratio"],
            "Max_Drawdown": f"{best_run['Max_Drawdown_Pct']}%"
        }

        print("\n==================================================================")
        print(f"   🤖  PORTFOLIO PILOT N-DIMENSIONAL META-REASONING WINNER REPORT ")
        print("==================================================================")
        print(f" ✅ Top Experiment Track    : {recommendation['Label']}")
        print(f" 📈 Optimal Strategy Model  : {recommendation['Strategy']}")
        print(f" 🌍 Optimal Capital Sector  : {recommendation['Universe']} ({recommendation['Zone']})")
        print(f" 🧠 Optimal Reasoning Layer : {recommendation['Analyst']}")
        print(" ────────────────────────────────────────────────────────────────")
        print(f" 💵 Expected Net Return     : {recommendation['Net_Return']}")
        print(f" 🎯 Expected Sharpe Ratio   : {recommendation['Sharpe_Ratio']}")
        print(f" 📉 Anticipated Max Drawdown: {recommendation['Max_Drawdown']}")
        print("==================================================================\n")
        return recommendation
