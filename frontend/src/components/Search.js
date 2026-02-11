import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { searchBooks, getErrorMessage } from '../services/api';
import './Search.css';

function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setSearched(false);

    try {
      const response = await searchBooks(query.trim());
      setResults(response.data);
      setSearched(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">けんさく</h1>

      <div className="search-box">
        <input
          className="input search-input"
          type="text"
          placeholder="本のなまえをいれてね"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="btn btn-yellow search-btn"
          onClick={handleSearch}
          disabled={loading || !query.trim()}
        >
          {loading ? 'さがしてるよ...' : 'さがす'}
        </button>
      </div>

      {error && <p className="message message-error">{error}</p>}

      {searched && results.length === 0 && (
        <p className="message">みつかりませんでした</p>
      )}

      {results.length > 0 && (
        <ul className="search-results">
          {results.map((book) => (
            <li key={book.id} className="search-result-item">
              {book.cover_image_url ? (
                <img src={book.cover_image_url} alt={book.title} className="search-result-cover" />
              ) : (
                <div className="search-result-cover-placeholder">No Image</div>
              )}
              <p className="search-result-title">{book.title}</p>
            </li>
          ))}
        </ul>
      )}

      <Link to="/" className="btn btn-gray back-btn">メニューにもどる</Link>
    </div>
  );
}

export default Search;
