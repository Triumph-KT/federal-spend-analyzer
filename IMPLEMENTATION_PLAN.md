# Implementation Plan & Project Retrospective

## 1. Project Overview

The objective of this project was to build a full-stack application to identify top federal contractors from FY2023 and analyze which of them experienced a significant drop in U.S. government revenue in FY2024. The application required a React front-end for user interaction and a back-end to handle the logic of fetching and processing data from the external [USAspending.gov API](https://api.usaspending.gov/).

This document outlines the architecture, implementation details, and the key technical challenges discovered and overcome during development.

---

## 2. System Architecture

The application follows a standard client-server architecture, cleanly separating the front-end presentation layer from the back-end business logic.

### High-Level Diagram

```text
+-----------------+      HTTP Request (JSON)      +----------------------+      Multiple API Calls (JSON)      +--------------------+
|                 |-----------------------------> |                      | ----------------------------------->|                    |
|   React Client  |      (e.g., topN: 100,       |   Django Backend     |      (Paginated, Cached)            |   USAspending.gov  |
| (localhost:300x)|      declinePct: 25)         |   (localhost:8000)   |                                      |        API         |
|                 |<-----------------------------|                      | <-----------------------------------|                    |
+-----------------+      HTTP Response (JSON)    +----------------------+      API Responses (JSON)           +--------------------+
````

### Component Breakdown

* **Frontend (React):**
  A single-page application responsible for all user interaction. It captures user input, sends analysis requests to the backend, and renders the results in a user-friendly, interactive table. It does not contain any business logic related to the USAspending API.

* **Backend (Django):**
  A stateless API that exposes a single endpoint. Its sole responsibility is to receive requests from the client, orchestrate the complex process of fetching and processing data from the external USAspending API, and return the final, calculated insights as a JSON response.

---

## 3. Implementation Details

### Backend (Django)

The backend was designed to be robust, performant, and scalable.

#### Core Logic & Data Flow

The primary challenge was fetching and comparing data for two separate fiscal years. The final, successful implementation follows a **two-call strategy to a single, verified endpoint**:

1. **Fetch FY2023 Data:**
   A single API call is made to get the top `N` recipients for FY2023.

2. **Fetch FY2024 Data:**
   To build a comprehensive dataset for comparison, the backend makes multiple, **paginated** API calls to the same endpoint for FY2024. This respects the API's rate limits while still gathering sufficient data.

3. **Process Data:**
   The two datasets are combined in memory to perform the final analysis.

#### Data Structures

To efficiently combine the two lists of data, a **Python dictionary (hash map)** was used.

* **`fy2024_map`:**
  After fetching the large list of 2024 data, it is transformed into a dictionary where the `key` is the company's DUNS number and the `value` is their total revenue for that year.

* **Benefit:**
  This allows for O(1) average-time complexity lookups. When iterating through the top 2023 companies, we can find their corresponding 2024 revenue almost instantly from this map, which is significantly more efficient than searching through a list repeatedly.

#### Performance Optimization: Caching

* **Problem:**
  The initial data fetch is slow due to the multiple, paginated calls to the external API.

* **Solution:**
  Django's built-in caching framework was implemented.

* **Mechanism:**

  * **Cache Backend:** `django.core.cache.backends.locmem.LocMemCache` (in-memory cache) was used for simplicity and speed. For a production environment with multiple server instances, a distributed cache like Redis would be the next step.
  * **Cache Key:** A unique key is generated for each query based on the user's input (e.g., `analysis_100_25`).
  * **Workflow:** When a request is received, the backend first checks the cache for this key. If the data exists, it is returned immediately. If not, the backend performs the slow API calls, and before returning the results, it stores them in the cache with a timeout of one hour.

#### API Interaction & Pagination

* **Discovery:**
  Through direct `curl` testing, a critical, undocumented API limitation was discovered: the `/spending_by_category/` endpoint has a maximum `limit` of 100 records per request.

* **Solution:**
  A dedicated `fetch_paginated_list` function was created. This function makes API calls in a loop, using the `page` parameter to request subsequent chunks of 100 records until the desired amount of data is collected or the API has no more results to return. This is a robust pattern for handling any API with rate limits.

### Frontend (React)

The frontend was built with a focus on user experience and maintainability.

* **State Management:**
  React's built-in `useState` hook was used to manage all component state, including form inputs, API results, loading indicators, error messages, and the current table sort configuration.

* **Sorting Logic:**
  To efficiently sort the results table without re-fetching data, the `useMemo` hook was used. This creates a memoized selector that only re-calculates the sorted array when the original `results` data or the `sortConfig` state changes, preventing unnecessary re-renders.

* **External Linking:**
  To provide value beyond the core requirement, each DUNS number is rendered as a hyperlink (`<a>` tag) that opens a new tab to the official recipient page on `usaspending.gov`, allowing for easy verification and further research.

---

## 4. Testing Plan

A multi-layered testing approach was used to ensure correctness and reliability.

* **API Verification:**
  `curl` was used extensively to directly test the external API, which proved crucial in diagnosing endpoint URLs, required request payloads, and undocumented rate limits.

* **Local Development Testing:**
  The application was tested end-to-end throughout development by running the Django and React servers concurrently.

* **Manual Test Cases Executed:**

  * **Happy Path:** Verified that entering standard values (e.g., Top 100, 25% decline) and clicking "Analyze" returns a correctly formatted table of results.
  * **Caching:** Verified that the first request is slow, and subsequent identical requests are instantaneous.
  * **Sorting:** Clicked each sortable table header to verify ascending and descending sort functionality.
  * **External Links:** Clicked multiple DUNS links to ensure they directed to the correct external URLs.
  * **Edge Cases:**

    * Tested with `topN=0` and `declinePct=0`.
    * Verified that an error message is shown if `topN` is greater than 100.
    * Verified that a "No companies found" message appears for criteria that yield no results.
  * **Error Handling:** Manually stopped the Django server to verify that the frontend displays the "Could not connect to the backend" error message.

---

## 5. Final Step: Commit and Push

Now, commit this new documentation file to your repository.

In your terminal, from the `federal-spend-analyzer` directory, run:

```bash
# Stage the new implementation plan file
git add IMPLEMENTATION_PLAN.md

# Also add the updated README.md
git add README.md

# Commit the new documentation
git commit -m "docs: Add detailed implementation plan and final README"

# Push the final commit to GitHub
git push origin main
```
