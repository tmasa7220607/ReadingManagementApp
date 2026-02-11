import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
});

// ネットワークエラー・タイムアウトをひらがなメッセージに変換
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      error.friendlyMessage = 'つながりませんでした';
    } else if (!error.response) {
      error.friendlyMessage = 'つながりませんでした';
    }
    return Promise.reject(error);
  },
);

export function getErrorMessage(err) {
  if (err.response?.data?.error) {
    return err.response.data.error;
  }
  if (err.friendlyMessage) {
    return err.friendlyMessage;
  }
  return 'エラーがおきました';
}

export function registerBook(isbn) {
  return api.post('/books/', { isbn });
}

export function getBooks(ordering = '-created_at') {
  return api.get('/books/', { params: { ordering } });
}

export function deleteBook(id) {
  return api.delete(`/books/${id}/`);
}

export function searchBooks(query) {
  return api.get('/books/search/', { params: { q: query } });
}
