import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  // State for the form inputs
  const [topN, setTopN] = useState(100);
  const [declinePct, setDeclinePct] = useState(25);

  // State for the API response and status
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  /**
   * Handles the form submission.
   * It sends a POST request to the Django backend API.
   */
  const handleAnalyzeClick = async () => {
    // Reset previous results and errors
    setIsLoading(true);
    setError('');
    setResults([]);

    try {
      // The URL of our Django API endpoint
      const apiUrl = 'http://127.0.0.1:8000/api/analyze/';
      const payload = { topN, declinePct };

      const response = await axios.post(apiUrl, payload);

      // Check if the response has data and update the state
      if (response.data && response.data.length > 0) {
        setResults(response.data);
      } else {
        setError('No companies found matching the criteria.');
      }
    } catch (err) {
      // Handle different types of errors
      if (err.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        const serverError = err.response.data.error || 'An unknown server error occurred.';
        setError(`Error from server: ${serverError}`);
      } else if (err.request) {
        // The request was made but no response was received
        setError('Could not connect to the backend server. Is it running?');
      } else {
        // Something happened in setting up the request that triggered an Error
        setError(`An error occurred: ${err.message}`);
      }
    } finally {
      // Ensure loading is set to false after the request is complete
      setIsLoading(false);
    }
  };

  /**
   * Helper function to format large numbers as currency.
   */
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Federal Spend Decline Dashboard</h1>
        <p>
          Find top federal contractors from FY2023 that saw a significant revenue drop in FY2024.
        </p>
      </header>

      <main className="App-main">
        <div className="controls-container">
          <p>
            Search the top
            <input
              type="number"
              value={topN}
              onChange={(e) => setTopN(e.target.value)}
              className="control-input"
              aria-label="Top N companies"
            />
            companies that saw their revenue from the U.S. government decline by more than
            <input
              type="number"
              value={declinePct}
              onChange={(e) => setDeclinePct(e.target.value)}
              className="control-input"
              aria-label="Decline percentage"
            />
            %
          </p>
          <button onClick={handleAnalyzeClick} disabled={isLoading}>
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {isLoading && <div className="loading-spinner"></div>}

        {results.length > 0 && (
          <div className="results-container">
            <h2>Analysis Results</h2>
            <table className="results-table">
              <thead>
                <tr>
                  <th>Company Name</th>
                  <th>DUNS</th>
                  <th>2023 Revenue</th>
                  <th>2024 Revenue</th>
                  <th>Decline</th>
                </tr>
              </thead>
              <tbody>
                {results.map((company) => (
                  <tr key={company.duns}>
                    <td>{company.name}</td>
                    <td>{company.duns}</td>
                    <td>{formatCurrency(company.revenue2023)}</td>
                    <td>{formatCurrency(company.revenue2024)}</td>
                    <td>
                      <span className="decline-percentage">
                        {company.declinePercentage}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
