
import sys
import os
import json
import datetime
import numpy as np

# Mock the sanitize function from web_server.py
def _sanitize(obj):
    if hasattr(obj, 'item'): # Numpy scalar
        return obj.item()
    if hasattr(obj, 'tolist'): # Numpy array
        return obj.tolist()
    if hasattr(obj, 'isoformat'): # Datetime
        return obj.isoformat()
    return obj

def test_sanitization():
    print("Testing Sanitization Logic...")
    
    # Create problematic data
    data = {
        "metrics": {
            "win_rate": np.float64(55.5),
            "total_trades": np.int64(100),
            "start_time": datetime.datetime.now()
        },
        "curve": {
            "times": [datetime.datetime.now(), datetime.datetime.now()],
            "equity": [np.float64(1000.0), np.float64(1050.5)]
        }
    }
    
    print(f"Original Data Types: {type(data['metrics']['win_rate'])}")
    
    # Apply logic from web_server.py
    metrics = data['metrics']
    curve = data['curve']
    
    safe_metrics = {k: _sanitize(v) for k, v in metrics.items()}
    safe_times = [_sanitize(t) for t in curve.get('times', [])]
    safe_equity = [_sanitize(e) for e in curve.get('equity', [])]
    
    final_response = {
        "metrics": safe_metrics,
        "equity_curve": {'times': safe_times, 'equity': safe_equity}
    }
    
    try:
        json_str = json.dumps(final_response)
        print("✅ Serialization Successful!")
        print(f"Result: {json_str[:100]}...")
        return True
    except TypeError as e:
        print(f"❌ Serialization Failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sanitization()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
