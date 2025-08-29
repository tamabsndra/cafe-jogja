#!/usr/bin/env python3
"""
Advanced SIG Cafe Jogja Application
Enhanced version with advanced features for large dataset

Features:
- Advanced filtering and search
- Interactive visualizations
- Performance optimization
- Real-time data analysis
- Export capabilities
"""

import json
import pandas as pd
import folium
from folium import plugins
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.utils
from flask import Flask, render_template, request, jsonify, send_file
import numpy as np
from datetime import datetime
import io
import base64
from collections import Counter
import math
import os

class AdvancedSIGApp:
    """Advanced SIG Application for Cafe Analysis"""

    def __init__(self):
        self.app = Flask(__name__)
        self.cafe_data = None
        self.load_large_scale_data()
        self.setup_routes()

    def load_large_scale_data(self):
        """Load scraped data from cafe_scraper.py"""
        try:
            # Try to load from new scraper first, fallback to old data
            data_files = [
                'data/progress/json/progress_20250829_084903.json'
            ]

            data = None
            for file_path in data_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    break

            if not data:
                raise FileNotFoundError("No cafe data found")

            self.metadata = data.get('metadata', {})

            # Add missing metadata fields for template compatibility
            if 'statistics' in self.metadata:
                stats = self.metadata['statistics']
                self.metadata['total_processed'] = stats.get('total_processed', 0)
                self.metadata['success_rate'] = round((stats.get('successful_extractions', 0) / max(stats.get('total_processed', 1), 1)) * 100, 1)

                # Calculate elapsed time from start_time
                if 'start_time' in stats:
                    import time
                    elapsed_seconds = time.time() - stats['start_time']
                    self.metadata['elapsed_time'] = elapsed_seconds

            cafes = data.get('cafes', [])

            # Convert to DataFrame for better analysis
            self.cafe_data = pd.DataFrame(cafes)

            # Data cleaning and preprocessing
            self.preprocess_data()

            print(f"✅ Loaded {len(self.cafe_data)} cafes successfully!")
            print(f"📊 Data coverage: {self.cafe_data['regency'].value_counts().to_dict()}")

        except Exception as e:
            print(f"❌ Failed to load data: {e}")
            self.load_fallback_data()

    def preprocess_data(self):
        """Preprocess and clean the data"""
        if self.cafe_data is None or self.cafe_data.empty:
            return

        # Fill missing values
        self.cafe_data['rating'] = pd.to_numeric(self.cafe_data['rating'], errors='coerce').fillna(0)
        self.cafe_data['reviews_count'] = pd.to_numeric(self.cafe_data['reviews_count'], errors='coerce').fillna(0)
        self.cafe_data['lat'] = pd.to_numeric(self.cafe_data['lat'], errors='coerce')
        self.cafe_data['lon'] = pd.to_numeric(self.cafe_data['lon'], errors='coerce')

        # Remove invalid coordinates
        self.cafe_data = self.cafe_data.dropna(subset=['lat', 'lon'])

        # Standardize regency names
        regency_mapping = {
            'yogyakarta': 'Yogyakarta',
            'sleman': 'Sleman',
            'bantul': 'Bantul',
            'kulon progo': 'Kulon Progo',
            'gunung kidul': 'Gunung Kidul'
        }

        self.cafe_data['regency'] = self.cafe_data['regency'].str.lower().map(regency_mapping).fillna(self.cafe_data['regency'])

        # Create popularity score
        self.cafe_data['popularity_score'] = (
            self.cafe_data['rating'] * 0.7 +
            np.log1p(self.cafe_data['reviews_count']) * 0.3
        ).round(2)

        # Extract price range numbers
        self.cafe_data['price_min'] = self.cafe_data['price_range'].str.extract(r'(\d+)').astype(float).fillna(0)

        # Create price categories
        def categorize_price(price_range):
            if pd.isna(price_range) or price_range == "":
                return "Unknown"
            if "25" in str(price_range) or "20" in str(price_range):
                return "Budget (< 50k)"
            elif "50" in str(price_range) or "75" in str(price_range):
                return "Mid-range (50-100k)"
            elif "100" in str(price_range):
                return "Premium (> 100k)"
            else:
                return "Unknown"

        self.cafe_data['price_category'] = self.cafe_data['price_range'].apply(categorize_price)

        print(f"🔧 Data preprocessing completed")
        print(f"📊 Rating range: {self.cafe_data['rating'].min():.1f} - {self.cafe_data['rating'].max():.1f}")
        print(f"📊 Reviews range: {self.cafe_data['reviews_count'].min():.0f} - {self.cafe_data['reviews_count'].max():.0f}")

    def load_fallback_data(self):
        """Load fallback sample data if main data fails"""
        sample_data = [
            {
                "name": "Sample Cafe 1", "lat": -7.7749, "lon": 110.3737,
                "rating": 4.5, "reviews_count": 100, "regency": "Sleman",
                "type": "Modern", "price_range": "Rp 25-50 rb", "address": "Sample Address"
            }
        ]
        self.cafe_data = pd.DataFrame(sample_data)
        self.preprocess_data()

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            return render_template('advanced_index.html',
                                 total_cafes=len(self.cafe_data),
                                 metadata=self.metadata)

        @self.app.route('/api/cafes')
        def get_cafes():
            """Get cafes with filtering"""
            # Get filter parameters
            regency = request.args.get('regency', '')
            cafe_type = request.args.get('type', '')
            min_rating = float(request.args.get('min_rating', 0))
            max_rating = float(request.args.get('max_rating', 5))
            price_category = request.args.get('price_category', '')
            search_query = request.args.get('search', '')

            # Apply filters
            filtered_data = self.cafe_data.copy()

            if regency:
                filtered_data = filtered_data[filtered_data['regency'] == regency]

            if cafe_type:
                filtered_data = filtered_data[filtered_data['type'] == cafe_type]

            if min_rating > 0 or max_rating < 5:
                filtered_data = filtered_data[
                    (filtered_data['rating'] >= min_rating) &
                    (filtered_data['rating'] <= max_rating)
                ]

            if price_category:
                filtered_data = filtered_data[filtered_data['price_category'] == price_category]

            if search_query:
                mask = filtered_data['name'].str.contains(search_query, case=False, na=False)
                filtered_data = filtered_data[mask]

            # Convert to dict and return
            return jsonify({
                'cafes': filtered_data.to_dict('records'),
                'total': len(filtered_data),
                'filters_applied': {
                    'regency': regency,
                    'type': cafe_type,
                    'rating_range': [min_rating, max_rating],
                    'price_category': price_category,
                    'search': search_query
                }
            })

        @self.app.route('/api/statistics')
        def get_statistics():
            """Get comprehensive statistics"""
            stats = {
                'total_cafes': len(self.cafe_data),
                'avg_rating': float(self.cafe_data['rating'].mean().round(2)),
                'total_reviews': int(self.cafe_data['reviews_count'].sum()),
                'regency_distribution': self.cafe_data['regency'].value_counts().to_dict(),
                'district_distribution': self.cafe_data['district'].value_counts().to_dict() if 'district' in self.cafe_data.columns else {},
                'type_distribution': self.cafe_data['type'].value_counts().to_dict(),
                'price_distribution': self.cafe_data['price_category'].value_counts().to_dict(),
                'coordinate_sources': self.cafe_data['coordinate_source'].value_counts().to_dict() if 'coordinate_source' in self.cafe_data.columns else {},
                'avg_precision_score': float(self.cafe_data['precision_score'].mean().round(3)) if 'precision_score' in self.cafe_data.columns else 0,
                'cafes_with_phone': int((self.cafe_data['phone'] != '').sum()) if 'phone' in self.cafe_data.columns else 0,
                'cafes_with_website': int((self.cafe_data['website'] != '').sum()) if 'website' in self.cafe_data.columns else 0,
                'top_rated_cafes': self.get_top_cafes('rating'),
                'most_reviewed_cafes': self.get_top_cafes('reviews_count'),
                'most_popular_cafes': self.get_top_cafes('popularity_score'),
                'rating_distribution': self.get_rating_distribution(),
                'metadata': self.metadata
            }
            return jsonify(stats)

        @self.app.route('/api/map')
        def generate_map():
            """Generate advanced interactive map"""
            map_html = self.create_advanced_map()
            return jsonify({'map_html': map_html})

        @self.app.route('/api/charts')
        def generate_charts():
            """Generate interactive charts"""
            charts = self.create_interactive_charts()
            return jsonify(charts)

        @self.app.route('/api/export/<format>')
        def export_data(format):
            """Export data in various formats"""
            if format == 'csv':
                return self.export_csv()
            elif format == 'json':
                return self.export_json()
            elif format == 'geojson':
                return self.export_geojson()
            else:
                return jsonify({'error': 'Unsupported format'}), 400

        @self.app.route('/dashboard')
        def dashboard():
            """Advanced dashboard page"""
            return render_template('advanced_dashboard.html')

        @self.app.route('/analysis')
        def analysis():
            """Advanced analysis page"""
            return render_template('advanced_analysis.html')

    def get_top_cafes(self, column, n=10):
        """Get top N cafes by specified column"""
        if column not in self.cafe_data.columns:
            return []

        # Select available columns
        available_columns = ['name', 'rating', 'reviews_count', 'regency', 'address', 'popularity_score']
        additional_columns = ['district', 'village', 'phone', 'website', 'precision_score', 'coordinate_source']

        # Add additional columns if they exist
        for col in additional_columns:
            if col in self.cafe_data.columns:
                available_columns.append(col)

        top_cafes = self.cafe_data.nlargest(n, column)[available_columns].to_dict('records')

        return top_cafes

    def get_rating_distribution(self):
        """Get rating distribution for histogram"""
        ratings = self.cafe_data['rating'][self.cafe_data['rating'] > 0]
        hist, bins = np.histogram(ratings, bins=10, range=(1, 5))

        return {
            'bins': bins.tolist(),
            'counts': hist.tolist()
        }

    def create_advanced_map(self):
        """Create advanced interactive map with clustering and heatmap"""
        # Center map on Yogyakarta
        center_lat = self.cafe_data['lat'].mean()
        center_lon = self.cafe_data['lon'].mean()

        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles=None
        )

        # Add multiple tile layers with proper attributions
        folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)
        folium.TileLayer(
            tiles='https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
            attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            name='Terrain',
            overlay=False,
            control=True
        ).add_to(m)
        folium.TileLayer(
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            name='Light',
            overlay=False,
            control=True
        ).add_to(m)

        # Create marker clusters by regency
        regencies = self.cafe_data['regency'].unique()
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred',
                 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white',
                 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']

        for i, regency in enumerate(regencies):
            if pd.isna(regency):
                continue

            regency_data = self.cafe_data[self.cafe_data['regency'] == regency]
            color = colors[i % len(colors)]

            # Create marker cluster for this regency
            marker_cluster = plugins.MarkerCluster(
                name=f'{regency} Cafes ({len(regency_data)})',
                overlay=True,
                control=True
            ).add_to(m)

            for idx, cafe in regency_data.iterrows():
                # Create popup with rich information
                popup_html = f"""
                <div style="width: 350px;">
                    <h4 style="margin: 0; color: #2c3e50;">{cafe['name']}</h4>
                    <hr style="margin: 5px 0;">

                    <div style="margin: 8px 0;">
                        <strong>📍 Location:</strong> {cafe['regency']}<br>
                        <strong>🏘️ District:</strong> {cafe.get('district', 'N/A')}<br>
                        <strong>🏡 Village:</strong> {cafe.get('village', 'N/A')}<br>
                        <strong>📧 Address:</strong> {cafe.get('address', 'N/A')[:60]}...
                    </div>

                    <div style="margin: 8px 0;">
                        <strong>⭐ Rating:</strong> {cafe['rating']}/5.0
                        ({int(cafe['reviews_count'])} reviews)<br>
                        <strong>🏷️ Type:</strong> {cafe['type']}<br>
                        <strong>💰 Price:</strong> {cafe.get('price_range', 'N/A')}
                    </div>

                    <div style="margin: 8px 0;">
                        <strong>🔥 Popularity Score:</strong> {cafe['popularity_score']}/5.0<br>
                        <strong>🕒 Hours:</strong> {cafe.get('opening_hours', 'N/A')[:40]}...
                    </div>

                    <div style="margin: 8px 0;">
                        <strong>📞 Phone:</strong> {cafe.get('phone', 'N/A')}<br>
                        <strong>🌐 Website:</strong> {cafe.get('website', 'N/A')[:40] if cafe.get('website') else 'N/A'}
                    </div>

                    <div style="margin: 8px 0; font-size: 11px; color: #7f8c8d;">
                        <strong>🎯 Precision:</strong> {cafe.get('precision_score', 'N/A')} ({cafe.get('coordinate_source', 'N/A')})<br>
                        <strong>🔍 Query:</strong> {cafe.get('search_query', 'N/A')[:40]}...<br>
                        <strong>📍 Coordinates:</strong> {cafe['lat']:.6f}, {cafe['lon']:.6f}
                    </div>
                </div>
                """

                # Icon based on rating
                if cafe['rating'] >= 4.5:
                    icon_color = 'green'
                    icon = 'star'
                elif cafe['rating'] >= 4.0:
                    icon_color = 'orange'
                    icon = 'heart'
                elif cafe['rating'] >= 3.5:
                    icon_color = 'blue'
                    icon = 'info-sign'
                else:
                    icon_color = 'red'
                    icon = 'minus-sign'

                folium.Marker(
                    location=[cafe['lat'], cafe['lon']],
                    popup=folium.Popup(popup_html, max_width=320),
                    tooltip=f"{cafe['name']} ({cafe['rating']}⭐)",
                    icon=folium.Icon(
                        color=icon_color,
                        icon=icon,
                        prefix='glyphicon'
                    )
                ).add_to(marker_cluster)

        # Add heatmap layer
        heat_data = [[row['lat'], row['lon'], row['popularity_score']]
                    for idx, row in self.cafe_data.iterrows()
                    if not pd.isna(row['lat']) and not pd.isna(row['lon'])]

        if heat_data:
            heatmap = plugins.HeatMap(
                heat_data,
                name='Popularity Heatmap',
                min_opacity=0.2,
                max_zoom=18,
                radius=25,
                blur=15,
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}
            )
            heatmap.add_to(m)

        # Add fullscreen button
        plugins.Fullscreen().add_to(m)

        # Add measure control
        plugins.MeasureControl().add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add mini map
        minimap = plugins.MiniMap(toggle_display=True)
        m.add_child(minimap)

        return m._repr_html_()

    def create_interactive_charts(self):
        """Create interactive charts using Plotly"""
        charts = {}

        # 1. Rating Distribution Histogram
        fig_rating = px.histogram(
            self.cafe_data[self.cafe_data['rating'] > 0],
            x='rating',
            nbins=20,
            title='Distribution of Cafe Ratings',
            labels={'rating': 'Rating', 'count': 'Number of Cafes'},
            color_discrete_sequence=['#3498db']
        )
        fig_rating.update_layout(
            xaxis_title="Rating (1-5 stars)",
            yaxis_title="Number of Cafes",
            showlegend=False
        )
        charts['rating_histogram'] = plotly.utils.PlotlyJSONEncoder().encode(fig_rating)

        # 2. Regency Distribution Pie Chart
        regency_counts = self.cafe_data['regency'].value_counts()
        fig_regency = px.pie(
            values=regency_counts.values,
            names=regency_counts.index,
            title='Cafe Distribution by Regency',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        charts['regency_pie'] = plotly.utils.PlotlyJSONEncoder().encode(fig_regency)

        # 3. Type vs Rating Box Plot
        fig_type_rating = px.box(
            self.cafe_data[self.cafe_data['rating'] > 0],
            x='type',
            y='rating',
            title='Rating Distribution by Cafe Type',
            color='type'
        )
        fig_type_rating.update_layout(showlegend=False)
        charts['type_rating_box'] = plotly.utils.PlotlyJSONEncoder().encode(fig_type_rating)

        # 4. Reviews vs Rating Scatter Plot
        fig_scatter = px.scatter(
            self.cafe_data[(self.cafe_data['rating'] > 0) & (self.cafe_data['reviews_count'] > 0)],
            x='reviews_count',
            y='rating',
            size='popularity_score',
            color='regency',
            hover_data=['name', 'type', 'price_range'],
            title='Reviews vs Rating (Size = Popularity Score)',
            labels={'reviews_count': 'Number of Reviews', 'rating': 'Rating'}
        )
        fig_scatter.update_layout(
            xaxis_type="log",
            xaxis_title="Number of Reviews (log scale)"
        )
        charts['reviews_rating_scatter'] = plotly.utils.PlotlyJSONEncoder().encode(fig_scatter)

        # 5. Price Category Distribution
        price_counts = self.cafe_data['price_category'].value_counts()
        fig_price = px.bar(
            x=price_counts.index,
            y=price_counts.values,
            title='Cafe Distribution by Price Category',
            labels={'x': 'Price Category', 'y': 'Number of Cafes'},
            color=price_counts.values,
            color_continuous_scale='viridis'
        )
        charts['price_bar'] = plotly.utils.PlotlyJSONEncoder().encode(fig_price)

        # 6. Top 15 Cafes by Popularity
        top_cafes = self.cafe_data.nlargest(15, 'popularity_score')
        fig_top = px.bar(
            top_cafes,
            x='popularity_score',
            y='name',
            orientation='h',
            title='Top 15 Most Popular Cafes',
            labels={'popularity_score': 'Popularity Score', 'name': 'Cafe Name'},
            color='rating',
            color_continuous_scale='RdYlGn'
        )
        fig_top.update_layout(height=600)
        charts['top_cafes_bar'] = plotly.utils.PlotlyJSONEncoder().encode(fig_top)

        # 7. District Distribution (if available)
        if 'district' in self.cafe_data.columns:
            district_counts = self.cafe_data['district'].value_counts().head(15)
            fig_district = px.bar(
                x=district_counts.index,
                y=district_counts.values,
                title='Top 15 Districts by Cafe Count',
                labels={'x': 'District', 'y': 'Number of Cafes'},
                color=district_counts.values,
                color_continuous_scale='plasma'
            )
            charts['district_bar'] = plotly.utils.PlotlyJSONEncoder().encode(fig_district)

        # 8. Precision Score Distribution (if available)
        if 'precision_score' in self.cafe_data.columns:
            precision_data = self.cafe_data[self.cafe_data['precision_score'] > 0]
            if not precision_data.empty:
                fig_precision = px.histogram(
                    precision_data,
                    x='precision_score',
                    nbins=20,
                    title='Distribution of Coordinate Precision Scores',
                    labels={'precision_score': 'Precision Score', 'count': 'Number of Cafes'},
                    color_discrete_sequence=['#e74c3c']
                )
                charts['precision_histogram'] = plotly.utils.PlotlyJSONEncoder().encode(fig_precision)

        return charts

    def export_csv(self):
        """Export data as CSV"""
        # Ensure all important columns are included
        export_columns = ['name', 'address', 'rating', 'reviews_count', 'price_range',
                         'lat', 'lon', 'district', 'village', 'regency', 'type',
                         'phone', 'website', 'opening_hours', 'popularity_score',
                         'precision_score', 'coordinate_source', 'search_query', 'scraped_at']

        # Filter to only include columns that exist in the data
        available_columns = [col for col in export_columns if col in self.cafe_data.columns]

        export_data = self.cafe_data[available_columns]
        output = io.StringIO()
        export_data.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'cafe_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    def export_json(self):
        """Export data as JSON"""
        data = {
            'metadata': self.metadata,
            'cafes': self.cafe_data.to_dict('records'),
            'export_timestamp': datetime.now().isoformat()
        }

        output = io.StringIO()
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'cafe_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

    def export_geojson(self):
        """Export data as GeoJSON"""
        features = []

        for idx, cafe in self.cafe_data.iterrows():
            if pd.isna(cafe['lat']) or pd.isna(cafe['lon']):
                continue

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(cafe['lon']), float(cafe['lat'])]
                },
                "properties": {
                    "name": cafe['name'],
                    "rating": float(cafe['rating']) if not pd.isna(cafe['rating']) else 0,
                    "reviews_count": int(cafe['reviews_count']) if not pd.isna(cafe['reviews_count']) else 0,
                    "regency": cafe['regency'],
                    "type": cafe['type'],
                    "address": cafe.get('address', ''),
                    "price_range": cafe.get('price_range', ''),
                    "popularity_score": float(cafe['popularity_score']) if not pd.isna(cafe['popularity_score']) else 0
                }
            }
            features.append(feature)

        geojson_data = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": self.metadata
        }

        output = io.StringIO()
        json.dump(geojson_data, output, indent=2)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='application/geo+json',
            as_attachment=True,
            download_name=f'cafe_geojson_{datetime.now().strftime("%Y%m%d_%H%M%S")}.geojson'
        )

    def run(self, debug=True, host='0.0.0.0', port=5004):
        """Run the advanced SIG application"""
        print(f"\n🚀 Advanced SIG Cafe Jogja Application")
        print(f"📊 Dataset: {len(self.cafe_data)} cafes loaded")
        print(f"🌐 Access: http://{host}:{port}")
        print(f"📍 Coverage: {', '.join(self.cafe_data['regency'].unique())}")
        print(f"⭐ Avg Rating: {self.cafe_data['rating'].mean():.2f}")
        print("=" * 50)

        self.app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    app = AdvancedSIGApp()
    app.run()
