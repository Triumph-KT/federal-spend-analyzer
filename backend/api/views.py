from django.shortcuts import render

# Create your views here.
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# The base URL for the USAspending API v2.
USA_SPENDING_API_URL = "https://api.usaspending.gov/api/v2/search/spending_by_recipient/"

class AnalyzeSpendView(APIView):
    """
    This view handles the analysis of federal spending data.
    It receives a POST request with 'topN' and 'declinePct',
    fetches data from the USAspending API for FY2023 and FY2024,
    calculates the percentage change in revenue for the top N companies,
    and returns the companies that saw a decline greater than the specified percentage.
    """

    def post(self, request, *args, **kwargs):
        # 1. Extract and validate input from the request payload.
        top_n_str = request.data.get('topN')
        decline_pct_str = request.data.get('declinePct')

        if not top_n_str or not decline_pct_str:
            return Response(
                {"error": "Both 'topN' and 'declinePct' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            top_n = int(top_n_str)
            decline_pct = float(decline_pct_str)
            if top_n <= 0 or decline_pct < 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid input. 'topN' must be a positive integer and 'declinePct' must be a non-negative number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Fetch Top N companies for Fiscal Year 2023.
        try:
            fy2023_data = self.fetch_spending_data(2023, top_n)
            if not fy2023_data:
                return Response({"results": []}) # Return empty if no data for 2023

            # Extract the recipient IDs (DUNS numbers) for the next query.
            recipient_ids = [item['recipient_duns'] for item in fy2023_data]

            # 3. Fetch spending data for those same companies for Fiscal Year 2024.
            fy2024_data = self.fetch_spending_data(2024, None, recipient_ids)

            # 4. Process and combine the data.
            results = self.process_and_filter_data(fy2023_data, fy2024_data, decline_pct)

            return Response(results)

        except requests.exceptions.RequestException as e:
            # Handle potential network errors or issues with the external API.
            return Response(
                {"error": f"Failed to connect to USAspending API: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            # Catch any other unexpected errors during processing.
            return Response(
                {"error": f"An unexpected error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def fetch_spending_data(self, fiscal_year, limit=None, recipient_ids=None):
        """
        Helper function to fetch data from the USAspending API for a given fiscal year.
        """
        payload = {
            "filters": {
                "time_period": [
                    {"start_date": f"{fiscal_year - 1}-10-01", "end_date": f"{fiscal_year}-09-30"}
                ],
                "recipient_type": "business"
            },
            "fields": ["recipient_name", "recipient_duns", "obligated_amount"],
            "sort": "obligated_amount",
            "order": "desc"
        }

        # If a limit is provided (for the top N query), add it to the payload.
        if limit:
            payload['limit'] = limit
        
        # If recipient IDs are provided, add them to the filter.
        if recipient_ids:
            payload['filters']['recipient_duns'] = recipient_ids
            # We don't need to sort or limit when fetching by specific IDs.
            payload.pop('sort', None)
            payload.pop('order', None)


        response = requests.post(USA_SPENDING_API_URL, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json().get('results', [])


    def process_and_filter_data(self, fy2023_data, fy2024_data, decline_pct):
        """
        Combines 2023 and 2024 data, calculates decline, and filters the results.
        """
        # Create a dictionary for FY2024 data for quick lookups.
        fy2024_map = {item['recipient_duns']: float(item['obligated_amount']) for item in fy2024_data}

        final_results = []
        for company2023 in fy2023_data:
            duns = company2023['recipient_duns']
            revenue2023 = float(company2023['obligated_amount'])
            
            # Get 2024 revenue for the company, defaulting to 0 if not found.
            revenue2024 = fy2024_map.get(duns, 0.0)

            # Avoid division by zero if 2023 revenue was 0 or negative.
            if revenue2023 <= 0:
                continue

            # Calculate the percentage change.
            percentage_change = ((revenue2024 - revenue2023) / revenue2023) * 100

            # Check if the decline is greater than the user-specified threshold.
            # A decline is a negative change, so we check if it's less than -decline_pct.
            if percentage_change < -decline_pct:
                final_results.append({
                    "duns": duns,
                    "name": company2023['recipient_name'],
                    "revenue2023": revenue2023,
                    "revenue2024": revenue2024,
                    "declinePercentage": round(percentage_change, 2)
                })
        
        return final_results

