from flask import Flask, request, jsonify
import asyncio
import re
from autosh import process_card, fetchProducts
from utils import Utils

app = Flask(__name__)

# Proxy class to match the format used in autosh.py
class Proxy:
    def __init__(self, proxy_string):
        # Expected format: user:pass@ip:port
        if '@' in proxy_string:
            auth, server = proxy_string.split('@', 1)
            self.proxy = proxy_string
        else:
            # If no auth, just use the server part
            self.proxy = proxy_string

# Site class to match the format used in autosh.py
class Site:
    def __init__(self, url, variant_id=None):
        self.url = url
        self.variant_id = variant_id

@app.route('/autosh/site=<site>')
def process_card_endpoint(site):
    try:
        # Get card information from query parameters
        cc = request.args.get('cc')
        
        if not cc:
            return jsonify({"error": "Card information is required"}), 400
        
        # Extract card details from pipe format
        card_parts = cc.split('|')
        if len(card_parts) != 4:
            return jsonify({"error": "Invalid card format. Expected format: card_number|month|year|cvv"}), 400
        
        card_number, month, year, cvv = card_parts
        
        # Validate card information
        if not Utils.luhn_check(card_number):
            return jsonify({"error": "Invalid card number"}), 400
        
        if not month.isdigit() or int(month) < 1 or int(month) > 12:
            return jsonify({"error": "Invalid month"}), 400
            
        if not year.isdigit() or len(year) not in [2, 4]:
            return jsonify({"error": "Invalid year"}), 400
            
        if not cvv.isdigit() or len(cvv) not in [3, 4]:
            return jsonify({"error": "Invalid CVV"}), 400
        
        # Process the card
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Hardcoded proxy
        proxy_string = "http://user-Mdw5TwO58ewqByFP-type-residential-country-US-city-New_York:9GFLalL6ZKPZraFe@geo.g-w.info:10080"
        proxy = Proxy(proxy_string)
        proxies = [proxy]
        
        # Check if site has variant_id
        site_parts = site.split('?')
        site_url = site_parts[0]
        variant_id = None
        
        if len(site_parts) > 1:
            variant_match = re.search(r'variant_id=([^&]+)', site_parts[1])
            if variant_match:
                variant_id = variant_match.group(1)
        
        # Create site object
        site_obj = Site(site_url, variant_id)
        
        # Process the card
        result = loop.run_until_complete(process_card(card_number, month, year, cvv, site_obj, proxies))
        
        # Return the result
        if isinstance(result, tuple) and len(result) >= 2:
            if result[0]:
                return jsonify({
                    "status": "success",
                    "message": result[1],
                    "details": result[2:] if len(result) > 2 else None
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": result[1],
                    "details": result[2:] if len(result) > 2 else None
                }), 400
        else:
            return jsonify({
                "status": "error",
                "message": "Unknown error occurred"
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Load resources
    Utils.load_resources()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
