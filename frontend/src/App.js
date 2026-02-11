import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Menu from './components/Menu';
import RegisterBarcode from './components/RegisterBarcode';
import RegisterManual from './components/RegisterManual';
import BookList from './components/BookList';
import Search from './components/Search';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<Menu />} />
          <Route path="/register/barcode" element={<RegisterBarcode />} />
          <Route path="/register/manual" element={<RegisterManual />} />
          <Route path="/books" element={<BookList />} />
          <Route path="/search" element={<Search />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
