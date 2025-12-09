
import os

agent_path = r'agents\agent_bundle_alpha_prime\agent.py'

with open(agent_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'def compute_features(df):' in content:
    print("compute_features already exists.")
else:
    # Insert after imports
    target = 'from typing import List, Dict, Optional'
    injection = '''from typing import List, Dict, Optional
from feature_engineering import FeatureEngineerV2

def compute_features(df):
    """
    Custom feature computation hook for Agent Adapter.
    Returns the feature vector for the last candle.
    """
    try:
        fe = FeatureEngineerV2()
        # process() returns DataFrame with features
        df_features = fe.process(df)
        
        # Return the last row as numpy array
        # Ensure we return float32 to match expected type
        return df_features.iloc[-1].values.astype("float32")
    except Exception as e:
        print(f"Error in alpha_prime compute_features: {e}")
        return None
'''
    new_content = content.replace(target, injection)
    
    with open(agent_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched agent.py")
