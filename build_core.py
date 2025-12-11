
from setuptools import setup
from Cython.Build import cythonize
import os
import glob
from setuptools.extension import Extension

# Core modules to protect
# Reduced scope to ensure success and protect ONLY the Secret Key
modules = [
    "core/license_manager.py"
]

# Convert to Extension objects
extensions = []
for file in modules:
    # Module name should use dots instead of slashes, e.g. core.license_manager
    module_name = file.replace(".py", "").replace("/", ".").replace("\\", ".")
    extensions.append(Extension(module_name, [file]))

print("🚀 Compiling Core Modules to Binary (.pyd)...")
print(f"Targets: {modules}")

setup(
    ext_modules=cythonize(extensions, 
        compiler_directives={'language_level': "3", 'always_allow_keywords': True},
        annotate=False
    ),
)
