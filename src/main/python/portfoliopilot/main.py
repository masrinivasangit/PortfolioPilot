# main.py
import configparser
import os
import sys
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# 🛠️ NATIVE PATH FIX: Tell Python to look in the current folder for signals.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Now these imports will work perfectly regardless of your folder depth
from signals import MomentumSignalModule
from engine import ModularPortfolioEngine


class MasterApplicationController:
    def __init__(self):
        # Automatically look for config.properties right next to main.py
        self.config_path = os.path.join(current_dir, "config.properties")
        self.config = configparser.ConfigParser()
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.config_path):
            print(f"❌ Error: Configuration file missing!")
            print(f"Please ensure 'config.properties' is placed in: {current_dir}")
            sys.exit(1)

        self.config.read(self.config_path)
        self.mode = self.config.get("MARKET_SETTINGS", "run_mode", fallback="BACKTEST").upper()
        self.country = self.config.get("MARKET_SETTINGS", "market_country", fallback="US").upper()
        self.budget = self.config.getfloat("MARKET_SETTINGS", "total_budget", fallback=50000.00)

    def launch(self):
        print("omsivayanama om ")
        print("==================================================================")
        print("    ✈️  MYPILOTPORTFOLIO MASTER CORE SYSTEM INITIALIZED  ✈️")
        print("==================================================================")
        print(f"⏰ System Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏳️  Market Zone : [{self.country}]")
        print(f"🛡️  Capital Pool: {self.budget:,.2f}")
        print(f"⚙️  System Mode : [{self.mode}]")
        print("==================================================================\n")

        if self.mode == "BACKTEST":
            print("📊 Starting Phase 1: Historical Data Simulation Engine...")
            engine = ModularPortfolioEngine(config_path=self.config_path)
            engine.run_simulation()
            print("\n✅ Simulation complete. Check your generated reports in the project directory.")

        elif self.mode in ["PAPER", "LIVE"]:
            if self.mode == "LIVE":
                print("⚠️  WARNING: LIVE REAL-MONEY MODE ARMED. EXECUTING LIVE TRADES ON CYCLE.")
            else:
                print("🧪 Initializing Phase 2: Paper Trading Live-Simulation Environment...")

            scheduler = BackgroundScheduler()
            cron_h = self.config.getint("SCHEDULE_SETTINGS", "hour", fallback=15)
            cron_m = self.config.getint("SCHEDULE_SETTINGS", "minute", fallback=0)
            cron_w = self.config.get("SCHEDULE_SETTINGS", "day_of_week", fallback="fri").lower()

            def scheduled_execution_job():
                print(f"\n⚡ [CLOCK TRIGGERED] Running Live/Paper Cycle scan for {self.country} market...")

            scheduler.add_job(scheduled_execution_job, 'cron', day_of_week=cron_w, hour=cron_h, minute=cron_m)
            scheduler.start()

            print(f"📡 Background core running actively. Awaiting scheduler trigger...")
            print(f"📅 Schedule Rule: Wakes up every '{cron_w.upper()}' at {cron_h:02d}:{cron_m:02d} local time.")
            print("👉 Leave PyCharm running. Press Stop in PyCharm to close down safely.\n")

            try:
                while True:
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                scheduler.shutdown()
                print("\n👋 Application background scheduler stopped cleanly.")


if __name__ == "__main__":
    app = MasterApplicationController()
    app.launch()
