import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import logging
from pathlib import Path
import sys
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cafe_merger.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CafeDataMerger:
    def __init__(self, enable_progress_bar: bool = True):
        self.merged_cafes = {}
        self.all_files_metadata = []
        self.enable_progress_bar = enable_progress_bar
        self.stats = {
            'total_processed': 0,
            'total_unique': 0,
            'total_duplicates': 0,
            'total_errors': 0
        }

    def get_json_files_from_folder(self, folder_path: str, pattern: str = "*.json") -> List[str]:
        """Get all JSON files from a folder with better error handling"""
        folder_path = Path(folder_path)

        if not folder_path.exists():
            logger.error(f"Folder not found: {folder_path}")
            return []

        if not folder_path.is_dir():
            logger.error(f"Path is not a directory: {folder_path}")
            return []

        # Use glob to find all JSON files
        search_pattern = folder_path / pattern
        json_files = list(folder_path.glob(pattern))

        if not json_files:
            logger.warning(f"No JSON files found in {folder_path} with pattern {pattern}")
            return []

        # Convert to strings and sort for consistent processing
        json_files = sorted([str(f) for f in json_files])

        logger.info(f"Found {len(json_files)} JSON files in {folder_path}:")
        for file in json_files:
            logger.info(f"  - {Path(file).name}")

        return json_files

    def load_json_file(self, filepath: str) -> Optional[Dict]:
        """Load and parse JSON file with enhanced error handling"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Successfully loaded {filepath}")
                return data
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            self.stats['total_errors'] += 1
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            self.stats['total_errors'] += 1
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            self.stats['total_errors'] += 1

        return None

    def generate_cafe_key(self, cafe: Dict) -> str:
        """Generate unique key for cafe based on name and coordinates with fallback"""
        name = cafe.get('name', '').strip().lower()
        lat = str(cafe.get('lat', ''))
        lon = str(cafe.get('lon', ''))

        # Create hash from name + coordinates for unique identification
        key_string = f"{name}_{lat}_{lon}"
        return hashlib.md5(key_string.encode()).hexdigest()[:12]

    def is_better_data(self, existing_cafe: Dict, new_cafe: Dict) -> bool:
        """Determine if new cafe data is better than existing data with enhanced logic"""
        # Prioritize data completeness
        existing_score = self.calculate_completeness_score(existing_cafe)
        new_score = self.calculate_completeness_score(new_cafe)

        if new_score > existing_score:
            return True
        elif new_score == existing_score:
            # If completeness is same, prefer newer data or higher ratings
            existing_rating = existing_cafe.get('rating', 0)
            new_rating = new_cafe.get('rating', 0)

            # Also consider review count for tie-breaking
            if new_rating == existing_rating:
                existing_reviews = existing_cafe.get('reviews_count', 0)
                new_reviews = new_cafe.get('reviews_count', 0)
                return new_reviews > existing_reviews

            return new_rating > existing_rating

        return False

    def calculate_completeness_score(self, cafe: Dict) -> int:
        """Calculate data completeness score with weighted fields"""
        score = 0
        field_weights = {
            'address': 2,
            'rating': 1,
            'reviews_count': 1,
            'price_range': 1,
            'phone': 1,
            'website': 1,
            'opening_hours': 1,
            'opening_hours_weekly': 3,  # Weekly hours are more valuable
            'maps_link': 1,
            'district': 1,
            'village': 1,
            'regency': 1
        }

        for field, weight in field_weights.items():
            value = cafe.get(field)
            if value and value != "" and value != 0 and value != {}:
                if field == 'opening_hours_weekly' and isinstance(value, dict) and len(value) > 0:
                    score += weight
                elif isinstance(value, (str, int, float)) and value:
                    score += weight

        return score

    def merge_cafe_data(self, existing_cafe: Dict, new_cafe: Dict) -> Dict:
        """Merge two cafe entries, keeping the best data from each with enhanced logic"""
        merged = existing_cafe.copy()

        # For each field, keep the more complete or newer data
        for key, value in new_cafe.items():
            existing_value = merged.get(key)

            # Skip metadata fields
            if key in ['scraped_at', 'search_query', 'coordinate_source', 'precision_score']:
                continue

            # If existing value is empty/null and new value has content
            if (not existing_value or existing_value == "" or existing_value == 0 or existing_value == {}) and value:
                merged[key] = value
            # For ratings, keep higher rating
            elif key == 'rating' and isinstance(value, (int, float)) and value > existing_value:
                merged[key] = value
            # For review counts, keep higher count
            elif key == 'reviews_count' and isinstance(value, int) and value > existing_value:
                merged[key] = value
            # For opening_hours_weekly, merge the dictionaries intelligently
            elif key == 'opening_hours_weekly' and isinstance(value, dict) and isinstance(existing_value, dict):
                merged[key] = {**existing_value, **value}
            # For addresses, prefer longer/more detailed ones
            elif key == 'address' and isinstance(value, str) and isinstance(existing_value, str):
                if len(value) > len(existing_value):
                    merged[key] = value

        # Update scraped_at to latest
        existing_time = existing_cafe.get('scraped_at')
        new_time = new_cafe.get('scraped_at')

        if existing_time and new_time:
            try:
                existing_dt = datetime.fromisoformat(existing_time.replace('Z', '+00:00'))
                new_dt = datetime.fromisoformat(new_time.replace('Z', '+00:00'))
                merged['scraped_at'] = new_time if new_dt > existing_dt else existing_time
            except ValueError:
                merged['scraped_at'] = new_time or existing_time
        else:
            merged['scraped_at'] = new_time or existing_time

        return merged

    def process_folder(self, folder_path: str, pattern: str = "*.json") -> Optional[Dict]:
        """Process all JSON files in a folder with progress tracking"""
        json_files = self.get_json_files_from_folder(folder_path, pattern)
        if not json_files:
            return None

        return self.process_files(json_files)

    def process_files(self, file_paths: List[str]) -> Optional[Dict]:
        """Process multiple JSON files and merge cafe data with enhanced progress tracking"""
        self.stats = {'total_processed': 0, 'total_unique': 0, 'total_duplicates': 0, 'total_errors': 0}

        logger.info("Starting to process files...")

        # Use tqdm for progress bar if enabled
        file_iterator = tqdm(file_paths, desc="Processing files") if self.enable_progress_bar else file_paths

        for filepath in file_iterator:
            if not os.path.exists(filepath):
                logger.error(f"File not found: {filepath}")
                self.stats['total_errors'] += 1
                continue

            logger.info(f"Processing: {Path(filepath).name}")
            data = self.load_json_file(filepath)

            if not data or 'cafes' not in data:
                logger.warning(f"Invalid data format in {filepath}")
                self.stats['total_errors'] += 1
                continue

            # Store metadata
            if 'metadata' in data:
                self.all_files_metadata.append({
                    'file': filepath,
                    'metadata': data['metadata']
                })

            # Process cafes
            cafes = data['cafes']
            file_processed = len(cafes)
            file_duplicates = 0

            for cafe in cafes:
                self.stats['total_processed'] += 1
                cafe_key = self.generate_cafe_key(cafe)

                if cafe_key in self.merged_cafes:
                    # Duplicate found - merge data
                    file_duplicates += 1
                    self.stats['total_duplicates'] += 1
                    existing_cafe = self.merged_cafes[cafe_key]

                    if self.is_better_data(existing_cafe, cafe):
                        # Replace with better data but merge useful fields
                        self.merged_cafes[cafe_key] = self.merge_cafe_data(existing_cafe, cafe)
                    else:
                        # Keep existing but merge useful fields from new data
                        self.merged_cafes[cafe_key] = self.merge_cafe_data(existing_cafe, cafe)
                else:
                    # New unique cafe
                    self.merged_cafes[cafe_key] = cafe
                    self.stats['total_unique'] += 1

            logger.info(f"  - Processed: {file_processed} cafes")
            logger.info(f"  - Duplicates in this file: {file_duplicates}")

        self._print_summary()
        return self.create_final_output()

    def _print_summary(self):
        """Print processing summary with enhanced formatting"""
        logger.info(f"\n{'='*50}")
        logger.info("PROCESSING SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total cafes processed: {self.stats['total_processed']}")
        logger.info(f"Unique cafes found: {self.stats['total_unique']}")
        logger.info(f"Duplicates removed: {self.stats['total_duplicates']}")
        logger.info(f"Errors encountered: {self.stats['total_errors']}")
        logger.info(f"Final unique cafes: {len(self.merged_cafes)}")
        logger.info(f"{'='*50}")

    def create_final_output(self) -> Dict:
        """Create final merged output with enhanced metadata"""
        final_cafes = list(self.merged_cafes.values())

        # Sort by rating (descending) then by review count (descending)
        final_cafes.sort(key=lambda x: (x.get('rating', 0), x.get('reviews_count', 0)), reverse=True)

        # Calculate enhanced statistics
        ratings = [cafe.get('rating', 0) for cafe in final_cafes if cafe.get('rating', 0) > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        # Create comprehensive metadata
        merged_metadata = {
            "total_cafes": len(final_cafes),
            "merged_at": datetime.now().isoformat(),
            "merger_version": "python_deduplicator_v2.0",
            "source_files": [meta['file'] for meta in self.all_files_metadata],
            "merge_statistics": {
                "total_unique_cafes": len(final_cafes),
                "source_files_count": len(self.all_files_metadata),
                "avg_rating": round(avg_rating, 2),
                "total_reviews": sum(cafe.get('reviews_count', 0) for cafe in final_cafes),
                "cafes_with_ratings": len(ratings),
                "cafes_with_reviews": len([c for c in final_cafes if c.get('reviews_count', 0) > 0])
            },
            "cafe_types_distribution": self.get_type_distribution(final_cafes),
            "location_distribution": self.get_location_distribution(final_cafes),
            "price_range_distribution": self.get_price_distribution(final_cafes),
            "original_files_metadata": self.all_files_metadata
        }

        return {
            "metadata": merged_metadata,
            "cafes": final_cafes
        }

    def get_type_distribution(self, cafes: List[Dict]) -> Dict:
        """Get distribution of cafe types"""
        type_count = {}
        for cafe in cafes:
            cafe_type = cafe.get('type', 'Unknown')
            type_count[cafe_type] = type_count.get(cafe_type, 0) + 1
        return type_count

    def get_location_distribution(self, cafes: List[Dict]) -> Dict:
        """Get distribution of cafe locations"""
        location_count = {}
        for cafe in cafes:
            district = cafe.get('district', 'Unknown')
            location_count[district] = location_count.get(district, 0) + 1
        return location_count

    def get_price_distribution(self, cafes: List[Dict]) -> Dict:
        """Get distribution of cafe price ranges"""
        price_count = {}
        for cafe in cafes:
            price_range = cafe.get('price_range', 'Unknown')
            price_count[price_range] = price_count.get(price_range, 0) + 1
        return price_count

    def save_merged_data(self, output_path: str, merged_data: Dict) -> bool:
        """Save merged data to JSON file with error handling"""
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Merged data saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False

    def print_comparison_report(self):
        """Print detailed comparison report with enhanced formatting"""
        logger.info(f"\n{'='*60}")
        logger.info("DETAILED CAFE COMPARISON REPORT")
        logger.info(f"{'='*60}")

        for i, cafe in enumerate(self.merged_cafes.values(), 1):
            logger.info(f"\n{i}. {cafe.get('name', 'Unknown')}")
            logger.info(f"   Rating: {cafe.get('rating', 'N/A')} ({cafe.get('reviews_count', 0)} reviews)")
            logger.info(f"   Address: {cafe.get('address', 'No address')}")
            logger.info(f"   Price Range: {cafe.get('price_range', 'No price info')}")
            logger.info(f"   Type: {cafe.get('type', 'Unknown')}")
            logger.info(f"   District: {cafe.get('district', 'Unknown')}")
            logger.info(f"   Hours: {cafe.get('opening_hours', 'No hours')}")
            if cafe.get('phone'):
                logger.info(f"   Phone: {cafe.get('phone')}")
            if cafe.get('website'):
                logger.info(f"   Website: {cafe.get('website')}")

def merge_cafe_folder(folder_path: str, pattern: str = "*.json", output_file: str = None,
                     enable_progress_bar: bool = True) -> Optional[Dict]:
    """
    Simple function to merge all cafe JSON files in a folder

    Args:
        folder_path: Path to folder containing JSON files
        pattern: File pattern to match (default: "*.json")
        output_file: Output file path (optional)
        enable_progress_bar: Whether to show progress bar (default: True)

    Returns:
        Dict: Merged cafe data or None if failed
    """
    merger = CafeDataMerger(enable_progress_bar=enable_progress_bar)
    merged_data = merger.process_folder(folder_path, pattern)

    if output_file and merged_data:
        merger.save_merged_data(output_file, merged_data)

    return merged_data

def merge_cafe_files(input_files: List[str], output_file: str = None,
                    enable_progress_bar: bool = True) -> Optional[Dict]:
    """
    Simple function to merge cafe JSON files

    Args:
        input_files: List of JSON file paths
        output_file: Output file path (optional)
        enable_progress_bar: Whether to show progress bar (default: True)

    Returns:
        Dict: Merged cafe data or None if failed
    """
    merger = CafeDataMerger(enable_progress_bar=enable_progress_bar)
    merged_data = merger.process_files(input_files)

    if output_file and merged_data:
        merger.save_merged_data(output_file, merged_data)

    return merged_data

def main():
    """Main function with improved user interface and error handling"""
    print("=== CAFE JSON MERGER v2.0 ===")
    print("Choose processing method:")
    print("1. Process entire folder")
    print("2. Process specific files")
    print("3. Quick test with sample data")

    try:
        choice = input("Enter choice (1, 2, or 3): ").strip()

        if choice == "1":
            # Process folder
            folder_path = input("Enter folder path (or press Enter for current directory): ").strip()
            if not folder_path:
                folder_path = "."

            pattern = input("Enter file pattern (or press Enter for *.json): ").strip()
            if not pattern:
                pattern = "*.json"

            output_file = input("Enter output filename (or press Enter for auto-generated): ").strip()
            if not output_file:
                output_file = f"merged_cafes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            print(f"\nProcessing folder: {folder_path}")
            print(f"Pattern: {pattern}")
            print(f"Output: {output_file}")

            result = merge_cafe_folder(folder_path, pattern, output_file)

        elif choice == "2":
            # Process specific files
            print("Enter JSON file paths (one per line, empty line to finish):")
            files = []
            while True:
                file_path = input().strip()
                if not file_path:
                    break
                files.append(file_path)

            if files:
                output_file = input("Enter output filename (or press Enter for auto-generated): ").strip()
                if not output_file:
                    output_file = f"merged_cafes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                result = merge_cafe_files(files, output_file)
            else:
                print("No files provided")
                return None

        elif choice == "3":
            # Quick test with current directory
            print("Running quick test with current directory...")
            result = merge_cafe_folder(".", "*.json", "quick_test_output.json")

        else:
            print("Invalid choice")
            return None

        if result:
            print(f"\n✅ Merging completed successfully!")
            print(f"Total unique cafes: {len(result['cafes'])}")
            if result['cafes']:
                avg_rating = result['metadata']['merge_statistics']['avg_rating']
                total_reviews = result['metadata']['merge_statistics']['total_reviews']
                print(f"Average rating: {avg_rating}")
                print(f"Total reviews: {total_reviews}")

                # Show top cafes
                print(f"\n🏆 Top 3 cafes by rating:")
                for i, cafe in enumerate(result['cafes'][:3], 1):
                    print(f"{i}. {cafe.get('name', 'Unknown')} - Rating: {cafe.get('rating', 'N/A')}")
        else:
            print("❌ No data to merge or processing failed")

        return result

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ An error occurred: {e}")
        return None

if __name__ == "__main__":
    main()
