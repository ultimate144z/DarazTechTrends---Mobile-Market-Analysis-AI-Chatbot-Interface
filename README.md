# DarazTechTrends: Mobile Market Analysis & AI Chatbot Interface

## Description
DarazTechTrends is an interactive system that combines advanced web scraping with an intelligent chatbot to analyze and present mobile market data from daraz.pk. This project allows users to explore mobile product trends and receive personalized recommendations through a conversational interface.

## Features
- Data extraction from daraz.pk for mobile products
- An AI-powered chatbot for handling user inquiries
- A dynamic dashboard for visual data representation
- Flask-based server for a responsive user experience

## Getting Started

### Prerequisites
- Python 3.x
- Pip (Python package installer)
- Virtualenv (optional for creating a virtual environment)

### Installation
1. Clone the repository:

2. Navigate to the project directory:
   - cd DarazTechTrends

4. (Optional) Create and activate a virtual environment:
   - virtualenv venv
   - source venv/bin/activate # On Windows use venv\Scripts\activate

5. Install the required packages:
   - pip install -r requirements.txt

- Update the `server.py` file with your database connection details.

### Running the Project
- To start the web scraper, run:
- python scraping/scraper.py

- To start the chatbot and dashboard server, run:
- python bot/server.py
  
## Usage
- Access the dashboard by navigating to `http://localhost:5000` in your web browser.
- Interact with the chatbot through the provided interface.
