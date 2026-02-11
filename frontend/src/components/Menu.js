import React from 'react';
import { Link } from 'react-router-dom';
import './Menu.css';

function Menu() {
  return (
    <div className="page">
      <h1 className="page-title">ぼくの読書きろく</h1>
      <nav className="menu-nav">
        <Link to="/register/barcode" className="btn btn-pink menu-btn">
          バーコードでとうろく
        </Link>
        <Link to="/register/manual" className="btn btn-blue menu-btn">
          手で入力
        </Link>
        <Link to="/books" className="btn btn-green menu-btn">
          本のいちらん
        </Link>
        <Link to="/search" className="btn btn-yellow menu-btn">
          けんさく
        </Link>
      </nav>
    </div>
  );
}

export default Menu;
