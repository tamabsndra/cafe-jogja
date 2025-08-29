from typing import List, Dict

def _generate_search_strategies() -> List[Dict]:
        """Generate super comprehensive & diversified search strategies for all coffee-related places in Yogyakarta"""

        # Base keywords & synonyms
        base_keywords = [
            "cafe", "coffee shop", "kedai kopi", "warung kopi", "tempat ngopi",
            "kopi kekinian", "kopi tradisional", "espresso bar", "roastery",
            "coffee house", "ngopi place", "kopi enak", "coffee corner", "specialty coffee",
            "specialty coffee", "cafe perak", "specialty coffee roastery", "kopi luwak", "kopi premium"
        ]

        # Context & popular attributes
        contexts = [
            "","viral", "skena", "kalcer", "hits", "murah", "instagrammable", "cozy", "buat nugas",
            "buka 24 jam", "late night", "live music", "view bagus",
            "sunset spot", "terdekat", "recommended", "best", "paling rame",
        ]

        # Kabupaten/Kota-level (DIY regions)
        regions = [
            "yogyakarta", "sleman", "bantul", "kulon progo", "gunungkidul", "kota jogja", "DIY"
        ]

        # Kecamatan/sub-area populer (lebih komplit dari sebelumnya)
        sub_areas = [
            # Sleman & sekitar UGM
            "malioboro", "condongcatur", "depok", "caturtunggal", "seturan",
            "gejayan", "pogung", "kentungan", "babarsari", "kalasan", "ngaglik",
            "mlati", "gamping", "godean", "berbah", "prambanan", "cangkringan",
            "pakem", "turi", "tempel", "seyegan", "minggir", "moyudan",
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
            "tugu jogja", "keraton yogyakarta", "taman sari", "alun alun kidul",
            "alun alun utara", "ambarukmo plaza", "hartono mall", "jogja city mall",
            "prambanan temple", "ratu boko", "parangtritis beach", "bukit bintang",
            "kaliurang", "merapi museum", "heha sky view", "tebing breksi",
            "pinus pengger", "mangunan", "sindu kusuma edupark",
            "gembira loka zoo", "xt square", "monjali", "yogyakarta international airport",
            "goa pindul", "waduk sermo", "ugm", "uii", "upn"
        ]

        all_queries = set()

        # Kombinasi base keywords dengan konteks & wilayah besar
        for kw in base_keywords:
            for ctx in contexts:
                for reg in regions:
                    query = f"{kw} {ctx} {reg}".strip()
                    all_queries.add(query)

        # Tambahin kombinasi dengan sub-area
        for kw in base_keywords:
            for ctx in contexts:
                for area in sub_areas:
                    query = f"{kw} {ctx} {area}".strip()
                    all_queries.add(query)

        # Tambahin kombinasi dengan landmark
        for kw in base_keywords:
            for ctx in contexts:
                for lm in landmarks:
                    query = f"{kw} {ctx} dekat {lm}".strip()
                    all_queries.add(query)

        strategies = []

        for q in sorted(all_queries):
            words = q.split()


            # Categorize queries by effectiveness
            if any(landmark in q.lower() for landmark in landmarks):
                strategies.append({
                    'query': q,
                    'expected_results': 100,
                    'priority': 0
                })
            elif any(area in q.lower() for area in sub_areas):
                strategies.append({
                    'query': q,
                    'expected_results': 80,
                    'priority': 1
                })
            elif 'dekat' not in q.lower() and len(words) <= 10:  # Simple, general queries
                strategies.append({
                    'query': q,
                    'expected_results': 60,
                    'priority': 1
                })
            elif 'dekat' in q.lower() and len(words) <= 10:  # Simple "near" queries
                strategies.append({
                    'query': q,
                    'expected_results': 40,
                    'priority': 2
                })

        # Sort by priority then by expected results
        strategies.sort(key=lambda x: (x['priority'], -x['expected_results']))

        return strategies


if __name__ == "__main__":
    strategy = _generate_search_strategies()
    print(len(strategy))
