import React, { useState, useMemo } from 'react';
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

  // --- NEW: State for managing table sorting ---
  const [sortConfig, setSortConfig] = useState({ key: 'declinePercentage', direction: 'ascending' });

  /**
   * This memoized value recalculates the sorted results only when
   * the original results or the sort configuration changes.
   */
  const sortedResults = useMemo(() => {
    let sortableItems = [...results];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [results, sortConfig]);

  /**
   * Function to request a new sort configuration.
   * Called when a table header is clicked.
   */
  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  /**
   * Handles the form submission.
   */
  const handleAnalyzeClick = async () => {
    setIsLoading(true);
    setError('');
    setResults([]);

    try {
      const apiUrl = 'http://127.0.0.1:8000/api/analyze/';
      const payload = { topN, declinePct };
      const response = await axios.post(apiUrl, payload);

      if (response.data && response.data.length > 0) {
        setResults(response.data);
        // Default sort by decline percentage after fetching
        setSortConfig({ key: 'declinePercentage', direction: 'ascending' });
      } else {
        setError('No companies found matching the criteria.');
      }
    } catch (err) {
      if (err.response) {
        const serverError = err.response.data.error || 'An unknown server error occurred.';
        setError(`Error from server: ${serverError}`);
      } else if (err.request) {
        setError('Could not connect to the backend server. Is it running?');
      } else {
        setError(`An error occurred: ${err.message}`);
      }
    } finally {
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
  
  /**
   * Helper to get the sort indicator arrow for table headers.
   */
  const getSortIndicator = (name) => {
    if (sortConfig.key === name) {
      return sortConfig.direction === 'ascending' ? ' ▲' : ' ▼';
    }
    return null;
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

        {/* Use sortedResults instead of results */}
        {sortedResults.length > 0 && (
          <div className="results-container">
            <h2>Analysis Results</h2>
            <table className="results-table">
              <thead>
                <tr>
                  <th onClick={() => requestSort('name')} className="sortable-header">
                    Company Name{getSortIndicator('name')}
                  </th>
                  <th>DUNS</th>
                  <th onClick={() => requestSort('revenue2023')} className="sortable-header">
                    2023 Revenue{getSortIndicator('revenue2023')}
                  </th>
                  <th onClick={() => requestSort('revenue2024')} className="sortable-header">
                    2024 Revenue{getSortIndicator('revenue2024')}
                  </th>
                  <th onClick={() => requestSort('declinePercentage')} className="sortable-header">
                    Decline{getSortIndicator('declinePercentage')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedResults.map((company) => (
                  <tr key={company.duns}>
                    <td>{company.name}</td>
                    <td>
                      {/* --- START OF CHANGE --- */}
                      <a 
                        href={`https://www.usaspending.gov/recipient/${company.recipient_id}/latest`} 
                        target="_blank" 
                        rel="noopener noreferrer"
                      >
                        {company.duns}
                      </a>
                      {/* --- END OF CHANGE --- */}
                    </td>
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