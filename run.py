"""
run.py — SysMon API entry point
Usage:
    python run.py             # development server
    flask run                 # alternative
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("  SysMon API  —  System Metrics Service")
    print("  http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
