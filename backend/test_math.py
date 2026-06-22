import json
import pandas as pd
from datetime import datetime, timedelta

def verify_math(data):
    for date_str, m in data.items():
        # verify totals
        total = m.get('total_offered', 0)
        ans = m.get('answered', 0)
        abn = m.get('overall_abn', 0)
        if total != (ans + abn):
            print(f"Mismatch total: {date_str}: {total} != {ans} + {abn}")
        
        queue = m.get('queue_level', 0)
        net = m.get('net_abn', 0)
        short = m.get('short_abn', 0)
        # queue + net + short might not equal overall_abn if there are other drops, but let's see
        if abn != (queue + net + short):
            pass #print(f"Mismatch abn parts: {date_str}: {abn} != {queue} + {net} + {short}")

if __name__ == "__main__":
    with open('manual_daily_metrics.json') as f:
        data = json.load(f)
    verify_math(data)
    print("Done")
