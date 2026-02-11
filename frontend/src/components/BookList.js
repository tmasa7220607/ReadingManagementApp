import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getBooks, deleteBook, getErrorMessage } from '../services/api';
import './BookList.css';

function BookList() {
  const [books, setBooks] = useState([]);
  const [ordering, setOrdering] = useState('-created_at');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchBooks = async (order) => {
    setLoading(true);
    try {
      const response = await getBooks(order);
      setBooks(response.data);
    } catch (err) {
      setMessage(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBooks(ordering);
  }, [ordering]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteBook(deleteTarget.id);
      setBooks(books.filter((b) => b.id !== deleteTarget.id));
      setMessage(null);
    } catch (err) {
      setMessage(getErrorMessage(err));
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">本のいちらん</h1>

      <div className="sort-buttons">
        <button
          className={`sort-btn ${ordering === '-created_at' ? 'sort-btn-active' : ''}`}
          onClick={() => setOrdering('-created_at')}
        >
          あたらしいじゅん
        </button>
        <button
          className={`sort-btn ${ordering === 'title' ? 'sort-btn-active' : ''}`}
          onClick={() => setOrdering('title')}
        >
          あいうえおじゅん
        </button>
      </div>

      {loading && <p className="message">よみこみちゅう...</p>}

      {!loading && books.length === 0 && (
        <p className="message">本がまだありません</p>
      )}

      {message && <p className="message message-error">{message}</p>}

      <ul className="book-list">
        {books.map((book) => (
          <li key={book.id} className="book-item">
            <div className="book-info">
              {book.cover_image_url ? (
                <img src={book.cover_image_url} alt={book.title} className="book-cover" />
              ) : (
                <div className="book-cover-placeholder">No Image</div>
              )}
              <p className="book-title">{book.title}</p>
            </div>
            <button
              className="delete-btn"
              onClick={() => setDeleteTarget(book)}
            >
              さくじょ
            </button>
          </li>
        ))}
      </ul>

      {deleteTarget && (
        <div className="dialog-overlay" onClick={() => setDeleteTarget(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <p className="dialog-message">
              「{deleteTarget.title}」をさくじょしますか？
            </p>
            <div className="dialog-buttons">
              <button className="btn btn-red dialog-btn" onClick={handleDelete}>
                さくじょする
              </button>
              <button className="btn btn-gray dialog-btn" onClick={() => setDeleteTarget(null)}>
                やめる
              </button>
            </div>
          </div>
        </div>
      )}

      <Link to="/" className="btn btn-gray back-btn">メニューにもどる</Link>
    </div>
  );
}

export default BookList;
