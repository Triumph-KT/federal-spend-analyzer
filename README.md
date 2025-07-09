Federal Spend Decline DashboardThis project is a full-stack web application designed to analyze U.S. federal spending data. It identifies the top N companies by federal revenue in fiscal year 2023 and then filters them to show which ones experienced a revenue decline greater than a specified percentage in fiscal year 2024.The application is built with a React front-end and a Django (Python) back-end, demonstrating a common pattern of consuming and processing data from a third-party API to surface actionable insights to a user.Project StructureThe repository is organized into two main directories:/frontend: Contains the React application for the user interface./backend: Contains the Django REST Framework API that handles the business logic and communication with the USAspending.gov API.PrerequisitesBefore you begin, ensure you have the following installed on your system:Node.js (v18 or later): Download Node.jsPython (v3.9 or later): Download Pythonpip (Python package installer)How to Run the Application LocallyTo run this application, you will need to start both the back-end server and the front-end development server in separate terminal windows.1. Back-end Setup (Django)First, set up and run the Django server.# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# On Windows, use:
# venv\Scripts\activate

# 3. Install the required Python packages
pip install -r requirements.txt

# 4. Run the Django development server
python manage.py runserver
The Django API will now be running at http://127.0.0.1:8000. Keep this terminal window open.2. Front-end Setup (React)In a new terminal window, set up and run the React application.# 1. Navigate to the frontend directory
cd frontend

# 2. Install the required Node.js packages
npm install

# 3. Start the React development server
npm start
The React application will automatically open in your default web browser at http://localhost:3000.You can now use the application to analyze federal spending data.API EndpointThe back-end exposes the following endpoint for the front-end to consume:POST /api/analyze/Description: Accepts topN and declinePct values, fetches data from the USAspending.gov API, processes it, and returns the list of companies that meet the decline criteria.Request Body:{
  "topN": 100,
  "declinePct": 25
}
Successful Response (200 OK):[
  {
    "duns": "012345678",
    "name": "Example Corporation",
    "revenue2023": 150000000.50,
    "revenue2024": 100000000.25,
    "declinePercentage": -33.33
  }
]
