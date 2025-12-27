import requests
import time
from .config import HEADERS

class APIClient:
    @staticmethod
    def post(url, data=None, json=None, wait_for_model=True):
        """Generic POST request with error handling and optional model waiting."""
        payload_kwargs = {}
        if data: payload_kwargs['data'] = data
        if json: payload_kwargs['json'] = json
        
        # Add wait_for_model option if using JSON payload (common for text gen)
        if json and wait_for_model and 'options' not in json:
             # Ensure headers are correct for JSON
             pass # requests handles content-type for json param

        try:
            response = requests.post(url, headers=HEADERS, **payload_kwargs)
            
            # Handle model loading state (503)
            if response.status_code == 503:
                estimated_time = response.json().get("estimated_time", 20)
                time.sleep(estimated_time)
                # Retry once
                response = requests.post(url, headers=HEADERS, **payload_kwargs)

            if response.status_code != 200:
                raise Exception(f"API Error {response.status_code}: {response.text}")
                
            return response.json()
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
