"""
Dependency Manager - Auto-check and install requirements
"""
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    import pkg_resources
except ImportError:
    # Fallback if pkg_resources not available
    pkg_resources = None


def check_and_install_dependencies(bundle_path: Path):
    """
    Check and install dependencies from requirements.txt
    
    Args:
        bundle_path: Path to agent bundle
    """
    if getattr(sys, 'frozen', False):
        logger.info(f"Running in frozen mode, skipping dependency check for '{bundle_path.name}'")
        return

    req_file = Path(bundle_path) / "requirements.txt"
    
    if not req_file.exists():
        logger.debug(f"No requirements.txt found in {bundle_path.name}")
        return
    
    logger.info(f"Checking dependencies for '{bundle_path.name}'...")
    
    with open(req_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not requirements:
        return
    
    missing = []
    
    for req in requirements:
        # Extract package name (remove version constraints)
        pkg_name = req.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
        
        if pkg_resources:
            try:
                pkg_resources.get_distribution(pkg_name)
                logger.debug(f"  ✓ {pkg_name} already installed")
            except pkg_resources.DistributionNotFound:
                missing.append(req)
                logger.warning(f"  ✗ {pkg_name} not found")
        else:
            # Fallback: try import
            try:
                __import__(pkg_name.replace('-', '_'))
                logger.debug(f"  ✓ {pkg_name} already installed")
            except ImportError:
                missing.append(req)
                logger.warning(f"  ✗ {pkg_name} not found")
    
    if missing:
        logger.info(f"Installing {len(missing)} missing package(s): {missing}")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            logger.info("✓ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            logger.error(e.stderr.decode() if e.stderr else "Unknown error")
            raise RuntimeError(f"Dependency installation failed for '{bundle_path.name}'")
    else:
        logger.info(f"✓ All dependencies satisfied for '{bundle_path.name}'")
