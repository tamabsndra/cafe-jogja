#!/usr/bin/env python3
"""
Run SIG Cafe Jogja Application
Now using data from cafe_scraper.py
"""

from app import AdvancedSIGApp

if __name__ == '__main__':
    print("🚀 Starting SIG Cafe Jogja Application...")
    print("📊 Loading cafe data from unified scraper...")
    
    app = AdvancedSIGApp()
    app.run(debug=True, host='0.0.0.0', port=5004)