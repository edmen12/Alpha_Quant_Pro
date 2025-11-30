"""
自动更新检查模块 (Auto Update Checker)

检查 GitHub Releases 获取最新版本，并提示用户下载。
"""
import requests
import threading
from packaging import version
import logging

logger = logging.getLogger(__name__)

# 应用版本信息
CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "edmen12/Alpha_Quant_Pro"  # GitHub 仓库
CHECK_UPDATE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class UpdateChecker:
    """
    更新检查器
    
    在后台线程检查 GitHub Releases，不阻塞 UI。
    """
    
    def __init__(self, current_version=CURRENT_VERSION):
        self.current_version = current_version
        self.latest_version = None
        self.download_url = None
        self.changelog = None
        self.update_available = False
        
    def check_for_updates(self, callback=None):
        """
        检查更新（异步）
        
        Args:
            callback: 回调函数，接收 (update_available, latest_version, download_url, changelog)
        """
        def _check():
            try:
                logger.info("Checking for updates...")
                response = requests.get(CHECK_UPDATE_URL, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    self.latest_version = data["tag_name"].lstrip("v")
                    self.changelog = data.get("body", "")
                    
                    # Use Release Page URL so user can see instructions for split installer
                    self.download_url = data.get("html_url", "")

                    
                    # 比较版本
                    if version.parse(self.latest_version) > version.parse(self.current_version):
                        self.update_available = True
                        logger.info(f"New version available: {self.latest_version}")
                    else:
                        logger.info("Already on latest version")
                    
                    if callback:
                        callback(self.update_available, self.latest_version, self.download_url, self.changelog)
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to check updates: {e}")
                if callback:
                    callback(False, None, None, None)
            except Exception as e:
                logger.error(f"Update check error: {e}")
                if callback:
                    callback(False, None, None, None)
        
        # 在后台线程运行
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()
