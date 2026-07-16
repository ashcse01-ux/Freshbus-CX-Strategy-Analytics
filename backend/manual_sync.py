import asyncio
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from routers.sync import bootstrap_historical_data

print("Starting manual sync...")
asyncio.run(bootstrap_historical_data())
print("Sync complete.")
