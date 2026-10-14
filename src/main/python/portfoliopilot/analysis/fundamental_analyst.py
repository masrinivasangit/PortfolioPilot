class FundamentalAnalystAgent:
    def __init__(self):
        pass

    def evaluate_health(self, fundamental_metrics: dict) -> float:
        """Returns a corporate health score between 0.0 (poor) and 1.0 (excellent)."""
        if "error" in fundamental_metrics or not fundamental_metrics:
            return 0.5

        score = 0.5
        # Example metric scoring rule logic
        d2e = fundamental_metrics.get("debt_to_equity")
        op_margin = fundamental_metrics.get("operating_margin")

        if d2e and d2e < 100: score += 0.2
        if op_margin and op_margin > 0.15: score += 0.2
        return min(max(score, 0.0), 1.0)
