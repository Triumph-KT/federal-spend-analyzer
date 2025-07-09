# Federal Spend Decline Dashboard

This project is a full-stack web application designed to analyze U.S. federal spending data. It identifies the top N companies by federal revenue in fiscal year 2023 and then filters them to show which ones experienced a revenue decline greater than a user-specified percentage in fiscal year 2024.

The application is built with a **React front-end** and a **Django (Python) back-end**. It demonstrates a complete, production-ready workflow: consuming and processing data from a complex external API, handling performance bottlenecks with caching, and presenting the final insights in a responsive and interactive user interface.

## Core Features

  * **Variable Analysis:** Users can dynamically set the number of top companies and the revenue decline threshold to analyze.
  * **High-Performance Backend:** The first API query is cached for one hour, making subsequent identical analyses instantaneous.
  * **Robust API Interaction:** The backend uses a paginated approach to reliably fetch large datasets from the external API while respecting its rate limits.
  * **Interactive UI:** The results table is sortable by company name, revenue, or decline percentage.
  * **Direct Data Linking:** Each company's DUNS number links directly to its official profile on USAspending.gov for further verification and research.

-----

## Technical Stack

  * **Backend:** Python 3, Django, Django Rest Framework
  * **Frontend:** React, Axios
  * **Development:** Git for version control

-----

## How to Run the Application Locally

To run this application, you will need to start both the back-end server and the front-end development server in separate terminal windows.

### **Prerequisites**

  * Node.js (v18 or later)
  * Python (v3.9 or later) & pip

### **1. Backend Setup (Django)**

First, set up and run the Django server.

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# On Windows, use: venv\Scripts\activate

# 3. Install the required Python packages
pip install -r requirements.txt

# 4. Run the Django development server
python manage.py runserver
```

The Django API will now be running at `http://127.0.0.1:8000`. Keep this terminal window open.

### **2. Frontend Setup (React)**

In a **new terminal window**, set up and run the React application.

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install the required Node.js packages
npm install

# 3. Start the React development server
npm start
```

The React application will automatically open in your default web browser (e.g., at `http://localhost:3000`). If that port is busy, it will choose another, which the backend is configured to allow.

-----

## Implementation Notes & API Discoveries

A key part of this project was successfully integrating with the `USAspending.gov` v2 API, which was an unfamiliar data source. The process involved significant debugging and discovery.

### **Challenge: Diagnosing API Errors**

Initial attempts to fetch data were met with `422 Unprocessable Entity` errors from the server. This error code indicated that while our request URL was correct, the data payload was invalid.

### **Discovery: Undocumented Rate Limits**

Through methodical testing using `curl` commands, I was able to diagnose the root cause: the API has an unwritten server-side rule that prevents requests for more than **100 records** at a time. Any request with a `"limit"` greater than 100 was rejected.

### **Solution: A Paginated, Two-Call Strategy**

The final, robust solution does not try to fetch all data in a single, large request. Instead, it respects the API's limits by implementing the following strategy:

1.  **Fetch Top Companies (FY 2023):** A single API call is made to the `/api/v2/search/spending_by_category/recipient_duns/` endpoint to get the top `N` companies (where `N` is less than or equal to 100).
2.  **Fetch Full Data Set (FY 2024):** To build a lookup table for 2024 revenues, the application makes multiple, paginated calls to the same endpoint in a loop, requesting 100 records at a time until a sufficient dataset is built.
3.  **Data Combination:** The two datasets are then combined in Python to perform the final analysis.

This approach ensures reliability and avoids overwhelming the external API, demonstrating a best-practice for consuming third-party data services.