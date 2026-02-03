import sys
import os

# Add your application directory to the Python path
# Update this path when deploying to your server
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

# Import the Flask app from check_sites.py
from check_sites import app

# This is what Gunicorn will use
if __name__ == "__main__":
    app.run()
