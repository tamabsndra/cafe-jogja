#!/usr/bin/env python3
"""
Usage:
    python3 scraper_monitor.py
"""

import json
import os
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

class ScraperMonitor:

    def __init__(self):
        self.progress_file = "scraping_progress.json"
        self.data_file = "cafes_test_results_20250828_090743.json"
        self.log_file = "cafe_scraper.log"

    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {}

    def load_data(self):
        """Load scraped data"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def print_progress_summary(self):
        """Print current progress summary"""
        progress = self.load_progress()
        data = self.load_data()

        print("📊 LARGE SCALE SCRAPER PROGRESS")
        print("=" * 40)

        if progress:
            completed = progress.get('completed_queries', 0)
            total = progress.get('total_queries', 0)
            percentage = (completed / max(total, 1)) * 100

            print(f"🔍 Queries Progress: {completed}/{total} ({percentage:.1f}%)")
            print(f"📝 Last Query: {progress.get('last_query', 'N/A')}")
            print(f"📊 Total Cafes: {progress.get('total_cafes', 0):,}")

        if data.get('metadata'):
            metadata = data['metadata']
            print(f"\n📈 Data Statistics:")
            print(f"   Total Cafes: {metadata.get('total_cafes', 0):,}")
            print(f"   Success Rate: {metadata.get('success_rate', 0):.1f}%")
            print(f"   Elapsed Time: {metadata.get('elapsed_time', 0)/3600:.1f} hours")

            if metadata.get('total_cafes', 0) > 0:
                rate = metadata.get('total_cafes', 0) / max(metadata.get('elapsed_time', 1)/3600, 0.1)
                print(f"   Scraping Rate: {rate:.1f} cafes/hour")

        # File sizes
        if os.path.exists(self.data_file):
            size_mb = os.path.getsize(self.data_file) / (1024 * 1024)
            print(f"\n📁 Data File Size: {size_mb:.1f} MB")

        if os.path.exists(self.log_file):
            log_size_mb = os.path.getsize(self.log_file) / (1024 * 1024)
            print(f"📋 Log File Size: {log_size_mb:.1f} MB")

    def analyze_data_quality(self):
        """Analyze quality of scraped data"""
        data = self.load_data()
        cafes = data.get('cafes', [])

        if not cafes:
            print("❌ No data to analyze")
            return

        print(f"\n🔍 DATA QUALITY ANALYSIS")
        print("=" * 30)

        # Field completeness
        fields = ['name', 'address', 'rating', 'lat', 'lon', 'regency', 'type']
        completeness = {}

        for field in fields:
            filled = sum(1 for cafe in cafes if cafe.get(field) and str(cafe.get(field)).strip())
            completeness[field] = (filled / len(cafes)) * 100

        print("📋 Field Completeness:")
        for field, percentage in completeness.items():
            status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
            print(f"   {status} {field}: {percentage:.1f}%")

        # Geographic distribution
        regency_counts = {}
        type_counts = {}

        for cafe in cafes:
            regency = cafe.get('regency', 'Unknown')
            cafe_type = cafe.get('type', 'Unknown')

            regency_counts[regency] = regency_counts.get(regency, 0) + 1
            type_counts[cafe_type] = type_counts.get(cafe_type, 0) + 1

        print(f"\n🏛️ Geographic Distribution:")
        for regency, count in sorted(regency_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {regency}: {count:,} ({count/len(cafes)*100:.1f}%)")

        print(f"\n🏷️ Type Distribution:")
        for cafe_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cafe_type}: {count:,} ({count/len(cafes)*100:.1f}%)")

        # Rating analysis
        ratings = [cafe.get('rating', 0) for cafe in cafes if cafe.get('rating', 0) > 0]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            print(f"\n⭐ Rating Analysis:")
            print(f"   Average Rating: {avg_rating:.1f}/5.0")
            print(f"   Rated Cafes: {len(ratings):,}/{len(cafes):,} ({len(ratings)/len(cafes)*100:.1f}%)")

    def estimate_completion_time(self):
        """Estimate completion time based on current progress"""
        progress = self.load_progress()
        data = self.load_data()

        if not progress or not data.get('metadata'):
            print("❌ Insufficient data for estimation")
            return

        completed_queries = progress.get('completed_queries', 0)
        total_queries = progress.get('total_queries', 1)
        elapsed_time = data['metadata'].get('elapsed_time', 0)

        if completed_queries == 0:
            print("❌ No queries completed yet")
            return

        # Calculate rates
        time_per_query = elapsed_time / completed_queries
        remaining_queries = total_queries - completed_queries
        estimated_remaining_time = remaining_queries * time_per_query

        # Current cafe collection rate
        current_cafes = data['metadata'].get('total_cafes', 0)
        cafes_per_hour = current_cafes / max(elapsed_time / 3600, 0.1)

        print(f"\n⏰ TIME ESTIMATION")
        print("=" * 20)
        print(f"📊 Progress: {completed_queries}/{total_queries} queries ({completed_queries/total_queries*100:.1f}%)")
        print(f"⏱️ Time per query: {time_per_query:.1f} seconds")
        print(f"🕐 Estimated remaining: {estimated_remaining_time/3600:.1f} hours")
        print(f"📈 Current rate: {cafes_per_hour:.1f} cafes/hour")

        # Estimate completion time
        completion_time = datetime.now() + timedelta(seconds=estimated_remaining_time)
        print(f"🏁 Estimated completion: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def show_top_cafes(self, n=10):
        """Show top rated cafes"""
        data = self.load_data()
        cafes = data.get('cafes', [])

        if not cafes:
            print("❌ No cafe data available")
            return

        # Sort by rating
        rated_cafes = [cafe for cafe in cafes if cafe.get('rating', 0) > 0]
        top_cafes = sorted(rated_cafes, key=lambda x: x.get('rating', 0), reverse=True)[:n]

        print(f"\n🏆 TOP {n} RATED CAFES")
        print("=" * 30)

        for i, cafe in enumerate(top_cafes, 1):
            rating = cafe.get('rating', 0)
            reviews = cafe.get('reviews_count', 0)
            regency = cafe.get('regency', 'Unknown')
            cafe_type = cafe.get('type', 'Unknown')

            print(f"{i:2d}. {cafe['name']}")
            print(f"    ⭐ {rating}/5.0 ({reviews:,} reviews)")
            print(f"    📍 {regency} - {cafe_type}")
            print()

    def generate_report(self):
        """Generate comprehensive progress report"""
        print("📋 GENERATING COMPREHENSIVE REPORT...")
        print("=" * 40)

        self.print_progress_summary()
        self.analyze_data_quality()
        self.estimate_completion_time()
        self.show_top_cafes()

        # Save report to file
        report_file = f"scraper_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        print(f"\n💾 Report saved to: {report_file}")

    def watch_progress(self, interval=30):
        """Watch progress in real-time"""
        print(f"👁️ Watching scraper progress (updates every {interval}s)")
        print("Press Ctrl+C to stop watching")
        print("=" * 50)

        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                print(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")
                self.print_progress_summary()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Stopped watching")

def main():
    """Main monitor function"""
    monitor = ScraperMonitor()

    print("📊 Scraper Monitor & Progress Tracker")
    print("=" * 40)

    while True:
        print("\nChoose an option:")
        print("1. 📊 Show Progress Summary")
        print("2. 🔍 Analyze Data Quality")
        print("3. ⏰ Estimate Completion Time")
        print("4. 🏆 Show Top Rated Cafes")
        print("5. 📋 Generate Full Report")
        print("6. 👁️ Watch Progress (Real-time)")
        print("7. ❌ Exit")

        choice = input("\nEnter choice (1-7): ").strip()

        if choice == "1":
            monitor.print_progress_summary()
        elif choice == "2":
            monitor.analyze_data_quality()
        elif choice == "3":
            monitor.estimate_completion_time()
        elif choice == "4":
            n = input("Number of top cafes to show (default 10): ").strip()
            n = int(n) if n.isdigit() else 10
            monitor.show_top_cafes(n)
        elif choice == "5":
            monitor.generate_report()
        elif choice == "6":
            interval = input("Update interval in seconds (default 30): ").strip()
            interval = int(interval) if interval.isdigit() else 30
            monitor.watch_progress(interval)
        elif choice == "7":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
