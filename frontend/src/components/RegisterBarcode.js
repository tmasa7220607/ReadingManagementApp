import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Html5Qrcode } from 'html5-qrcode';
import { registerBook, getErrorMessage } from '../services/api';
import './RegisterBarcode.css';

function RegisterBarcode() {
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState('');
  const [registeredBook, setRegisteredBook] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(false);
  const scannerRef = useRef(null);
  const readerRef = useRef(null);

  const stopScanner = async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
      } catch {
        // already stopped
      }
      scannerRef.current = null;
    }
    setScanning(false);
  };

  const handleBarcode = async (decodedText) => {
    const isbn = decodedText.replace(/[^0-9]/g, '');
    if (isbn.length !== 10 && isbn.length !== 13) {
      setMessage('もういちどためしてください');
      setMessageType('error');
      return;
    }

    await stopScanner();
    setLoading(true);
    setMessage(null);
    setRegisteredBook(null);

    try {
      const response = await registerBook(isbn);
      setRegisteredBook(response.data);
      setMessage('とうろくできました！');
      setMessageType('success');
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

  const startScanner = async () => {
    setMessage(null);
    setRegisteredBook(null);

    const html5Qrcode = new Html5Qrcode('barcode-reader');
    scannerRef.current = html5Qrcode;

    try {
      await html5Qrcode.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 150 } },
        handleBarcode,
      );
      setScanning(true);
    } catch {
      setMessage('カメラをつかえませんでした');
      setMessageType('error');
    }
  };

  useEffect(() => {
    return () => {
      if (scannerRef.current) {
        scannerRef.current.stop().catch(() => {});
      }
    };
  }, []);

  return (
    <div className="page">
      <h1 className="page-title">バーコードでとうろく</h1>

      <div id="barcode-reader" ref={readerRef} className="barcode-reader" />

      {!scanning && !loading && (
        <button className="btn btn-pink scanner-btn" onClick={startScanner}>
          カメラをひらく
        </button>
      )}

      {scanning && (
        <button className="btn btn-gray scanner-btn" onClick={stopScanner}>
          カメラをとじる
        </button>
      )}

      {loading && <p className="message">さがしてるよ...</p>}

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

      {!scanning && (
        <Link to="/" className="btn btn-gray back-btn">メニューにもどる</Link>
      )}
    </div>
  );
}

export default RegisterBarcode;
