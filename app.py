import os
import subprocess
import json
from flask import Flask, request, jsonify, Response

# Initialize the Flask application
app = Flask(__name__)

@app.route('/api/checkout', methods=['GET'])
def run_checkout():
    """
    API endpoint to run the Shopify checkout PHP script.
    Expects 'site' and 'cc' as query parameters.
    """
    # 1. Get query parameters from the request URL
    site = request.args.get('site')
    cc = request.args.get('cc')

    # 2. Validate that both parameters are provided
    if not site or not cc:
        return jsonify({
            "Response": "Error: 'site' and 'cc' query parameters are required."
        }), 400

    # 3. Construct the command to execute the PHP script
    # We pass 'site' and 'cc' as command-line arguments
    command = ['php', 'index.php', site, cc]

    try:
        # 4. Run the command as a subprocess
        # - capture_output=True: Captures stdout and stderr
        # - text=True: Decodes stdout/stderr as text
        # - check=True: Raises an exception if the script returns a non-zero exit code (an error)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=60 # Add a 60-second timeout
        )

        # 5. The PHP script outputs a JSON string, so we try to parse it
        # If it fails, we return the raw text output.
        try:
            # The PHP script's output is in result.stdout
            json_output = json.loads(result.stdout)
            return jsonify(json_output)
        except json.JSONDecodeError:
            # If the output isn't valid JSON (e.g., a PHP warning was printed)
            # return the raw text with a 500 status code.
            return Response(result.stdout, status=500, mimetype='text/plain')

    except subprocess.CalledProcessError as e:
        # This block runs if the PHP script exited with an error
        return jsonify({
            "Response": "PHP script execution failed.",
            "error": e.stderr  # The error message from the PHP script
        }), 500
    except subprocess.TimeoutExpired:
        # This block runs if the script takes too long
        return jsonify({
            "Response": "Error: Script execution timed out after 60 seconds."
        }), 504 # Gateway Timeout
    except Exception as e:
        # Catch any other unexpected errors
        return jsonify({
            "Response": "An unexpected server error occurred.",
            "error": str(e)
        }), 500

# This allows running the server locally for testing
if __name__ == '__main__':
    # Render will use a production server like Gunicorn; this is for local dev
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
