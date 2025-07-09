import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from django.core.cache import cache # Import Django's cache

# The single, correct endpoint that you discovered and verified.
USA_SPENDING_API_URL = "https://api.usaspending.gov/api/v2/search/spending_by_category/recipient_duns/"

class AnalyzeSpendView(APIView):
    """
    This view handles the analysis of federal spending data using a corrected,
    paginated strategy to respect the API's rate limits.
    
    This version now includes caching to improve performance on repeated requests.
    """

    def post(self, request, *args, **kwargs):
        top_n_str = request.data.get('topN')
        decline_pct_str = request.data.get('declinePct')

        try:
            top_n = int(top_n_str)
            decline_pct = float(decline_pct_str)
            if top_n > 100:
                return Response({"error": "Please enter a value of 100 or less for 'Top N companies'."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"error": "Invalid input."}, status=status.HTTP_400_BAD_REQUEST)

        # --- CACHING LOGIC START ---
        # Create a unique key for this specific search combination.
        cache_key = f"analysis_{top_n}_{decline_pct}"
        
        # Check if the results are already in the cache.
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            # If found, return the cached data immediately.
            return Response(cached_results)
        # --- CACHING LOGIC END ---

        try:
            # If not in cache, proceed with the slow API calls.
            fy2023_data = self.fetch_ranked_list(2023, top_n)
            if not fy2023_data:
                return Response([])
            
            fy2024_data = self.fetch_paginated_list(2024, num_pages=50)
            results = self.process_and_filter_data(fy2023_data, fy2024_data, decline_pct)

            # --- CACHING LOGIC START ---
            # Save the new results to the cache for 1 hour (3600 seconds).
            cache.set(cache_key, results, timeout=3600)
            # --- CACHING LOGIC END ---

            return Response(results)

        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if e.response:
                try:
                    error_message = e.response.json()
                except json.JSONDecodeError:
                    error_message = e.response.text
            return Response(
                {"error": f"Failed to connect to USAspending API: {error_message}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def fetch_ranked_list(self, fiscal_year, limit):
        headers = {'Content-Type': 'application/json'}
        payload = {
            "filters": {
                "time_period": [{"start_date": f"{fiscal_year - 1}-10-01", "end_date": f"{fiscal_year}-09-30"}]
            },
            "limit": limit,
            "page": 1
        }
        response = requests.post(USA_SPENDING_API_URL, json=payload, headers=headers, timeout=60.0)
        response.raise_for_status()
        all_results = response.json().get('results', [])
        return [d for d in all_results if d.get('code')]

    def fetch_paginated_list(self, fiscal_year, num_pages):
        all_fy_data = []
        for page_num in range(1, num_pages + 1):
            headers = {'Content-Type': 'application/json'}
            payload = {
                "filters": {
                    "time_period": [{"start_date": f"{fiscal_year - 1}-10-01", "end_date": f"{fiscal_year}-09-30"}]
                },
                "limit": 100,
                "page": page_num
            }
            response = requests.post(USA_SPENDING_API_URL, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            page_results = response.json().get('results', [])
            if not page_results:
                break
            all_fy_data.extend(page_results)
        return [d for d in all_fy_data if d.get('code')]

    def process_and_filter_data(self, fy2023_data, fy2024_data, decline_pct):
        fy2024_map = {item['code']: float(item['amount']) for item in fy2024_data}
        final_results = []
        for company2023 in fy2023_data:
            duns = company2023['code']
            revenue2023 = float(company2023['amount'])
            revenue2024 = fy2024_map.get(duns, 0.0)
            if revenue2023 <= 0:
                continue
            percentage_change = ((revenue2024 - revenue2023) / revenue2023) * 100
            if percentage_change < -decline_pct:
                final_results.append({
                    "duns": duns,
                    "name": company2023['name'],
                    "revenue2023": revenue2023,
                    "revenue2024": revenue2024,
                    "declinePercentage": round(percentage_change, 2)
                })
        return final_results