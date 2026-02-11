import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { registerBook, getErrorMessage } from '../services/api';
import './RegisterManual.css';

function RegisterManual() {
  const [isbn, setIsbn] = useState('');
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState('');
  const [registeredBook, setRegisteredBook] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const value = e.target.value.replace(/[^0-9]/g, '');
    if (value.length <= 13) {
      setIsbn(value);
    }
  };

  const handleSubmit = async () => {
    if (isbn.length !== 10 && isbn.length !== 13) {
      setMessage('ISBNは10けたか13けたでいれてね');
      setMessageType('error');
      return;
    }

    setLoading(true);
    setMessage(null);
    setRegisteredBook(null);

    try {
      const response = await registerBook(isbn);
      setRegisteredBook(response.data);
      setMessage('とうろくできました！');
      setMessageType('success');
      setIsbn('');
    } catch (err) {
      setMessage(getErrorMessage(err));
      setMessageType('error');
      if (err.response?.status === 409 && err.response?.data?.book) {
        setRegisteredBook(err.response.data.book);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">手で入力</h1>

      <input
        className="input"
        type="text"
        inputMode="numeric"
        placeholder="ISBNをいれてね"
        value={isbn}
        onChange={handleChange}
        disabled={loading}
      />

      <div className="isbn-count">{isbn.length} けた</div>

      <button
        className="btn btn-blue register-btn"
        onClick={handleSubmit}
        disabled={loading || isbn.length === 0}
      >
        {loading ? 'さがしてるよ...' : 'とうろくする'}
      </button>

      {message && (
        <p className={`message ${messageType === 'error' ? 'message-error' : 'message-success'}`}>
          {message}
        </p>
      )}

      {registeredBook && (
        <div className="registered-book">
          {registeredBook.cover_image_url && (
            <img
              src={registeredBook.cover_image_url}
              alt={registeredBook.title}
              className="registered-book-cover"
            />
          )}
          <p className="registered-book-title">{registeredBook.title}</p>
        </div>
      )}

      <Link to="/" className="btn btn-gray back-btn">メニューにもどる</Link>
    </div>
  );
}

export default RegisterManual;
