import MetaTrader5 as mt5
from datetime import datetime
import pytz

if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()
    exit()

print(f"MT5 Version: {mt5.version()}")

# Check for calendar functions
if hasattr(mt5, 'calendar_value_history'):
    print("calendar_value_history exists")
else:
    print("calendar_value_history MISSING")

if hasattr(mt5, 'calendar_value_history_by_country'):
    print("calendar_value_history_by_country exists")

try:
    # Try to fetch some data (e.g., last 24 hours)
    now = datetime.now(pytz.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Note: MT5 calendar functions might need specific arguments
    # calendar_value_history(country_code, start, end)
    # Let's try fetching for US (840)
    print("Attempting to fetch US calendar data...")
    # values = mt5.calendar_value_history("US", start, end) # This signature is hypothetical, need to check docs/experiment
    # Actually, let's check if we can get country list first
    
    countries = mt5.calendar_countries()
    if countries:
        print(f"Found {len(countries)} countries")
        us = next((c for c in countries if c.code == 'US' or c.name == 'United States'), None)
        if us:
            print(f"US Country ID: {us.id}")
            
            # Fetch events
            events = mt5.calendar_events(country_code=us.code) # or us.id?
            if events:
                 print(f"Found {len(events)} events for US")
            else:
                 print("No events found (or function failed silently)")
        else:
            print("US not found in country list")
    else:
        print("calendar_countries() returned None/Empty")

except Exception as e:
    print(f"Error during API test: {e}")

mt5.shutdown()
