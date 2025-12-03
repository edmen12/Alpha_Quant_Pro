"""
News Calendar Module
Fetches high-impact economic events from ForexFactory and provides trading pause logic.
"""
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pytz
import logging

logger = logging.getLogger(__name__)


class NewsCalendar:
    """
    新闻日历模块 (News Calendar)
    
    负责从 ForexFactory 抓取高影响力经济数据，并提供交易暂停逻辑。
    用于在重大新闻发布前后自动暂停交易，规避剧烈波动风险。
    """
    def __init__(self, buffer_minutes=30):
        """
        Initialize News Calendar
        
        Args:
            buffer_minutes: Minutes before/after event to pause trading (default: 30)
        """
        self.buffer_minutes = buffer_minutes
        self.events = []
        self.last_update = None
        self.enabled = False
        
    def enable(self, enabled=True):
        """Enable or disable news filter"""
        self.enabled = enabled
        logger.info(f"News Filter: {'Enabled' if enabled else 'Disabled'}")
        
    def fetch_today_events(self):
        """
        获取今日高影响力事件 (Fetch Today's Events)
        
        从 ForexFactory 爬取今日财经日历，筛选出红色（高影响力）事件。
        
        Returns:
            list: 事件字典列表 [{'name': 'CPI', 'time': datetime, 'impact': 'High'}]
        """
        try:
            url = "https://www.forexfactory.com/calendar"
            # Use cloudscraper to bypass Cloudflare
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            
            response = scraper.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse calendar table
            events = []
            rows = soup.find_all('tr', class_='calendar__row')
            
            for row in rows:
                event = self._parse_forexfactory_row(row)
                if event:
                    events.append(event)
            
            self.events = events
            self.last_update = datetime.now()
            logger.info(f"Fetched {len(events)} high-impact events for today")
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to fetch news calendar: {e}")
            # Fail-Safe: If scraping fails, we should NOT block trading indefinitely, 
            # but we also can't protect against news. 
            # Strategy: Log error, clear events (allow trading), but maybe set a flag?
            # For now, clearing events ensures we don't crash the main loop.
            self.events = []
            return []
            
    def _parse_forexfactory_row(self, row):
        """Helper to parse a single row safely"""
        try:
            # Check impact
            impact = row.find('td', class_='calendar__impact')
            if not impact or 'icon--ff-impact-red' not in str(impact):
                return None
                
            # Check time
            time_cell = row.find('td', class_='calendar__time')
            if not time_cell: return None
            time_str = time_cell.get_text(strip=True)
            if not time_str or time_str == 'All Day': return None
            
            # Check event name
            event_cell = row.find('td', class_='calendar__event')
            event_name = event_cell.get_text(strip=True) if event_cell else 'Unknown'
            
            # Parse time
            event_time = datetime.strptime(time_str, '%I:%M%p')
            today = datetime.now(pytz.UTC).date()
            event_datetime = datetime.combine(today, event_time.time())
            event_datetime = pytz.UTC.localize(event_datetime)
            
            return {
                'name': event_name,
                'time': event_datetime,
                'impact': 'High'
            }
        except Exception:
            return None
    
    def is_trading_allowed(self, current_time=None):
        """
        检查是否允许交易 (Check Trading Allowed)
        
        判断当前时间是否处于任何高影响力新闻的缓冲期内。
        
        Args:
            current_time: 当前时间 (默认: now)
            
        Returns:
            bool: True 如果允许交易 (无新闻), False 如果应暂停 (有新闻)
        """
        if not self.enabled:
            return True
        
        if current_time is None:
            current_time = datetime.now(pytz.UTC)
        
        # Ensure current_time is timezone-aware
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        
        # Update events if stale (older than 1 hour)
        if not self.last_update or (datetime.now() - self.last_update) > timedelta(hours=1):
            self.fetch_today_events()
        
        # Check if current time is within any event's buffer window
        buffer = timedelta(minutes=self.buffer_minutes)
        
        for event in self.events:
            event_start = event['time'] - buffer
            event_end = event['time'] + buffer
            
            if event_start <= current_time <= event_end:
                logger.warning(f"Trading paused: {event['name']} at {event['time'].strftime('%H:%M UTC')}")
                return False
        
        return True
    
    def get_next_event(self):
        """获取下一个即将到来的高影响力事件"""
        if not self.events:
            return None
        
        now = datetime.now(pytz.UTC)
        upcoming = [e for e in self.events if e['time'] > now]
        if upcoming:
            return min(upcoming, key=lambda x: x['time'])
        return None


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    calendar = NewsCalendar(buffer_minutes=30)
    calendar.enable(True)
    
    events = calendar.fetch_today_events()
    print(f"\\nFound {len(events)} high-impact events:")
    for e in events:
        print(f"  - {e['time'].strftime('%H:%M UTC')}: {e['name']}")
    
    print(f"\\nTrading allowed now? {calendar.is_trading_allowed()}")
    
    next_event = calendar.get_next_event()
    if next_event:
        print(f"Next event: {next_event['name']} at {next_event['time'].strftime('%H:%M UTC')}")
