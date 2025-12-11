import os
import shutil
import sys
import tkinter

def main():
    print("Patching Tkinter Dependencies...")
    
    # 1. Locate Target Directory (PyInstaller output)
    target_dir = os.path.join(os.getcwd(), "dist", "AlphaQuantPro", "_internal")
    if not os.path.exists(target_dir):
        # Maybe not using _internal (older PyInstaller?)
        target_dir = os.path.join(os.getcwd(), "dist", "AlphaQuantPro")
    
    print(f"Target Dir: {target_dir}")
    
    # 2. Locate Source Tcl/Tk Data
    # Option A: From python env
    python_root = os.path.dirname(sys.executable)
    tcl_src = os.path.join(python_root, "tcl")
    
    # Option B: From tkinter
    try:
        tk = tkinter.Tk()
        tcl_root_var = tk.tk.exprstring('$tcl_library')
        tk_root_var = tk.tk.exprstring('$tk_library')
        tk.destroy()
        print(f"Tkinter reports: Tcl={tcl_root_var}, Tk={tk_root_var}")
    except Exception as e:
        print(f"Warning: Could not query Tkinter: {e}")

    # Explicit copy
    # We need to copy 'tcl8.6' folder to '{target_dir}/tcl8.6' OR '{target_dir}/_tcl_data' depending on what rthook wants?
    # The error said: "Tcl data directory ...\_internal\_tcl_data not found"
    # Actually, recent PyInstaller expects certain layout.
    
    # Let's try copying 'tcl' folders to target root
    src_tcl86 = os.path.join(tcl_src, "tcl8.6")
    src_tk86 = os.path.join(tcl_src, "tk8.6")
    
    if os.path.exists(src_tcl86) and os.path.exists(src_tk86):
        # Copy to _internal/tcl8.6
        shutil.copytree(src_tcl86, os.path.join(target_dir, "tcl8.6"), dirs_exist_ok=True)
        shutil.copytree(src_tk86, os.path.join(target_dir, "tk8.6"), dirs_exist_ok=True)
        print("Copied tcl8.6 and tk8.6")
        
        # ALSO Try copying to tcl/ folder inside (some configs want that)
        tcl_sub = os.path.join(target_dir, "tcl")
        os.makedirs(tcl_sub, exist_ok=True)
        shutil.copytree(src_tcl86, os.path.join(tcl_sub, "tcl8.6"), dirs_exist_ok=True)
        shutil.copytree(src_tk86, os.path.join(tcl_sub, "tk8.6"), dirs_exist_ok=True)
        print("Copied to tcl/ subdir")

    # Fix: Create _tcl_data marker or folder if needed? 
    # The error explicitely mentioned "_tcl_data". 
    # Some hooks look for this folder.
    tcl_data_folder = os.path.join(target_dir, "_tcl_data")
    if not os.path.exists(tcl_data_folder):
         os.makedirs(tcl_data_folder, exist_ok=True)
         # Copy contents of tcl8.6 into it? Or just exist?
         pass # Just creating it might not be enough if it needs content.
         
    # Let's assume tcl8.6 and tk8.6 beside executable or in _internal is enough for standard hook.
    # If using custom hook, might be different.
    
    print("Done patching.")

if __name__ == "__main__":
    main()
