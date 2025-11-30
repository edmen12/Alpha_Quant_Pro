"""
配置管理模块 (Configuration Manager)

负责终端配置的持久化存储和加载。
所有用户设置（品种、手数、风控参数等）都通过此模块保存到 JSON 文件。

主要功能：
1. 加载配置 - 从 terminal_config.json 读取设置
2. 保存配置 - 将当前设置写入文件
3. 默认值管理 - 提供安全的默认配置
"""
import json
from pathlib import Path
import logging
from path_manager import PathManager

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    配置管理器 (Configuration Manager)
    
    使用 JSON 文件存储终端配置，确保设置在重启后保持不变。
    采用静态方法设计，无需实例化即可使用。
    """
    
    # 默认配置 - 首次启动或配置文件损坏时使用
    DEFAULT_CONFIG = {
        "bundle": "Select Bundle",      # Agent Bundle 名称
        "symbol": "XAUUSD",              # 交易品种
        "mt5": "auto",                   # MT5 路径（auto = 自动检测）
        "lot_size": "0.01",              # 固定手数
        "risk": "1.0",                   # 风险百分比（动态仓位）
        "max_spread": 50,                # 最大点差限制
        "max_loss": 500.0,               # 每日最大亏损
        "min_equity": 0.0,               # 权益熔断阈值
        "news_filter": False,            # 新闻过滤开关
        "news_buffer": 30,               # 新闻缓冲时间（分钟）
        "trailing_enabled": False,       # 追踪止损开关
        "trailing_distance": 50,         # 追踪距离（点）
        "partial_close_enabled": False,  # 分批止盈开关
        "tp1_distance": 50,              # TP1 触发距离（点）
        "partial_close_percent": 50      # 分批平仓百分比
    }
    
    @staticmethod
    def get_config_file():
        return PathManager.get_config_path()
    
    @staticmethod
    def load():
        """
        加载配置 (Load Configuration)
        
        从 terminal_config.json 读取配置。如果文件不存在或损坏，
        返回默认配置。自动合并新增的配置项。
        
        Returns:
            dict: 完整的配置字典
        """
        try:
            config_file = ConfigManager.get_config_file()
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置，确保所有键都存在（向后兼容）
                    merged = ConfigManager.DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged
            return ConfigManager.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            return ConfigManager.DEFAULT_CONFIG.copy()
            
    @staticmethod
    def save(config):
        """
        保存配置 (Save Configuration)
        
        将配置写入 terminal_config.json。使用 UTF-8 编码和缩进格式化，
        便于手动编辑。
        
        Args:
            config (dict): 要保存的配置字典
            
        Returns:
            bool: 保存成功返回 True，失败返回 False
        """
        try:
            config_file = ConfigManager.get_config_file()
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info("配置已保存")
            return True
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
            return False

