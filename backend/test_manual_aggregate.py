import json
import datetime
from fastapi.encoders import jsonable_encoder

with open('manual_daily_metrics.json', 'r') as f:
    manual_data = json.load(f)

def aggregate_manual_data(start_date_str, end_date_str):
    try:
        start_dt = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_dt = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
    except:
        return None
        
    current = start_dt
    
    aggr = {
        "volume": {"total_offered":0,"agent_offered":0,"answered":0,"wh_offered":0,"wh_answered":0,"travel_update_offered":0,"inbound_wh_offered":0},
        "service": {"sl_calls":0,"sl_pct":0,"al_pct":0,"avg_wait":0,"on_hold":0,"avg_hold":0},
        "efficiency": {"aht":0,"long_calls":0,"long_call_pct":0,"call_per_agent":0,"same_day_repeat":0,"repeat_pct":0},
        "failure": {"overall_abn":0,"net_abn":0,"net_abn_pct":0,"short_abn":0,"short_pct":0,"gross_abn_pct":0,"queue_level":0},
        "journey": {"intr_journey_pct":0,"travel_util_pct":0,"same_day_disp_repeat":0,"disp_repeat_pct":0}
    }
    
    chart_data = []
    
    total_wait_sec = 0
    total_hold_sec = 0
    total_handle_sec = 0
    
    days_counted = 0
    
    while current <= end_dt:
        date_str = current.strftime('%Y-%m-%d')
        if date_str in manual_data:
            day_data = manual_data[date_str]
            days_counted += 1
            
            # Volume
            aggr["volume"]["total_offered"] += day_data.get("total_offered", 0)
            aggr["volume"]["agent_offered"] += day_data.get("agent_offered", 0)
            aggr["volume"]["answered"] += day_data.get("answered", 0)
            aggr["volume"]["wh_offered"] += day_data.get("wh_offered", 0)
            aggr["volume"]["wh_answered"] += day_data.get("wh_answered", 0)
            aggr["volume"]["travel_update_offered"] += day_data.get("travel_update_offered", 0)
            aggr["volume"]["inbound_wh_offered"] += day_data.get("inbound_wh_offered", 0)
            
            # Service
            aggr["service"]["sl_calls"] += day_data.get("sl_calls", 0)
            aggr["service"]["on_hold"] += day_data.get("on_hold", 0)
            total_wait_sec += day_data.get("avg_wait", 0) * day_data.get("answered", 0) # approximation
            total_hold_sec += day_data.get("avg_hold", 0) * day_data.get("on_hold", 0)
            
            # Efficiency
            total_handle_sec += day_data.get("aht", 0) * day_data.get("answered", 0)
            aggr["efficiency"]["long_calls"] += day_data.get("long_calls", 0)
            aggr["efficiency"]["same_day_repeat"] += day_data.get("same_day_repeat", 0)
            
            # Failure
            aggr["failure"]["overall_abn"] += day_data.get("overall_abn", 0)
            aggr["failure"]["net_abn"] += day_data.get("net_abn", 0)
            aggr["failure"]["short_abn"] += day_data.get("short_abn", 0)
            aggr["failure"]["queue_level"] += day_data.get("queue_level", 0)
            
            # Journey
            aggr["journey"]["same_day_disp_repeat"] += day_data.get("same_day_disp_repeat", 0)
            
            # add to chart data
            chart_data.append({
                "period": date_str,
                "total_offered": day_data.get("total_offered", 0),
                "answered": day_data.get("answered", 0),
                "abandoned": day_data.get("overall_abn", 0),
                "sl_calls": day_data.get("sl_calls", 0)
            })
            
        current += datetime.timedelta(days=1)
        
    if days_counted == 0:
        return None
        
    # Recalculate percentages and averages
    ans = aggr["volume"]["answered"]
    off = aggr["volume"]["total_offered"]
    agnt_off = aggr["volume"]["agent_offered"]
    
    if ans > 0:
        aggr["service"]["sl_pct"] = round(aggr["service"]["sl_calls"] / ans, 4)
        aggr["service"]["al_pct"] = round(ans / agnt_off, 4) if agnt_off > 0 else 0
        aggr["service"]["avg_wait"] = round(total_wait_sec / ans)
        aggr["efficiency"]["aht"] = round(total_handle_sec / ans)
        aggr["efficiency"]["long_call_pct"] = round(aggr["efficiency"]["long_calls"] / ans, 4)
        aggr["efficiency"]["repeat_pct"] = round(aggr["efficiency"]["same_day_repeat"] / ans, 4)
        aggr["journey"]["disp_repeat_pct"] = round(aggr["journey"]["same_day_disp_repeat"] / ans, 4)
    if aggr["service"]["on_hold"] > 0:
        aggr["service"]["avg_hold"] = round(total_hold_sec / aggr["service"]["on_hold"])
    if off > 0:
        aggr["failure"]["gross_abn_pct"] = round(aggr["failure"]["overall_abn"] / off, 4)
        aggr["failure"]["net_abn_pct"] = round(aggr["failure"]["net_abn"] / off, 4)
        aggr["failure"]["short_pct"] = round(aggr["failure"]["short_abn"] / off, 4)
        
    # Missing intr_journey_pct, travel_util_pct, call_per_agent (just leave as 0)
    
    res = {
        "summary": aggr,
        "chart_data": chart_data,
        "distributions": {},
        "heatmap": [],
        "raw_count": int(off),
        "total_rows": int(off),
        "buckets": {"tta": {}, "duration": {}, "ratings": {}}
    }
    return res

print(json.dumps(aggregate_manual_data("2026-06-01", "2026-06-02"), indent=2))
