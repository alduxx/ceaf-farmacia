# wsgi.py
from src.app import app, initialize_data

# Initialize data when imported by gunicorn
initialize_data()

if __name__ == "__main__":
  app.run()