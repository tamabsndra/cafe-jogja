#!/usr/bin/env python3
"""
🚀 MULTI-INSTANCE SCRAPER COORDINATOR
=====================================

Coordinates multiple scraper instances for parallel execution while maintaining anti-detection.
Distributes queries across instances and merges results.

Usage:
    python3 multi_instance_coordinator.py --instances 3 --max-cafes 100000
"""

import json
import time
import random
import logging
import argparse
import os
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

class MultiInstanceCoordinator:
    """Coordinates multiple scraper instances for optimal performance"""

    def __init__(self, num_instances: int = 3, output_dir: str = "data/multi_instance"):
        self.num_instances = num_instances
        self.output_dir = output_dir
        self.setup_logging()
        self.setup_directories()

        # Instance management
        self.instances = []
        self.instance_processes = {}
        self.instance_results = {}

        # Query distribution
        self.query_chunks = []
        self.completed_queries = set()

        # Results aggregation
        self.all_results = []
        self.seen_hashes = set()

    def setup_logging(self):
        """Setup logging for coordinator"""
        os.makedirs('logs', exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - COORDINATOR - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/multi_instance_coordinator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Setup output directories for instances"""
        os.makedirs(self.output_dir, exist_ok=True)
        for i in range(self.num_instances):
            os.makedirs(f"{self.output_dir}/instance_{i}", exist_ok=True)

    def distribute_queries_by_region(self, max_cafes_per_instance: int):
        """Distribute queries geographically to minimize overlap - COMPREHENSIVE MODE"""

        # Regional distribution strategy for comprehensive coverage
        regions = {
            "instance_0": ["malioboro", "tugu", "kraton", "alun alun", "jogja city"],  # Central Yogya
            "instance_1": ["ugm", "condongcatur", "sleman", "depok", "gejayan"],      # North (Sleman)
            "instance_2": ["bantul", "sewon", "kasihan", "parangtritis"],             # South (Bantul)
        }

        # Add more instances if needed
        if self.num_instances > 3:
            regions["instance_3"] = ["kulon progo", "wates", "pengasih"]
            regions["instance_4"] = ["gunungkidul", "wonosari", "playen"]

        query_distribution = {}

        for i in range(self.num_instances):
            instance_key = f"instance_{i}"
            region_keywords = regions.get(instance_key, ["yogyakarta"])  # Default fallback

            query_distribution[instance_key] = {
                'max_cafes': max_cafes_per_instance,
                'area_filter': region_keywords[0],  # Primary area focus
                'priority_areas': region_keywords,
                'instance_id': i,
                'comprehensive_mode': True  # Enable comprehensive coverage
            }

        return query_distribution

    def launch_instance(self, instance_config: Dict) -> subprocess.Popen:
        """Launch a single scraper instance"""
        instance_id = instance_config['instance_id']
        area_filter = instance_config['area_filter']
        max_cafes = instance_config['max_cafes']

        # Stagger start times to avoid simultaneous requests
        start_delay = instance_id * random.uniform(25, 75)

        cmd = [
            'python3', 'cafe_scraper.py',
            '--full-scrape',
            '--max-cafes', str(max_cafes),
            '--area', area_filter,
            '--headless',
            '--multi-session',
            '--queries-per-session', '20',  # Optimal for comprehensive mode
            '--workers', '2',  # Reduced workers per instance
            '--max-empty-queries', '200',  # Extended patience for comprehensive
        ]

        self.logger.info(f"🚀 Launching Instance {instance_id} - Area: {area_filter} - Delay: {start_delay:.1f}s")

        # Start with delay
        time.sleep(start_delay)

        # Change to instance-specific output directory
        env = os.environ.copy()
        env['SCRAPER_OUTPUT_DIR'] = f"{self.output_dir}/instance_{instance_id}"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.getcwd()
        )

        self.instance_processes[instance_id] = process
        return process

    def monitor_instances(self, query_distribution: Dict):
        """Monitor running instances and collect results"""

        with ThreadPoolExecutor(max_workers=self.num_instances) as executor:
            # Launch all instances
            futures = {}
            for instance_key, config in query_distribution.items():
                future = executor.submit(self.launch_instance, config)
                futures[future] = config['instance_id']

            # Monitor completion
            completed_instances = 0
            while completed_instances < self.num_instances:
                time.sleep(60)  # Check every minute

                for instance_id, process in list(self.instance_processes.items()):
                    if process.poll() is not None:  # Process finished
                        if instance_id not in self.instance_results:
                            self.logger.info(f"✅ Instance {instance_id} completed")
                            self.collect_instance_results(instance_id)
                            completed_instances += 1

                # Log progress
                total_cafes = sum(len(results) for results in self.instance_results.values())
                self.logger.info(f"📊 Progress: {completed_instances}/{self.num_instances} instances done, {total_cafes} cafes collected")

    def collect_instance_results(self, instance_id: int):
        """Collect results from a completed instance"""
        instance_dir = f"{self.output_dir}/instance_{instance_id}"

        # Find the latest results file
        json_files = []
        for root, dirs, files in os.walk(instance_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))

        if not json_files:
            self.logger.warning(f"⚠️ No results found for instance {instance_id}")
            self.instance_results[instance_id] = []
            return

        # Get the most recent file
        latest_file = max(json_files, key=os.path.getmtime)

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cafes = data.get('cafes', [])
                self.instance_results[instance_id] = cafes
                self.logger.info(f"📊 Instance {instance_id}: {len(cafes)} cafes collected")

        except Exception as e:
            self.logger.error(f"❌ Failed to load results from instance {instance_id}: {e}")
            self.instance_results[instance_id] = []

    def merge_and_deduplicate_results(self):
        """Merge results from all instances and remove duplicates"""
        self.logger.info("🔄 Merging and deduplicating results...")

        all_cafes = []
        seen_hashes = set()
        duplicates_removed = 0

        for instance_id, cafes in self.instance_results.items():
            self.logger.info(f"📋 Processing {len(cafes)} cafes from instance {instance_id}")

            for cafe_dict in cafes:
                # Create hash for deduplication
                name = cafe_dict.get('name', '').lower().strip()
                lat = cafe_dict.get('lat', 0)
                lon = cafe_dict.get('lon', 0)

                unique_string = f"{name}_{lat:.6f}_{lon:.6f}"
                import hashlib
                cafe_hash = hashlib.md5(unique_string.encode()).hexdigest()

                if cafe_hash not in seen_hashes:
                    seen_hashes.add(cafe_hash)
                    cafe_dict['source_instance'] = instance_id
                    all_cafes.append(cafe_dict)
                else:
                    duplicates_removed += 1

        self.all_results = all_cafes

        self.logger.info(f"✅ Merged results:")
        self.logger.info(f"   • Total unique cafes: {len(all_cafes)}")
        self.logger.info(f"   • Duplicates removed: {duplicates_removed}")
        self.logger.info(f"   • Deduplication rate: {duplicates_removed/(len(all_cafes)+duplicates_removed)*100:.1f}%")

    def save_final_results(self, suffix: str = "merged"):
        """Save final merged results"""
        if not self.all_results:
            self.logger.warning("⚠️ No results to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Metadata
        metadata = {
            'total_cafes': len(self.all_results),
            'scraped_at': datetime.now().isoformat(),
            'scraper_version': 'multi_instance_v1.0',
            'coordination_stats': {
                'num_instances': self.num_instances,
                'instances_completed': len(self.instance_results),
                'total_duplicates_removed': sum(len(cafes) for cafes in self.instance_results.values()) - len(self.all_results)
            },
            'instance_contributions': {
                f'instance_{iid}': len(cafes)
                for iid, cafes in self.instance_results.items()
            }
        }

        # Save merged JSON
        output_file = os.path.join(self.output_dir, f"{suffix}_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': metadata,
                'cafes': self.all_results
            }, f, indent=2, ensure_ascii=False)

        self.logger.info(f"💾 Final results saved: {output_file}")
        self.logger.info(f"🎯 Total cafes: {len(self.all_results)}")

        return output_file

    def run_coordinated_scraping(self, max_cafes: int):
        """Run coordinated multi-instance scraping"""
        self.logger.info(f"🚀 Starting coordinated scraping with {self.num_instances} instances")
        self.logger.info(f"🎯 Target: {max_cafes} cafes total")

        # Distribute target across instances
        max_cafes_per_instance = max_cafes // self.num_instances + (max_cafes % self.num_instances)

        # Create query distribution
        query_distribution = self.distribute_queries_by_region(max_cafes_per_instance)

        try:
            # Launch and monitor instances
            self.monitor_instances(query_distribution)

            # Process results
            self.merge_and_deduplicate_results()

            # Save final results
            final_file = self.save_final_results()

            self.logger.info("🎉 Coordinated scraping completed successfully!")
            return final_file

        except KeyboardInterrupt:
            self.logger.info("⏸️ Coordinated scraping interrupted")
            self.cleanup_instances()
        except Exception as e:
            self.logger.error(f"❌ Coordinated scraping failed: {e}")
            self.cleanup_instances()

    def cleanup_instances(self):
        """Clean up running instances"""
        self.logger.info("🧹 Cleaning up instances...")
        for instance_id, process in self.instance_processes.items():
            if process.poll() is None:  # Still running
                process.terminate()
                self.logger.info(f"🛑 Terminated instance {instance_id}")


def main():
    """Main function for multi-instance coordination"""
    parser = argparse.ArgumentParser(description='Multi-Instance Cafe Scraper Coordinator')
    parser.add_argument('--instances', type=int, default=3, help='Number of scraper instances (default: 3)')
    parser.add_argument('--max-cafes', type=int, default=100000, help='Total target cafes (default: 100000)')
    parser.add_argument('--output-dir', type=str, default='data/multi_instance', help='Output directory')

    args = parser.parse_args()

    # Validate instance count
    max_instances = multiprocessing.cpu_count() - 1
    if args.instances > max_instances:
        print(f"⚠️ Warning: {args.instances} instances requested, but only {max_instances} CPU cores available")

    coordinator = MultiInstanceCoordinator(
        num_instances=args.instances,
        output_dir=args.output_dir
    )

    try:
        final_file = coordinator.run_coordinated_scraping(args.max_cafes)
        print(f"✅ Scraping completed! Results saved to: {final_file}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
