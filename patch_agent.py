import os

agent_path = r"c:\Users\User\Desktop\trading_terminal\agents\agent_bundle_AI_MODEL_V7_1\agent.py"

with open(agent_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patch the import block to print the error
old_block = """try:
    import onnxruntime as ort
except ImportError:  # pragma: no cover - runtime requirement
    ort = None"""

new_block = """try:
    import onnxruntime as ort
except ImportError as e:
    print(f"CRITICAL AGENT IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
    ort = None"""

if old_block in content:
    new_content = content.replace(old_block, new_block)
    with open(agent_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched agent.py to show import errors.")
else:
    print("Could not find the import block to patch. It might have been patched already.")
