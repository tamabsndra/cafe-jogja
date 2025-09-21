import json
import time
import random
import logging
import argparse
import os
import csv
import hashlib
import re
import signal
import sys
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Set, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

import socket
import urllib.parse
import requests

@dataclass
class CafeData:
    """Complete cafe data structure with precise coordinates"""
    name: str
    address: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    price_range: str = ""
    lat: float = 0.0
    lon: float = 0.0
    district: str = ""
    village: str = ""
    regency: str = ""
    type: str = ""
    phone: str = ""
    website: str = ""
    opening_hours: str = ""
    opening_hours_weekly: Dict[str, str] = field(default_factory=dict)
    maps_link: str = ""
    search_query: str = ""
    scraped_at: str = ""
    coordinate_source: str = ""
    precision_score: float = 0.0

    def get_hash(self) -> str:
        """Generate unique hash for deduplication"""
        unique_string = f"{self.name.lower().strip()}_{self.lat:.6f}_{self.lon:.6f}"
        return hashlib.md5(unique_string.encode()).hexdigest()


class AntiDetectionManager:
    """🛡️ Advanced anti-detection system for scraping"""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]

        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
            (1280, 720), (1600, 900), (2560, 1440), (1920, 1200)
        ]

        self.languages = ["en-US,en;q=0.9", "en-GB,en;q=0.9", "en-US,en;q=0.8"]

        self.current_proxy = None
        self.session_count = 0
        self.last_action_time = 0

    def get_random_user_agent(self) -> str:
        """Get random user agent"""
        return random.choice(self.user_agents)

    def get_random_resolution(self) -> Tuple[int, int]:
        """Get random screen resolution"""
        return random.choice(self.screen_resolutions)

    def get_human_delay(self, base_delay: float = 3.0) -> float:
        """Generate human-like delay with randomization"""
        # Base delay + random variation (±50%)
        variation = base_delay * 0.5
        delay = base_delay + random.uniform(-variation, variation)

        # Add occasional longer pauses (10% chance)
        if random.random() < 0.1:
            delay += random.uniform(8, 20)

        return max(1.5, delay)

    def should_take_break(self) -> bool:
        """Determine if we should take a longer break"""
        # Take break every 12-18 requests (more frequent)
        if self.session_count > 0 and self.session_count % random.randint(12, 18) == 0:
            return True
        return False

    def get_break_duration(self) -> float:
        """Get break duration in seconds"""
        # 3-8 minute breaks (longer)
        return random.uniform(90, 360)

    def simulate_human_behavior(self, driver):
        """Simulate human-like behavior"""
        try:
            # Random mouse movements
            action = ActionChains(driver)

            # Move to random positions
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                action.move_by_offset(x, y)
                time.sleep(random.uniform(0.2, 0.8))

            # Random scrolling
            if random.random() < 0.4:
                scroll_amount = random.randint(-500, 500)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1.0, 2.5))

            # Occasionally hover over elements
            if random.random() < 0.3:
                try:
                    elements = driver.find_elements(By.TAG_NAME, "div")[:8]
                    if elements:
                        element = random.choice(elements)
                        action.move_to_element(element).perform()
                        time.sleep(random.uniform(0.5, 1.5))
                except:
                    pass

        except Exception:
            # Ignore errors in behavior simulation
            pass

    def get_enhanced_chrome_options(self, headless: bool = True) -> Options:
        """Get enhanced Chrome options with anti-detection"""
        options = Options()

        if headless:
            options.add_argument("--headless=new")

        # Basic stealth options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Random user agent and window size
        user_agent = self.get_random_user_agent()
        width, height = self.get_random_resolution()

        options.add_argument(f"--user-agent={user_agent}")
        options.add_argument(f"--window-size={width},{height}")

        # Language and locale
        language = random.choice(self.languages)
        options.add_argument(f"--accept-lang={language}")

        # Additional stealth options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-dev-tools")

        # Memory and performance
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")

        # Randomize viewport
        options.add_argument(f"--window-position={random.randint(0, 100)},{random.randint(0, 100)}")

        return options

    def rate_limit(self):
        """Implement intelligent rate limiting"""
        current_time = time.time()

        # Minimum delay between actions (longer)
        min_delay = self.get_human_delay(5.0)  # 5 seconds base

        if self.last_action_time > 0:
            elapsed = current_time - self.last_action_time
            if elapsed < min_delay:
                sleep_time = min_delay - elapsed
                logging.info(f"⏳ Rate limiting: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)

        # Check if we need a break
        if self.should_take_break():
            break_time = self.get_break_duration()
            logging.info(f"🛑 Taking a break for {break_time/60:.1f} minutes...")
            time.sleep(break_time)

        self.last_action_time = time.time()
        self.session_count += 1


class BatchProcessor:
    """🔄 Batch processing with long intervals for stealth scraping"""

    def __init__(self, scraper, batch_size: int = 5, batch_interval: int = 1800):
        self.scraper = scraper
        self.batch_size = batch_size  # Number of queries per batch
        self.batch_interval = batch_interval  # Seconds between batches (30 min default)
        self.current_batch = 0

    def process_strategies_in_batches(self, strategies: List[Dict], max_cafes: int):
        """Process strategies in batches with long intervals"""
        total_batches = (len(strategies) + self.batch_size - 1) // self.batch_size

        self.scraper.logger.info(f"🔄 Processing {len(strategies)} strategies in {total_batches} batches")
        self.scraper.logger.info(f"📊 Batch size: {self.batch_size}, Interval: {self.batch_interval/60:.1f} minutes")

        for batch_num in range(total_batches):
            if len(self.scraper.all_cafes) >= max_cafes:
                self.scraper.logger.info(f"🎯 Target reached: {len(self.scraper.all_cafes)}/{max_cafes}")
                break

            # Get strategies for this batch
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(strategies))
            batch_strategies = strategies[start_idx:end_idx]

            self.scraper.logger.info(f"\n🔄 BATCH {batch_num + 1}/{total_batches}")
            self.scraper.logger.info(f"📋 Processing strategies {start_idx + 1}-{end_idx}")

            # Process current batch
            for i, strategy in enumerate(batch_strategies):
                if len(self.scraper.all_cafes) >= max_cafes:
                    break

                query = strategy['query']
                expected = strategy['expected_results']

                self.scraper.logger.info(f"📋 Strategy {start_idx + i + 1}/{len(strategies)}: {query}")

                try:
                    results = self.scraper.search_and_extract(query, expected)

                    if results:
                        self.scraper.logger.info(f"✅ Found {len(results)} cafes")
                    else:
                        self.scraper.logger.info("❌ No results found")

                except Exception as e:
                    self.scraper.logger.error(f"❌ Error processing {query}: {e}")
                    continue

                # Progress update
                self.scraper.logger.info(
                    f"📊 Progress: {len(self.scraper.all_cafes)}/{max_cafes} cafes | "
                    f"🔄 Duplicates: {self.scraper.stats['duplicates_removed']} | "
                    f"✅ Unique: {self.scraper.stats['unique_cafes']}"
                )

            # Save progress after each batch
            self.scraper.save_data(f"batch_{batch_num + 1}")

            # Long interval between batches (except for last batch)
            if batch_num < total_batches - 1 and len(self.scraper.all_cafes) < max_cafes:
                interval_minutes = self.batch_interval / 60
                self.scraper.logger.info(f"⏳ Waiting {interval_minutes:.1f} minutes before next batch...")

                # Add random variation to interval (±20%)
                variation = self.batch_interval * 0.2
                actual_interval = self.batch_interval + random.uniform(-variation, variation)
                time.sleep(actual_interval)

                # Restart driver for fresh session
                self.scraper.logger.info("🔄 Restarting driver for fresh session...")
                if self.scraper.driver:
                    self.scraper.driver.quit()
                self.scraper.setup_driver(headless=True)


class MultiSessionManager:
    """🔄 Multi-session approach with session rotation"""

    def __init__(self, scraper, session_duration: int = 3600, max_queries_per_session: int = 10):
        self.scraper = scraper
        self.session_duration = session_duration  # Max session duration in seconds (1 hour default)
        self.max_queries_per_session = max_queries_per_session
        self.current_session_start = 0
        self.queries_in_session = 0
        self.session_count = 0

    def should_rotate_session(self) -> bool:
        """Check if we should rotate to a new session"""
        current_time = time.time()
        session_elapsed = current_time - self.current_session_start

        # Rotate if session too long or too many queries
        return (session_elapsed > self.session_duration or
                self.queries_in_session >= self.max_queries_per_session)

    def rotate_session(self):
        """Rotate to a new session with fresh driver"""
        self.scraper.logger.info(f"🔄 Rotating to new session (#{self.session_count + 1})")

        # Close current session
        if self.scraper.driver:
            self.scraper.driver.quit()

        # Wait between sessions
        if self.session_count > 1 :
            rotation_delay = random.uniform(120, 420)
            self.scraper.logger.info(f"⏳ Session rotation delay: {rotation_delay/60:.1f} minutes")
            time.sleep(rotation_delay)

        # Start fresh session
        self.scraper.setup_driver(headless=True)
        self.current_session_start = time.time()
        self.queries_in_session = 0
        self.session_count += 1

        # Randomize initial behavior
        self.scraper.anti_detection.simulate_human_behavior(self.scraper.driver)

    def execute_query(self, query: str, max_results: int) -> List:
        """Execute query with session management"""
        # Check if we need to rotate session
        if self.should_rotate_session():
            self.rotate_session()

        # Execute the query
        results = self.scraper.search_and_extract(query, max_results)
        self.queries_in_session += 1

        return results

    def process_strategies_with_rotation(self, strategies: List[Dict], max_cafes: int):
        """Process strategies with automatic session rotation"""
        self.scraper.logger.info(f"🔄 Multi-session processing: max {self.max_queries_per_session} queries per session")

        # Start first session
        self.rotate_session()

        for i, strategy in enumerate(strategies):
            if len(self.scraper.all_cafes) >= max_cafes:
                self.scraper.logger.info(f"🎯 Target reached: {len(self.scraper.all_cafes)}/{max_cafes}")
                break

            query = strategy['query']
            expected = strategy['expected_results']

            self.scraper.logger.info(f"📋 Strategy {i+1}/{len(strategies)}: {query} (Session #{self.session_count})")

            try:
                results = self.execute_query(query, expected)

                if results:
                    self.scraper.logger.info(f"✅ Found {len(results)} cafes")
                else:
                    self.scraper.logger.info("❌ No results found")

            except Exception as e:
                self.scraper.logger.error(f"❌ Error processing {query}: {e}")
                continue

            # Progress update
            self.scraper.logger.info(
                f"📊 Progress: {len(self.scraper.all_cafes)}/{max_cafes} cafes | "
                f"🔄 Duplicates: {self.scraper.stats['duplicates_removed']} | "
                f"✅ Unique: {self.scraper.stats['unique_cafes']} | "
                f"Session: {self.queries_in_session}/{self.max_queries_per_session}"
            )

            # Save progress periodically
            if (i + 1) % 10 == 0:
                self.scraper.save_data("progress")


class UltimateCafeScraper:
    """Ultimate cafe scraper with all features combined"""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        self.setup_logging()
        self.setup_directories()

        # Initialize anti-detection manager
        self.anti_detection = AntiDetectionManager()

        # Data storage with thread safety
        self.all_cafes: List[CafeData] = []
        self.seen_hashes: Set[str] = set()
        self.seen_names: Set[str] = set()  # Additional dedup by name
        self.seen_coordinates: Set[Tuple[float, float]] = set()  # Dedup by coords
        self.data_lock = threading.Lock()  # Thread safety for data operations

        # Selenium components
        self.driver = None
        self.wait = None

        # Parallel processing settings
        self.max_workers = 3  # Number of parallel threads
        self.batch_size = 10  # Elements per batch

        # Productivity tracking with comprehensive settings
        self.consecutive_empty_queries = 0
        self.max_consecutive_empty = 500  # Increase for comprehensive coverage
        self.query_performance = {}  # Track query effectiveness
        self.high_yield_mode = False  # Keep comprehensive mode

        # Statistics with deduplication tracking
        self.stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'high_precision_count': 0,
            'duplicates_removed': 0,
            'unique_cafes': 0,
            'start_time': time.time()
        }

        # Pause/Resume functionality
        self.is_paused = False
        self.should_stop = False
        self.current_strategy_index = 0
        self.state_file = os.path.join(self.output_dir, "scraper_state.json")
        self.resume_data_file = os.path.join(self.output_dir, "resume_data.json")

        # Setup signal handlers for pause/resume
        self.setup_signal_handlers()

        # Search strategies with comprehensive mode (user preference for complete coverage)
        self.search_strategies = self._generate_search_strategies()

    def setup_logging(self):
        """Setup comprehensive logging"""
        os.makedirs('logs', exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/cafe_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Setup output directories"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)

    def setup_signal_handlers(self):
        """Setup signal handlers for pause/resume functionality"""
        def signal_handler(signum, frame):
            if signum == signal.SIGINT:  # Ctrl+C
                print("\n⏸️  Pausing scraper... Press 'r' + Enter to resume, 'q' + Enter to quit")
                self.is_paused = True
                self.save_state()
            elif signum == signal.SIGTERM:  # Termination signal
                print("\n🛑 Stopping scraper...")
                self.should_stop = True
                self.save_state()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def save_state(self):
        """Save current scraping state for resume functionality"""
        try:
            state_data = {
                'current_strategy_index': self.current_strategy_index,
                'consecutive_empty_queries': self.consecutive_empty_queries,
                'high_yield_mode': self.high_yield_mode,
                'query_performance': self.query_performance,
                'stats': self.stats,
                'seen_hashes': list(self.seen_hashes),
                'seen_names': list(self.seen_names),
                'seen_coordinates': list(self.seen_coordinates),
                'timestamp': datetime.now().isoformat()
            }

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            # Save current cafe data
            resume_data = {
                'cafes': [asdict(cafe) for cafe in self.all_cafes],
                'metadata': {
                    'total_cafes': len(self.all_cafes),
                    'saved_at': datetime.now().isoformat(),
                    'scraper_version': 'ultimate_v2.0_pause_resume'
                }
            }

            with open(self.resume_data_file, 'w', encoding='utf-8') as f:
                json.dump(resume_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"💾 State saved to {self.state_file}")
            self.logger.info(f"💾 Resume data saved to {self.resume_data_file}")

        except Exception as e:
            self.logger.error(f"❌ Failed to save state: {e}")

    def load_state(self) -> bool:
        """Load previous scraping state for resume functionality"""
        try:
            if not os.path.exists(self.state_file) or not os.path.exists(self.resume_data_file):
                return False

            # Load state
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            self.current_strategy_index = state_data.get('current_strategy_index', 0)
            self.consecutive_empty_queries = state_data.get('consecutive_empty_queries', 0)
            self.high_yield_mode = state_data.get('high_yield_mode', False)
            self.query_performance = state_data.get('query_performance', {})
            self.stats = state_data.get('stats', self.stats)

            # Restore deduplication sets
            self.seen_hashes = set(state_data.get('seen_hashes', []))
            self.seen_names = set(state_data.get('seen_names', []))
            self.seen_coordinates = set(tuple(coord) if isinstance(coord, list) else coord
                                     for coord in state_data.get('seen_coordinates', []))

            # Load cafe data
            with open(self.resume_data_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)

            # Restore cafes
            self.all_cafes = []
            for cafe_dict in resume_data.get('cafes', []):
                # Convert dict back to CafeData object
                cafe = CafeData(**cafe_dict)
                self.all_cafes.append(cafe)

            saved_time = state_data.get('timestamp', 'unknown')
            self.logger.info(f"✅ State loaded from {saved_time}")
            self.logger.info(f"📊 Resuming from strategy {self.current_strategy_index + 1}")
            self.logger.info(f"📋 {len(self.all_cafes)} cafes already scraped")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to load state: {e}")
            return False

    def clear_state(self):
        """Clear saved state files"""
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            if os.path.exists(self.resume_data_file):
                os.remove(self.resume_data_file)
            self.logger.info("🗑️  Previous state cleared")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to clear state: {e}")

    def handle_pause(self):
        """Handle pause state with user input"""
        while self.is_paused and not self.should_stop:
            try:
                user_input = input("⏸️  Scraper is paused. Enter 'r' to resume, 'q' to quit, 's' to save and quit: ").strip().lower()

                if user_input == 'r':
                    print("▶️  Resuming scraper...")
                    self.is_paused = False
                    break
                elif user_input == 'q':
                    print("🛑 Quitting without saving...")
                    self.should_stop = True
                    break
                elif user_input == 's':
                    print("💾 Saving and quitting...")
                    self.save_state()
                    self.save_data("paused")
                    self.should_stop = True
                    break
                else:
                    print("Invalid input. Use 'r' to resume, 'q' to quit, 's' to save and quit")

            except (EOFError, KeyboardInterrupt):
                print("\n🛑 Force quit detected")
                self.should_stop = True
                break

    def is_duplicate(self, cafe: CafeData) -> bool:
        """Enhanced duplicate detection with multiple criteria"""
        # Check hash (primary method)
        cafe_hash = cafe.get_hash()
        if cafe_hash in self.seen_hashes:
            return True

        # Check name similarity (normalize and compare)
        normalized_name = self._normalize_name(cafe.name)
        if normalized_name in self.seen_names:
            return True

        # Check coordinate proximity (within ~10 meters)
        if cafe.lat and cafe.lon:
            coord_tuple = (round(cafe.lat, 4), round(cafe.lon, 4))  # ~11m precision
            if coord_tuple in self.seen_coordinates:
                return True

        return False

    def _normalize_name(self, name: str) -> str:
        """Normalize cafe name for better duplicate detection"""
        if not name:
            return ""

        # Convert to lowercase and remove common variations
        normalized = name.lower().strip()

        # Remove common prefixes/suffixes
        prefixes = ['kafe', 'cafe', 'kedai', 'warung', 'toko', 'rumah']
        suffixes = ['coffee', 'kopi', 'shop', 'store', 'house', 'jogja', 'yogya']

        for prefix in prefixes:
            if normalized.startswith(prefix + ' '):
                normalized = normalized[len(prefix):].strip()

        for suffix in suffixes:
            if normalized.endswith(' ' + suffix):
                normalized = normalized[:-len(suffix)].strip()

        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def add_cafe_if_unique(self, cafe: CafeData) -> bool:
        """Thread-safe method to add cafe if it's unique"""
        with self.data_lock:
            if self.is_duplicate(cafe):
                self.stats['duplicates_removed'] += 1
                self.logger.debug(f"🔄 Duplicate detected: {cafe.name}")
                return False

            # Add to tracking sets
            self.seen_hashes.add(cafe.get_hash())
            self.seen_names.add(self._normalize_name(cafe.name))
            if cafe.lat and cafe.lon:
                coord_tuple = (round(cafe.lat, 4), round(cafe.lon, 4))
                self.seen_coordinates.add(coord_tuple)

            # Add to results
            self.all_cafes.append(cafe)
            self.stats['unique_cafes'] += 1
            self.logger.debug(f"✅ Added unique cafe: {cafe.name}")
            return True

    def _generate_search_strategies(self) -> List[Dict]:
        """Generate search strategies with optional high-yield filtering and specialty coverage"""

        # Full keyword set for comprehensive scraping
        base_keywords = [
            "cafe", "coffee shop", "kedai kopi", "kopi", "coffee",
            "roastery", "specialty coffee", "espresso bar", "coffee house",
            "warung kopi", "tempat ngopi", "kopi tradisional", "kopi kekinian",
        ]

        contexts = [
            "terbaik", "buat nugas", "buka 24 jam", "cozy", "di", "hits", "instagrammable", "kalcer", "late night",
            "live music", "murah", "paling rame", "populer", "recommended", "skena", "sunset spot",
            "terdekat", "view bagus", "viral"
        ]

        # Kabupaten/Kota-level (DIY regions)
        regions = [
            "yogyakarta", "sleman", "bantul", "kulon progo", "gunungkidul", "kota jogja", "DIY"
        ]

        # Kecamatan/sub-area populer
        sub_areas = [
            # Sleman & sekitar UGM
            "malioboro", "condongcatur", "depok", "caturtunggal", "seturan",
            "gejayan", "pogung", "kentungan", "babarsari", "kalasan", "ngaglik",
            "mlati", "gamping", "godean", "berbah", "prambanan", "cangkringan",
            "pakem", "turi", "tempel", "seyegan", "minggir", "moyudan", "jakal",
            "demangan", "klebengan",

            # Bantul
            "sewon", "kasihan", "banguntapan", "pleret", "pajangan", "imogiri",
            "pundong", "kretek", "sanden", "bambanglipuro", "srandakan", "dlingo",
            # Kulon Progo
            "wates", "panjatan", "galur", "lendah", "sentolo", "pengasih",
            "kokap", "nanggulan", "girimulyo", "kalibawang", "temon",
            # Gunungkidul
            "wonosari", "playen", "paliyan", "panggang", "purwosari", "tepus",
            "rongkop", "girisubo", "semanu", "tanjungsari", "ponjong", "patuk",
            "karangmojo", "gedangsari", "ngawen"
        ]

        # Landmark/places of interest
        landmarks = [
            "alun alun kidul", "alun alun utara", "ambarukmo plaza", "bukit bintang",
            "gembira loka zoo", "goa pindul", "hartono mall", "heha sky view",
            "jogja city mall", "kaliurang", "keraton yogyakarta", "mangunan",
            "merapi museum", "monjali", "parangtritis beach", "pinus pengger",
            "prambanan temple", "ratu boko", "sindu kusuma edupark", "taman sari",
            "tebing breksi", "tugu jogja", "waduk sermo", "xt square",
            "yogyakarta international airport",
        ]

        # University in Yogyakarta
        universities_jogja = [
            "ugm", "uii", "upn", "uin", "uny", "usd", "amikom", "udb", "stikes", "instiper", "akprind", "isi", "ukdw", "uty", "umy", "uad"
        ]

        essential_menu = ["magic","latte","dirty latte","matcha","butterscotch","americano","cappuccino","flat white","mocha","caramel macchiato"]

        kata_tempat = ["dekat", "di", "sekitar", "area"]

        all_queries = set()

        # Kombinasi base keywords dengan konteks & wilayah besar
        for kw in base_keywords:
            for ctx in contexts:
                for reg in regions:
                    query = f"{kw} {ctx} {reg}".strip()
                    all_queries.add(query)

        # Tambahin kombinasi dengan sub-area
        for area in sub_areas:
            query = f"{base_keywords[random.randint(0, len(base_keywords) - 1)]} {kata_tempat[random.randint(0, len(kata_tempat) - 1)]} {area}".strip()
            all_queries.add(query)

        # Tambahin kombinasi dengan landmark
        for kw in base_keywords:
            for lm in landmarks:
                query = f"{kw} {kata_tempat[random.randint(0, len(kata_tempat) - 1)]} {lm}".strip()
                all_queries.add(query)

        # Tambahin kombinasi dengan university
        for kw in base_keywords:
            for ctx in contexts:
                for uni in universities_jogja:
                    query = f"{kw} {ctx} {kata_tempat[random.randint(0, len(kata_tempat) - 1)]} {uni} jogja".strip()
                    all_queries.add(query)

        awalan = ["jual", "rekomendasi", "beli", "cafe"]

        # Tambahin kombinasi dengan menu
        for menu in essential_menu:
            for reg in regions:
                query = f"{awalan[random.randint(0, len(awalan) - 1)]} {menu} {kata_tempat[random.randint(0, len(kata_tempat) - 1)]} {reg}".strip()
                all_queries.add(query)

        strategies = []

        for q in sorted(all_queries):
            words = q.split()

            if any (sub_area in q.lower() for sub_area in sub_areas):
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 0
                })

            if any(region in q.lower() for region in regions):
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 0
                })
            elif any(uni in q.lower() for uni in universities_jogja):
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 1
                })
            elif any(menu in q.lower() for menu in essential_menu):
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 2
                })
            elif 'dekat' not in q.lower() and len(words) <= 10:  # Simple, general queries
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 3
                })
            elif 'dekat' in q.lower() and len(words) <= 10:  # Simple "near" queries
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 4
                })
            else:
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 5
                })

        strategies.sort(key=lambda x: (x['priority'], -x['expected_results']))

        return strategies

    def setup_driver(self, headless: bool = True):
        """Setup Chrome driver with advanced anti-detection"""
        # Use enhanced options from anti-detection manager
        options = self.anti_detection.get_enhanced_chrome_options(headless)

        try:
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=options
            )

            # Set random wait timeout
            wait_timeout = random.randint(5, 18)
            self.wait = WebDriverWait(self.driver, wait_timeout)

            # Execute stealth scripts to hide automation
            stealth_script = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                window.chrome = {
                    runtime: {},
                };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' }),
                    }),
                });
            """
            self.driver.execute_script(stealth_script)

            self.logger.info(f"✅ Chrome driver initialized with anti-detection (UA: {self.anti_detection.get_random_user_agent()[:50]}...)")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize driver: {e}")
            raise

    def extract_precise_coordinates(self, element) -> Tuple[float, float, str, float]:
        """Extract precise coordinates using multiple methods"""
        # Method 1: Extract from URL (HIGHEST PRECISION)
        lat, lon, precision = self.extract_from_url(element)
        if lat and lon and precision >= 0.85:
            return lat, lon, "extract_from_url", precision

        # Method 2: Extract from data attributes
        lat, lon, precision = self.extract_from_data_attributes(element)
        if lat and lon and precision >= 0.80:
            return lat, lon, "extract_from_data_attributes", precision

        # Method 3: Extract from onclick events
        lat, lon, precision = self.extract_from_onclick(element)
        if lat and lon and precision >= 0.70:
            return lat, lon, "extract_from_onclick", precision

        # Method 4: Extract from aria-label
        lat, lon, precision = self.extract_from_aria_label(element)
        if lat and lon and precision >= 0.65:
            return lat, lon, "extract_from_aria_label", precision

        # Fallback: Improved estimation
        lat, lon = self.estimate_coordinates_smart()
        return lat, lon, "smart_estimation", 0.3

    def extract_from_url(self, element) -> Tuple[Optional[float], Optional[float], float]:
        """Extract coordinates from Google Maps URL - HIGHEST PRECISION"""
        try:
            links = element.find_elements(By.TAG_NAME, 'a')

            for link in links:
                href = link.get_attribute('href')
                if not href:
                    continue

                # Pattern 1: @lat,lon,zoom format
                pattern1 = r'@(-?\d+\.?\d*),(-?\d+\.?\d*),\d+z'
                match = re.search(pattern1, href)
                if match:
                    lat, lon = float(match.group(1)), float(match.group(2))
                    self.logger.debug(f"🎯 URL coordinates: {lat:.6f}, {lon:.6f}")
                    return lat, lon, 0.95

                # Pattern 2: !3d and !4d format
                pattern2 = r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)'
                match = re.search(pattern2, href)
                if match:
                    lat, lon = float(match.group(1)), float(match.group(2))
                    self.logger.debug(f"🎯 URL coordinates (3d/4d): {lat:.6f}, {lon:.6f}")
                    return lat, lon, 0.90

        except Exception as e:
            self.logger.debug(f"URL extraction failed: {e}")

        return None, None, 0.0

    def extract_from_data_attributes(self, element) -> Tuple[Optional[float], Optional[float], float]:
        """Extract from data attributes - HIGH PRECISION"""
        try:
            data_attrs = ['data-lat', 'data-lng', 'data-latitude', 'data-longitude']
            lat = lon = None

            for attr in data_attrs:
                if 'lat' in attr:
                    lat_val = element.get_attribute(attr)
                    if lat_val:
                        lat = float(lat_val)
                else:
                    lon_val = element.get_attribute(attr)
                    if lon_val:
                        lon = float(lon_val)

            if lat and lon:
                self.logger.debug(f"🎯 Data attributes: {lat:.6f}, {lon:.6f}")
                return lat, lon, 0.85

        except Exception as e:
            self.logger.debug(f"Data attributes extraction failed: {e}")

        return None, None, 0.0

    def extract_from_onclick(self, element) -> Tuple[Optional[float], Optional[float], float]:
        """Extract from onclick events - MEDIUM PRECISION"""
        try:
            onclick = element.get_attribute('onclick')
            if onclick:
                pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
                matches = re.findall(pattern, onclick)

                for match in matches:
                    lat, lon = float(match[0]), float(match[1])
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        self.logger.debug(f"🎯 Onclick coordinates: {lat:.6f}, {lon:.6f}")
                        return lat, lon, 0.75

        except Exception as e:
            self.logger.debug(f"Onclick extraction failed: {e}")

        return None, None, 0.0

    def extract_from_aria_label(self, element) -> Tuple[Optional[float], Optional[float], float]:
        """Extract from aria-label - MEDIUM PRECISION"""
        try:
            aria_label = element.get_attribute('aria-label')
            if aria_label:
                pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
                matches = re.findall(pattern, aria_label)

                for match in matches:
                    lat, lon = float(match[0]), float(match[1])
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        self.logger.debug(f"🎯 Aria-label coordinates: {lat:.6f}, {lon:.6f}")
                        return lat, lon, 0.70

        except Exception as e:
            self.logger.debug(f"Aria-label extraction failed: {e}")

        return None, None, 0.0

    def estimate_coordinates_smart(self) -> Tuple[float, float]:
        """Smart coordinate estimation as fallback"""
        # Precise area definitions for Yogyakarta
        precise_areas = {
            'malioboro': (-7.7956, 110.3695, -7.7926, 110.3725),
            'tugu': (-7.7890, 110.3640, -7.7860, 110.3670),
            'ugm': (-7.7720, 110.3740, -7.7690, 110.3770),
            'condongcatur': (-7.7540, 110.4080, -7.7510, 110.4110),
            'sleman_center': (-7.7450, 110.3510, -7.7420, 110.3540),
            'bantul_center': (-7.8880, 110.3290, -7.8850, 110.3320),
            'yogya_center': (-7.8020, 110.3650, -7.7990, 110.3680)
        }

        # Default to central Yogyakarta with accurate range
        return random.uniform(-7.82, -7.76), random.uniform(110.35, 110.40)

    def precise_geocode(self, lat: float, lon: float) -> Dict:
        """Enhanced precise geocoding with village-level accuracy"""
        try:
            # More detailed mapping for Yogyakarta area
            if -7.78 <= lat <= -7.72 and 110.35 <= lon <= 110.42:
                # Sleman area - more specific districts
                if -7.75 <= lat <= -7.72 and 110.37 <= lon <= 110.40:
                    return {'regency': 'Sleman', 'district': 'Depok', 'village': 'Condongcatur'}
                elif -7.76 <= lat <= -7.74 and 110.36 <= lon <= 110.38:
                    return {'regency': 'Sleman', 'district': 'Depok', 'village': 'Caturtunggal'}
                elif -7.77 <= lat <= -7.75 and 110.38 <= lon <= 110.41:
                    return {'regency': 'Sleman', 'district': 'Mlati', 'village': 'Sinduadi'}
                else:
                    return {'regency': 'Sleman', 'district': 'Sleman', 'village': 'Sleman'}

            elif -7.82 <= lat <= -7.78 and 110.36 <= lon <= 110.39:
                # Yogyakarta City - specific areas
                if -7.80 <= lat <= -7.78 and 110.36 <= lon <= 110.37:
                    return {'regency': 'Yogyakarta', 'district': 'Jetis', 'village': 'Bumijo'}
                elif -7.80 <= lat <= -7.79 and 110.37 <= lon <= 110.38:
                    return {'regency': 'Yogyakarta', 'district': 'Gondokusuman', 'village': 'Terban'}
                elif -7.79 <= lat <= -7.78 and 110.36 <= lon <= 110.37:
                    return {'regency': 'Yogyakarta', 'district': 'Kraton', 'village': 'Panembahan'}
                else:
                    return {'regency': 'Yogyakarta', 'district': 'Yogyakarta', 'village': 'Malioboro'}

            elif -7.95 <= lat <= -7.82 and 110.32 <= lon <= 110.42:
                # Bantul area
                if -7.85 <= lat <= -7.82 and 110.35 <= lon <= 110.38:
                    return {'regency': 'Bantul', 'district': 'Sewon', 'village': 'Panggungharjo'}
                elif -7.88 <= lat <= -7.85 and 110.33 <= lon <= 110.36:
                    return {'regency': 'Bantul', 'district': 'Kasihan', 'village': 'Tamantirto'}
                else:
                    return {'regency': 'Bantul', 'district': 'Bantul', 'village': 'Bantul'}

            elif -7.85 <= lat <= -7.75 and 110.15 <= lon <= 110.25:
                return {'regency': 'Kulon Progo', 'district': 'Wates', 'village': 'Wates'}

            elif -7.95 <= lat <= -7.85 and 110.45 <= lon <= 110.70:
                return {'regency': 'Gunung Kidul', 'district': 'Wonosari', 'village': 'Wonosari'}

            else:
                # Try reverse geocoding with Nominatim as fallback
                return self.fallback_geocode(lat, lon)

        except Exception as e:
            self.logger.debug(f"Geocoding failed: {e}")
            return {'regency': '', 'district': '', 'village': ''}

    def fallback_geocode(self, lat: float, lon: float) -> Dict:
        """Fallback geocoding using Nominatim"""
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="cafe_scraper")
            location = geolocator.reverse(f"{lat}, {lon}", timeout=5)

            if location and location.raw.get('address'):
                addr = location.raw['address']
                return {
                    'regency': addr.get('city', '') or addr.get('county', '') or addr.get('state_district', ''),
                    'district': addr.get('suburb', '') or addr.get('neighbourhood', '') or addr.get('village', ''),
                    'village': addr.get('hamlet', '') or addr.get('residential', '') or addr.get('road', '')
                }
            else:
                return {'regency': 'Yogyakarta', 'district': '', 'village': ''}

        except Exception as e:
            self.logger.debug(f"Fallback geocoding failed: {e}")
            return {'regency': 'Yogyakarta', 'district': '', 'village': ''}

    def classify_cafe_type(self, name: str, address: str) -> str:
        """Classify cafe type"""
        text = f"{name} {address}".lower()

        if any(word in text for word in ['traditional', 'warung', 'angkringan', 'lesehan']):
            return 'Traditional'
        elif any(word in text for word in ['roastery', 'roaster', 'specialty']):
            return 'Roastery'
        elif any(word in text for word in ['coffee', 'espresso', 'latte', 'cappuccino']):
            return 'Coffee Shop'
        elif any(word in text for word in ['resto', 'restaurant', 'dining']):
            return 'Cafe & Restaurant'
        else:
            return 'Modern'

    def extract_cafe_data(self, element, query: str, extract_details: bool = True) -> Optional[CafeData]:
        """Extract complete cafe data with precise coordinates"""
        try:
            full_text = element.text.strip()
            if not full_text:
                return None

            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            if not lines:
                return None

            # Extract precise coordinates
            lat, lon, coord_source, precision_score = self.extract_precise_coordinates(element)

            # Initialize cafe
            cafe = CafeData(
                name=lines[0],
                lat=lat,
                lon=lon,
                coordinate_source=coord_source,
                precision_score=precision_score,
                search_query=query,
                scraped_at=datetime.now().isoformat()
            )

            # Extract Google Maps place link (for clean reference)
            try:
                links = element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href') or ''
                    if '/maps/place/' in href:
                        cafe.maps_link = href
                        break
            except Exception:
                pass

            # Parse additional info
            for line in lines[1:]:
                # Combined rating, reviews, and price extraction from lines like "4,5(7.602) · Rp 25-50 rb"
                rating_reviews_price_match = re.search(r'(\d+[.,]\d+)\s*\(([0-9,.k]+)\)\s*·\s*(.*)', line)
                if rating_reviews_price_match:
                    # Extract rating
                    cafe.rating = float(rating_reviews_price_match.group(1).replace(',', '.'))

                    # Extract reviews count
                    reviews_str = rating_reviews_price_match.group(2)
                    if 'k' in reviews_str.lower():
                        # Handle "7.6k" format
                        cafe.reviews_count = int(float(reviews_str.replace('k', '').replace('.', '').replace(',', '')) * 100)
                    else:
                        # Handle "7.602" format (thousands separator)
                        reviews_clean = reviews_str.replace('.', '').replace(',', '')
                        cafe.reviews_count = int(reviews_clean)

                    # Extract price range
                    price_text = rating_reviews_price_match.group(3).strip()
                    if 'Rp' in price_text or '$' in price_text or '€' in price_text:
                        cafe.price_range = price_text

                # Fallback: Rating and reviews only - look for pattern like "4,5(7.602)"
                elif not cafe.rating:
                    rating_reviews_match = re.search(r'(\d+[.,]\d+)\s*\(([0-9,.k]+)\)', line)
                    if rating_reviews_match:
                        # Extract rating
                        cafe.rating = float(rating_reviews_match.group(1).replace(',', '.'))

                        # Extract reviews count
                        reviews_str = rating_reviews_match.group(2)
                        if 'k' in reviews_str.lower():
                            cafe.reviews_count = int(float(reviews_str.replace('k', '').replace('.', '').replace(',', '')) * 100)
                        else:
                            reviews_clean = reviews_str.replace('.', '').replace(',', '')
                            cafe.reviews_count = int(reviews_clean)

                # Fallback: Price range only
                elif '·' in line and ('Rp' in line or '$' in line or '€' in line) and not cafe.price_range:
                    # Extract price from lines with separator
                    parts = line.split('·')
                    for part in parts:
                        if 'Rp' in part or '$' in part or '€' in part:
                            cafe.price_range = part.strip()
                            break

                # Standalone price patterns (without separator)
                elif not cafe.price_range and any(currency in line for currency in ['Rp', '$', '€', 'USD', 'IDR']):
                    # Look for price patterns like "Rp 25-50 rb", "$10-20", etc.
                    price_patterns = [
                        r'Rp\s*[\d.,]+\s*[--]\s*[\d.,]+\s*(?:rb|ribu|k)?',
                        r'\$\s*[\d.,]+\s*[--]\s*[\d.,]+',
                        r'€\s*[\d.,]+\s*[--]\s*[\d.,]+',
                        r'[\d.,]+\s*[--]\s*[\d.,]+\s*(?:USD|IDR|rb|ribu)',
                    ]

                    for pattern in price_patterns:
                        price_match = re.search(pattern, line, re.IGNORECASE)
                        if price_match:
                            cafe.price_range = price_match.group(0).strip()
                            break

                # Also try standalone rating pattern
                elif '⭐' in line or '★' in line:
                    rating_match = re.search(r'(\d+[.,]\d*)', line)
                    if rating_match and not cafe.rating:  # Only if not already found
                        cafe.rating = float(rating_match.group(1).replace(',', '.'))

                elif any(word in line.lower() for word in ['jl.', 'jalan', 'street', 'km', 'no.']):
                    if not cafe.address:
                        cafe.address = line

                elif 'buka' in line.lower() or 'tutup' in line.lower():
                    if not cafe.opening_hours:
                        cafe.opening_hours = line

            # Geocode and classify
            if cafe.lat and cafe.lon:
                geo_info = self.precise_geocode(cafe.lat, cafe.lon)
                cafe.regency = geo_info.get('regency', '')
                cafe.district = geo_info.get('district', '')
                cafe.village = geo_info.get('village', '')

            cafe.type = self.classify_cafe_type(cafe.name, cafe.address)

            # Track precision
            if precision_score >= 0.8:
                self.stats['high_precision_count'] += 1

            # Try to get additional details by clicking (if enabled)
            if extract_details:
                try:
                    self.extract_detailed_info(element, cafe)
                except Exception as e:
                    self.logger.debug(f"Detailed extraction failed: {e}")

            return cafe

        except Exception as e:
            self.logger.debug(f"Cafe extraction failed: {e}")
            return None

    def extract_detailed_info(self, element, cafe: CafeData):
        """Extract additional details by clicking on the element"""
        try:
            # Save current window handle
            original_window = self.driver.current_window_handle

            # Click on the element to get more details
            self.driver.execute_script("arguments[0].click();", element)
            time.sleep(2)

            # Address (detail pane provides full address reliably)
            if not cafe.address:
                try:
                    addr_el = self.driver.find_element(By.CSS_SELECTOR, 'button.CsEnBe[data-item-id="address"] .Io6YTe')
                    txt = addr_el.text.strip()
                    if txt:
                        cafe.address = txt
                except Exception:
                    pass

            # Try to extract phone number
            if not cafe.phone:
                try:
                    # New selector pattern: button with data-item-id starting with phone:tel:
                    phone_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.CsEnBe[data-item-id^="phone:tel:"]')
                    # Prefer aria-label (contains "Telepon: <number>")
                    aria = (phone_btn.get_attribute('aria-label') or '').strip()
                    if 'Telepon:' in aria:
                        cafe.phone = aria.split('Telepon:')[-1].strip()
                    if not cafe.phone:
                        # Try visible text inside button
                        txt = phone_btn.text.strip()
                        if txt:
                            cafe.phone = txt
                except:
                    # Try alternative phone selectors
                    phone_selectors = ['a[href^="tel:"]', '.rogA2c']
                    for selector in phone_selectors:
                        try:
                            phone_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            phone_text = phone_elem.get_attribute('href') or phone_elem.text
                            if phone_text:
                                if phone_text.startswith('tel:'):
                                    cafe.phone = phone_text.replace('tel:', '').strip()
                                elif re.search(r'[\d\+\-\s\(\)]{8,}', phone_text):
                                    cafe.phone = phone_text.strip()
                                break
                        except:
                            continue

            # Try to extract website
            if not cafe.website:
                try:
                    # Primary: authority link in detail pane
                    website_link = self.driver.find_element(By.CSS_SELECTOR, 'a.CsEnBe[data-item-id*="authority"]')
                    website_url = website_link.get_attribute('href')
                    if website_url and ('http' in website_url):
                        # Clean up the URL
                        if 'instagram.com' in website_url:
                            cafe.website = website_url
                        elif 'facebook.com' in website_url:
                            cafe.website = website_url
                        elif website_url.startswith('http'):
                            cafe.website = website_url
                except:
                    # Try alternative website selectors
                    website_selectors = ['a[href^="http"]']
                    for selector in website_selectors:
                        try:
                            web_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            web_url = web_elem.get_attribute('href')
                            if web_url and web_url.startswith('http') and 'google.com/maps' not in web_url:
                                cafe.website = web_url
                                break
                        except:
                            continue

            # Try to get more detailed opening hours (weekly table)
            try:
                # Open dropdown if collapsed
                try:
                    toggle = self.driver.find_element(By.CSS_SELECTOR, 'div.OMl5r[role="button"]')
                    if toggle.get_attribute('aria-expanded') == 'false':
                        toggle.click()
                        time.sleep(1)
                except Exception:
                    pass

                rows = self.driver.find_elements(By.CSS_SELECTOR, 'table.eK4R0e tr.y0skZc')
                if rows:
                    weekly = {}
                    for row in rows:
                        try:
                            day = row.find_element(By.CSS_SELECTOR, 'td.ylH6lf').text.strip()
                            hours = row.find_element(By.CSS_SELECTOR, 'td.mxowUb').text.strip()
                            if day and hours:
                                weekly[day] = hours
                        except Exception:
                            continue
                    if weekly:
                        cafe.opening_hours_weekly = weekly
                        # Also set a concise opening_hours if empty
                        if not cafe.opening_hours:
                            # Pick a representative day (e.g., Senin)
                            rep = weekly.get('Senin') or next(iter(weekly.values()), '')
                            cafe.opening_hours = rep
            except Exception:
                pass

            # Price summary in detail (per person). Prefer summary text.
            try:
                price_btn = self.driver.find_element(By.CSS_SELECTOR, 'div.MNVeJb[role="button"]')
                summary = price_btn.text.strip()
                if summary:
                    # Normalize to a concise form before the newline, if any
                    summary_line = summary.split('\n')[0].strip()
                    cafe.price_range = summary_line
            except Exception:
                # If histogram present, optionally choose dominant bucket (skipped to reduce page time)
                pass

            # Go back to list view
            try:
                back_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-value="Back"]')
                back_button.click()
                time.sleep(1)
            except:
                # Alternative: press escape or click outside
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(1)
                except:
                    pass

        except Exception as e:
            self.logger.debug(f"Detailed info extraction failed: {e}")
            # Ensure we're back to list view
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except:
                pass

    def search_and_extract(self, query: str, max_results: int = 50, extract_details: bool = True) -> List[CafeData]:
        """Search Google Maps and extract cafe data with anti-detection"""
        self.logger.info(f"🔍 Searching: {query} (max {max_results} results)")

        # Apply rate limiting before each search
        self.anti_detection.rate_limit()

        results = []

        try:
            # Ensure driver is set up
            if not self.driver:
                self.setup_driver(headless=True)

            # Go to Google Maps with human-like delay
            self.driver.get('https://maps.google.com')
            human_delay = self.anti_detection.get_human_delay(2.5)
            time.sleep(human_delay)

            # Simulate human behavior before searching
            self.anti_detection.simulate_human_behavior(self.driver)

            # Search with human-like typing
            search_box = self.wait.until(EC.presence_of_element_located((By.ID, 'searchboxinput')))
            search_box.clear()

            # Type with human-like delays
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            time.sleep(random.uniform(0.5, 1.2))
            search_box.send_keys(Keys.RETURN)

            # Wait with human-like delay
            wait_time = self.anti_detection.get_human_delay(4.0)
            time.sleep(wait_time)

            # Auto-scroll to load more results
            self.auto_scroll_results(max_results)

            # Extract results
            elements = self.driver.find_elements(By.CSS_SELECTOR, '.Nv2PK')

            self.logger.info(f"📋 Processing {len(elements)} elements...")

            # Process elements in parallel batches
            results = self.process_elements_parallel(elements[:max_results], query, extract_details)

        except Exception as e:
            self.logger.error(f"❌ Search failed for '{query}': {e}")

        return results

    def process_elements_parallel(self, elements, query: str, extract_details: bool = True) -> List[CafeData]:
        """Process elements in parallel batches for better performance"""
        results = []

        # Split elements into batches
        batches = [elements[i:i + self.batch_size] for i in range(0, len(elements), self.batch_size)]

        self.logger.info(f"🚀 Processing {len(elements)} elements in {len(batches)} parallel batches")

        for batch_idx, batch in enumerate(batches):
            batch_results = []

            # Process batch with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks
                future_to_element = {
                    # Always extract base info in parallel for stability; detail enrichment is sequential
                    executor.submit(self.process_single_element, element, query, idx, False): (element, idx)
                    for idx, element in enumerate(batch)
                }

                # Collect results
                for future in as_completed(future_to_element):
                    element, idx = future_to_element[future]
                    try:
                        cafe = future.result()
                        if cafe:
                            # Use thread-safe deduplication
                            if self.add_cafe_if_unique(cafe):
                                batch_results.append(cafe)
                                self.stats['successful_extractions'] += 1
                                self.logger.info(f"✅ {cafe.name} - {cafe.coordinate_source} ({cafe.precision_score:.2f})")
                            # Duplicate message already logged in add_cafe_if_unique
                        else:
                            self.stats['failed_extractions'] += 1
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to process element in batch {batch_idx}: {e}")
                        self.stats['failed_extractions'] += 1

            results.extend(batch_results)

            # Sequentially enrich details by opening place links in a new tab
            if extract_details and batch_results:
                for cafe in batch_results:
                    try:
                        self.enrich_cafe_details_from_link(cafe)
                        # Be polite
                        time.sleep(random.uniform(0.5, 1.2))
                    except Exception as e:
                        self.logger.debug(f"Detail enrichment failed for {cafe.name}: {e}")

            # Rate limiting between batches
            if batch_idx < len(batches) - 1:  # Don't sleep after last batch
                time.sleep(random.uniform(2, 4))
                self.logger.debug(f"📊 Batch {batch_idx + 1}/{len(batches)} completed, {len(batch_results)} new cafes")

        return results

    def process_single_element(self, element, query: str, idx: int, extract_details: bool = True) -> Optional[CafeData]:
        """Process a single element (thread-safe)"""
        try:
            self.stats['total_processed'] += 1

            # Add small random delay to avoid overwhelming
            time.sleep(random.uniform(0.1, 0.3))

            return self.extract_cafe_data(element, query, extract_details)
        except Exception as e:
            self.logger.debug(f"Element {idx} processing failed: {e}")
            return None

    def enrich_cafe_details_from_link(self, cafe: CafeData):
        """Open the cafe's Google Maps place link in a new tab, extract details, then close the tab.
        This is more reliable than clicking list elements and keeps the results view intact."""
        if not cafe.maps_link:
            return

        try:
            # Open in new tab
            self.driver.execute_script("window.open(arguments[0], '_blank');", cafe.maps_link)
            self.anti_detection.rate_limit()

            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # Wait for detail pane elements
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button.CsEnBe[data-item-id="address"]'))
                )
            except TimeoutException:
                # Fallback wait on any header element
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="region"]'))
                )

            # Address
            if not cafe.address:
                try:
                    addr_el = self.driver.find_element(By.CSS_SELECTOR, 'button.CsEnBe[data-item-id="address"] .Io6YTe')
                    txt = addr_el.text.strip()
                    if txt:
                        cafe.address = txt
                except Exception:
                    pass

            # Website
            if not cafe.website:
                try:
                    website_link = self.driver.find_element(By.CSS_SELECTOR, 'a.CsEnBe[data-item-id*="authority"]')
                    url = website_link.get_attribute('href') or ''
                    if url.startswith('http') and 'google.com/maps' not in url:
                        cafe.website = url
                except Exception:
                    pass

            # Phone
            if not cafe.phone:
                try:
                    phone_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.CsEnBe[data-item-id^="phone:tel:"]')
                    aria = (phone_btn.get_attribute('aria-label') or '').strip()
                    if 'Telepon:' in aria:
                        cafe.phone = aria.split('Telepon:')[-1].strip()
                    if not cafe.phone:
                        txt = phone_btn.text.strip()
                        if txt:
                            cafe.phone = txt
                except Exception:
                    # Fallback tel link
                    try:
                        tel_a = self.driver.find_element(By.CSS_SELECTOR, 'a[href^="tel:"]')
                        tel = tel_a.get_attribute('href') or ''
                        if tel.startswith('tel:'):
                            cafe.phone = tel.replace('tel:', '').strip()
                    except Exception:
                        pass

            # Weekly opening hours
            try:
                # Expand if needed
                try:
                    toggle = self.driver.find_element(By.CSS_SELECTOR, 'div.OMl5r[role="button"]')
                    if toggle.get_attribute('aria-expanded') == 'false':
                        toggle.click()
                        time.sleep(0.5)
                except Exception:
                    pass

                rows = self.driver.find_elements(By.CSS_SELECTOR, 'table.eK4R0e tr.y0skZc')
                weekly = {}
                for row in rows:
                    try:
                        day = row.find_element(By.CSS_SELECTOR, 'td.ylH6lf').text.strip()
                        hours = row.find_element(By.CSS_SELECTOR, 'td.mxowUb').text.strip()
                        if day and hours:
                            weekly[day] = hours
                    except Exception:
                        continue
                if weekly:
                    cafe.opening_hours_weekly = weekly
                    if not cafe.opening_hours:
                        rep = weekly.get('Senin') or next(iter(weekly.values()), '')
                        cafe.opening_hours = rep
            except Exception:
                pass

            # Price summary
            try:
                price_btn = self.driver.find_element(By.CSS_SELECTOR, 'div.MNVeJb[role="button"]')
                summary = price_btn.text.strip()
                if summary:
                    cafe.price_range = summary.split('\n')[0].strip()
            except Exception:
                pass

        finally:
            # Close tab and return
            try:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception:
                pass

    def auto_scroll_results(self, max_results: int):
        """Auto-scroll to load more results"""
        try:
            last_count = 0
            no_change_count = 0

            while no_change_count < 3:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Count current results
                current_results = len(self.driver.find_elements(By.CSS_SELECTOR, '.Nv2PK'))

                if current_results > last_count:
                    last_count = current_results
                    no_change_count = 0

                    if current_results >= max_results:
                        self.logger.info(f"🎯 Reached target: {current_results} results")
                        break
                else:
                    no_change_count += 1

        except Exception as e:
            self.logger.warning(f"⚠️ Auto-scroll failed: {e}")

    def quick_test(self, test_query: str = "cafe malioboro yogyakarta", max_results: int = 5, extract_details: bool = True):
        """Quick test with a small sample"""
        self.logger.info(f"🧪 Quick test: {test_query}")

        try:
            self.setup_driver(headless=False)
            results = self.search_and_extract(test_query, max_results, extract_details)

            self.logger.info(f"✅ Test completed: {len(results)} cafes extracted")

            # Save test results
            self.save_data("test_results")

            return results

        finally:
            if self.driver:
                self.driver.quit()

    def full_scrape(self, max_cafes: int = 1000, area_filter: str = None, results_per_query: int = 100,
                   batch_mode: bool = False, batch_size: int = 5, batch_interval: int = 1800,
                   multi_session: bool = False, session_duration: int = 3600, max_queries_per_session: int = 10,
                   resume: bool = False):
        """Full scraping with all strategies and optional batch/multi-session processing"""

        # Handle resume functionality
        if resume:
            if self.load_state():
                self.logger.info("✅ Resuming from previous session")
            else:
                self.logger.info("⚠️  No previous state found, starting fresh")
                resume = False
        else:
            # Clear any existing state if not resuming
            self.clear_state()

        self.logger.info(f"🚀 Starting {'resumed' if resume else 'new'} full scrape (target: {max_cafes} cafes)")

        if batch_mode:
            self.logger.info(f"🔄 Batch mode enabled: {batch_size} queries per batch, {batch_interval/60:.1f}min intervals")
        elif multi_session:
            self.logger.info(f"🔄 Multi-session mode: {max_queries_per_session} queries per session, {session_duration/3600:.1f}h max duration")

        # Print pause/resume instructions
        self.logger.info("ℹ️  Controls: Ctrl+C to pause, then 'r' to resume, 's' to save & quit, 'q' to quit")

        try:
            strategies = self.search_strategies
            if area_filter:
                strategies = [s for s in strategies if area_filter.lower() in s['query'].lower()]

            # Use batch processing if enabled
            if batch_mode:
                batch_processor = BatchProcessor(self, batch_size, batch_interval)
                batch_processor.process_strategies_in_batches(strategies, max_cafes)
                return

            # Use multi-session if enabled
            elif multi_session:
                session_manager = MultiSessionManager(self, session_duration, max_queries_per_session)
                session_manager.process_strategies_with_rotation(strategies, max_cafes)
                return

            # Standard processing with pause/resume support
            self.setup_driver(headless=True)

            # Start from current strategy index if resuming
            start_index = self.current_strategy_index if resume else 0

            for i in range(start_index, len(strategies)):
                # Check for stop signal
                if self.should_stop:
                    self.logger.info("🛑 Stopping scraper as requested")
                    break

                # Handle pause state
                if self.is_paused:
                    self.save_state()  # Save before pausing
                    self.handle_pause()

                    # Check if user chose to quit during pause
                    if self.should_stop:
                        break

                # Update current strategy index
                self.current_strategy_index = i

                if len(self.all_cafes) >= max_cafes:
                    self.logger.info(f"🎯 Target reached: {len(self.all_cafes)} cafes")
                    break

                strategy = strategies[i]
                query = strategy['query']
                expected = min(strategy['expected_results'], results_per_query)  # Use the smaller value

                self.logger.info(f"\n📋 Strategy {i+1}/{len(strategies)}: {query} (max {expected} results)")

                try:
                    results = self.search_and_extract(query, expected)

                    # Track query performance for adaptive optimization
                    if results:
                        self.query_performance[query] = len(results)
                        self.consecutive_empty_queries = 0
                    else:
                        self.consecutive_empty_queries += 1
                        self.query_performance[query] = 0

                    # Switch to high-yield mode if too many empty queries
                    if self.consecutive_empty_queries >= 50 and not self.high_yield_mode:
                        self.logger.info("🔄 Switching to high-yield query mode")
                        self.high_yield_mode = True
                        # Regenerate strategies with high-yield keywords only
                        remaining_strategies = strategies[i+1:]
                        high_yield_strategies = self._generate_search_strategies()
                        strategies = strategies[:i+1] + high_yield_strategies[:len(remaining_strategies)]

                    # Early stopping if too many consecutive empty queries
                    if self.consecutive_empty_queries >= self.max_consecutive_empty:
                        self.logger.warning(f"⚠️ Stopping due to {self.consecutive_empty_queries} consecutive empty queries")
                        break

                    self.logger.info(f"📊 Progress: {len(self.all_cafes)}/{max_cafes} cafes | 🔄 Duplicates: {self.stats['duplicates_removed']} | ✅ Unique: {self.stats['unique_cafes']}")

                    # Save progress periodically and save state
                    if (i + 1) % 20 == 0:
                        self.save_data("progress")
                        self.save_state()

                    # Rate limiting between queries
                    time.sleep(random.uniform(5, 10))

                except KeyboardInterrupt:
                    self.logger.info("⏸️  Keyboard interrupt - pausing...")
                    self.is_paused = True
                    continue
                except Exception as e:
                    self.logger.error(f"❌ Error processing query '{query}': {e}")
                    continue

            # Save final results and clear state if completed successfully
            if not self.should_stop and not self.is_paused:
                self.save_data("final")
                self.clear_state()  # Clear state after successful completion
                self.print_final_summary()
            else:
                # Save current progress
                self.save_data("interrupted")
                self.save_state()
                self.logger.info("💾 Progress saved. Use --resume to continue later.")

        except KeyboardInterrupt:
            self.logger.info("⏸️  Scraping interrupted - saving progress")
            self.save_data("interrupted")
            self.save_state()
        except Exception as e:
            self.logger.error(f"❌ Full scrape failed: {e}")
            self.save_data("error")
            self.save_state()
        finally:
            if self.driver:
                self.driver.quit()

    def print_final_summary(self):
        """Print comprehensive final summary with deduplication stats"""
        duration = time.time() - self.stats['start_time']

        self.logger.info("\n" + "="*60)
        self.logger.info("🎉 SCRAPING COMPLETED - FINAL SUMMARY")
        self.logger.info("="*60)

        # Basic stats
        self.logger.info(f"⏱️  Duration: {duration/60:.1f} minutes")
        self.logger.info(f"📊 Total Elements Processed: {self.stats['total_processed']}")
        self.logger.info(f"✅ Successful Extractions: {self.stats['successful_extractions']}")
        self.logger.info(f"❌ Failed Extractions: {self.stats['failed_extractions']}")

        # Deduplication stats
        self.logger.info("\n🔄 DEDUPLICATION SUMMARY:")
        self.logger.info(f"   • Unique Cafes: {self.stats['unique_cafes']}")
        self.logger.info(f"   • Duplicates Removed: {self.stats['duplicates_removed']}")
        dedup_rate = self.stats['duplicates_removed'] / max(self.stats['total_processed'], 1) * 100
        self.logger.info(f"   • Deduplication Rate: {dedup_rate:.1f}%")
        self.logger.info(f"   • Unique Names Tracked: {len(self.seen_names)}")
        self.logger.info(f"   • Unique Coordinates: {len(self.seen_coordinates)}")

        # Performance stats
        self.logger.info("\n🚀 PARALLEL PROCESSING:")
        self.logger.info(f"   • Max Workers: {self.max_workers}")
        self.logger.info(f"   • Batch Size: {self.batch_size}")
        self.logger.info(f"   • Processing Speed: {self.stats['total_processed']/duration:.1f} elements/min")

        # Quality stats
        if self.all_cafes:
            high_precision = self.stats['high_precision_count']
            precision_rate = high_precision / len(self.all_cafes) * 100
            self.logger.info(f"\n📍 COORDINATE PRECISION:")
            self.logger.info(f"   • High Precision (≥0.8): {high_precision} ({precision_rate:.1f}%)")

            # Top coordinate sources
            sources = {}
            for cafe in self.all_cafes:
                source = cafe.coordinate_source
                sources[source] = sources.get(source, 0) + 1

            self.logger.info(f"   • Coordinate Sources:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"     - {source}: {count}")

        # Pause/Resume info
        self.logger.info(f"\n⏸️ PAUSE/RESUME INFO:")
        self.logger.info(f"   • State files cleared (scraping completed successfully)")
        self.logger.info(f"   • Final strategy index: {self.current_strategy_index + 1}")

        self.logger.info("="*60)

    def save_data(self, suffix: str = ""):
        """Save data in multiple formats"""
        if not self.all_cafes:
            self.logger.warning("⚠️ No data to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if suffix:
            base_name = f"{suffix}_{timestamp}"
            base_dir = os.path.join(self.output_dir, f"{suffix}")
        else:
            base_name = f"cafes_{timestamp}"
            base_dir = self.output_dir

        # Ensure directories exist
        os.makedirs(os.path.join(base_dir, "json"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "csv"), exist_ok=True)

        # Calculate statistics
        precision_scores = [cafe.precision_score for cafe in self.all_cafes]
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0

        sources = {}
        for cafe in self.all_cafes:
            source = cafe.coordinate_source
            sources[source] = sources.get(source, 0) + 1

        metadata = {
            'total_cafes': len(self.all_cafes),
            'scraped_at': datetime.now().isoformat(),
            'scraper_version': 'ultimate_v2.0_parallel_dedup',
            'statistics': self.stats,
            'precision_stats': {
                'avg_precision': avg_precision,
                'high_precision_count': sum(1 for score in precision_scores if score >= 0.8),
                'coordinate_sources': sources
            },
            'deduplication_stats': {
                'unique_cafes': self.stats['unique_cafes'],
                'duplicates_removed': self.stats['duplicates_removed'],
                'deduplication_rate': self.stats['duplicates_removed'] / max(self.stats['total_processed'], 1) * 100,
                'unique_names_tracked': len(self.seen_names),
                'unique_coordinates_tracked': len(self.seen_coordinates),
                'unique_hashes_tracked': len(self.seen_hashes)
            },
            'parallel_processing': {
                'max_workers': self.max_workers,
                'batch_size': self.batch_size,
                'processing_mode': 'parallel_batches'
            }
        }

        # Save JSON
        json_file = os.path.join(base_dir, f"json/{base_name}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': metadata,
                'cafes': [asdict(cafe) for cafe in self.all_cafes]
            }, f, indent=2, ensure_ascii=False)

        # Save CSV
        csv_file = os.path.join(base_dir, f"csv/{base_name}.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.all_cafes:
                writer = csv.DictWriter(f, fieldnames=asdict(self.all_cafes[0]).keys())
                writer.writeheader()
                for cafe in self.all_cafes:
                    writer.writerow(asdict(cafe))

        self.logger.info(f"💾 Data saved:")
        self.logger.info(f"  📄 JSON: {json_file}")
        self.logger.info(f"  📊 CSV: {csv_file}")
        self.logger.info(f"  🎯 {len(self.all_cafes)} cafes, avg precision: {avg_precision:.3f}")

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description='Ultimate Cafe Scraper for Yogyakarta')
    parser.add_argument('--quick-test', action='store_true', help='Run quick test with 5 cafes')
    parser.add_argument('--full-scrape', action='store_true', help='Run full scraping')
    parser.add_argument('--resume', action='store_true', help='Resume from previous session')
    parser.add_argument('--clear-state', action='store_true', help='Clear saved state and start fresh')
    parser.add_argument('--max-cafes', type=int, default=1000, help='Maximum cafes to scrape')
    parser.add_argument('--area', type=str, help='Filter by area (e.g., malioboro, sleman)')
    parser.add_argument('--query', type=str, help='Custom search query')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers (default: 3)')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for parallel processing (default: 10)')
    parser.add_argument('--results-per-query', type=int, default=100, help='Maximum results per query (default: 100)')
    parser.add_argument('--max-empty-queries', type=int, default=100, help='Stop after N consecutive empty queries (default: 20)')

    # Anti-detection and batch processing options
    parser.add_argument('--stealth-mode', action='store_true', help='Enable batch processing with long intervals')
    parser.add_argument('--stealth-batch-size', type=int, default=5, help='Queries per batch in stealth mode (default: 5)')
    parser.add_argument('--stealth-interval', type=int, default=1800, help='Seconds between batches in stealth mode (default: 1800=30min)')

    # Multi-session options
    parser.add_argument('--multi-session', action='store_true', help='Enable multi-session with automatic rotation')
    parser.add_argument('--session-duration', type=int, default=3600, help='Max session duration in seconds (default: 3600=1h)')
    parser.add_argument('--queries-per-session', type=int, default=10, help='Max queries per session (default: 10)')

    # Data extraction options
    parser.add_argument('--extract-details', action='store_true', help='Extract detailed info (phone, website) by clicking on elements (slower but more complete)')
    parser.add_argument('--no-details', action='store_true', help='Skip detailed extraction for faster scraping')

    args = parser.parse_args()

    scraper = UltimateCafeScraper()

    # Configure parallel processing and early stopping
    scraper.max_workers = args.workers
    scraper.batch_size = args.batch_size
    scraper.max_consecutive_empty = args.max_empty_queries

    try:
        if args.clear_state:
            scraper.clear_state()
            print("✅ Previous state cleared")
            return

        if args.quick_test:
            query = args.query or "cafe malioboro yogyakarta"
            extract_details = not args.no_details  # Default True unless --no-details is specified
            scraper.quick_test(query, 5, extract_details)

        elif args.full_scrape or args.resume:
            scraper.full_scrape(
                max_cafes=args.max_cafes,
                area_filter=args.area,
                results_per_query=args.results_per_query,
                batch_mode=args.stealth_mode,
                batch_size=args.stealth_batch_size,
                batch_interval=args.stealth_interval,
                multi_session=args.multi_session,
                session_duration=args.session_duration,
                max_queries_per_session=args.queries_per_session,
                resume=args.resume
            )

        elif args.query:
            scraper.setup_driver(headless=args.headless)
            extract_details = not args.no_details  # Default True unless --no-details is specified
            results = scraper.search_and_extract(args.query, args.max_cafes, extract_details)
            scraper.save_data("custom")
            scraper.driver.quit()

        else:
            print("🎯 ULTIMATE CAFE SCRAPER")
            print("Usage examples:")
            print("  python3 cafe_scraper.py --quick-test")
            print("  python3 cafe_scraper.py --full-scrape --max-cafes 500")
            print("  python3 cafe_scraper.py --resume  # Resume from previous session")
            print("  python3 cafe_scraper.py --clear-state  # Clear saved progress")
            print("  python3 cafe_scraper.py --area malioboro --max-cafes 50")
            print("  python3 cafe_scraper.py --query 'coffee shop sleman' --max-cafes 100")
            print("")
            print("🎮 Pause/Resume Controls:")
            print("  - Press Ctrl+C during scraping to pause")
            print("  - When paused: 'r' to resume, 's' to save & quit, 'q' to quit")
            print("  - Use --resume to continue from where you left off")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
