from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Book
from .services import (
    fetch_book_from_ndl,
    fetch_cover_from_google_books,
    lookup_book_by_isbn,
)


class BookCreateAPITest(TestCase):
    """POST /api/books/ — 書籍登録のテスト"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/books/'

    @patch('books.views.lookup_book_by_isbn')
    def test_create_success(self, mock_lookup):
        mock_lookup.return_value = {
            'title': 'テストの本',
            'cover_image_url': 'https://example.com/cover.jpg',
        }
        response = self.client.post(self.url, {'isbn': '9784000000001'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], 'テストの本')
        self.assertEqual(response.data['isbn'], '9784000000001')
        self.assertTrue(Book.objects.filter(isbn='9784000000001').exists())

    @patch('books.views.lookup_book_by_isbn')
    def test_create_without_cover(self, mock_lookup):
        mock_lookup.return_value = {
            'title': '表紙なしの本',
            'cover_image_url': None,
        }
        response = self.client.post(self.url, {'isbn': '9784000000002'})
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data['cover_image_url'])

    def test_create_invalid_isbn_not_digits(self):
        response = self.client.post(self.url, {'isbn': 'abcdefghijk'})
        self.assertEqual(response.status_code, 400)

    def test_create_invalid_isbn_wrong_length(self):
        response = self.client.post(self.url, {'isbn': '123'})
        self.assertEqual(response.status_code, 400)

    def test_create_missing_isbn(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    @patch('books.views.lookup_book_by_isbn')
    def test_create_duplicate(self, mock_lookup):
        Book.objects.create(isbn='9784000000001', title='既存の本')
        mock_lookup.return_value = {'title': '既存の本', 'cover_image_url': None}
        response = self.client.post(self.url, {'isbn': '9784000000001'})
        self.assertEqual(response.status_code, 409)
        self.assertIn('book', response.data)

    @patch('books.views.lookup_book_by_isbn')
    def test_create_not_found(self, mock_lookup):
        mock_lookup.return_value = None
        response = self.client.post(self.url, {'isbn': '9784000000099'})
        self.assertEqual(response.status_code, 404)

    @patch('books.views.lookup_book_by_isbn')
    def test_create_timeout(self, mock_lookup):
        mock_lookup.side_effect = requests.exceptions.Timeout()
        response = self.client.post(self.url, {'isbn': '9784000000001'})
        self.assertEqual(response.status_code, 504)

    @patch('books.views.lookup_book_by_isbn')
    def test_create_connection_error(self, mock_lookup):
        mock_lookup.side_effect = requests.exceptions.ConnectionError()
        response = self.client.post(self.url, {'isbn': '9784000000001'})
        self.assertEqual(response.status_code, 502)

    @patch('books.views.lookup_book_by_isbn')
    def test_create_request_exception(self, mock_lookup):
        mock_lookup.side_effect = requests.exceptions.RequestException()
        response = self.client.post(self.url, {'isbn': '9784000000001'})
        self.assertEqual(response.status_code, 502)


class BookListAPITest(TestCase):
    """GET /api/books/ — 書籍一覧のテスト"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/books/'
        self.book1 = Book.objects.create(isbn='9784000000001', title='あいうえお')
        self.book2 = Book.objects.create(isbn='9784000000002', title='かきくけこ')

    def test_list_default_ordering(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        # デフォルトは -created_at（新しい順）
        self.assertEqual(response.data[0]['isbn'], '9784000000002')

    def test_list_ordering_by_title(self):
        response = self.client.get(self.url, {'ordering': 'title'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['title'], 'あいうえお')
        self.assertEqual(response.data[1]['title'], 'かきくけこ')

    def test_list_ordering_by_created_at(self):
        response = self.client.get(self.url, {'ordering': 'created_at'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['isbn'], '9784000000001')

    def test_list_invalid_ordering_fallback(self):
        response = self.client.get(self.url, {'ordering': 'invalid'})
        self.assertEqual(response.status_code, 200)
        # 不正な値はデフォルト（-created_at）にフォールバック
        self.assertEqual(response.data[0]['isbn'], '9784000000002')

    def test_list_empty(self):
        Book.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)


class BookDeleteAPITest(TestCase):
    """DELETE /api/books/{id}/ — 書籍削除のテスト"""

    def setUp(self):
        self.client = APIClient()
        self.book = Book.objects.create(isbn='9784000000001', title='削除テスト')

    def test_delete_success(self):
        response = self.client.delete(f'/api/books/{self.book.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_delete_not_found(self):
        response = self.client.delete('/api/books/99999/')
        self.assertEqual(response.status_code, 404)


class BookSearchAPITest(TestCase):
    """GET /api/books/search/?q= — 書籍検索のテスト"""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/books/search/'
        Book.objects.create(isbn='9784000000001', title='ドラえもん')
        Book.objects.create(isbn='9784000000002', title='ドラゴンボール')
        Book.objects.create(isbn='9784000000003', title='ワンピース')

    def test_search_match(self):
        response = self.client.get(self.url, {'q': 'ドラ'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_search_single_match(self):
        response = self.client.get(self.url, {'q': 'ワンピース'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'ワンピース')

    def test_search_no_match(self):
        response = self.client.get(self.url, {'q': 'ナルト'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_search_empty_query(self):
        response = self.client.get(self.url, {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_search_no_query_param(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_search_whitespace_query(self):
        response = self.client.get(self.url, {'q': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)


# --- 外部API連携テスト ---

NDL_XML_WITH_ITEM = '''\
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/"
     version="2.0">
  <channel>
    <title>NDL Search</title>
    <openSearch:totalResults>1</openSearch:totalResults>
    <item>
      <title>テストブック</title>
      <dc:creator>テスト著者</dc:creator>
    </item>
  </channel>
</rss>'''.encode('utf-8')

NDL_XML_NO_ITEM = '''\
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/"
     version="2.0">
  <channel>
    <title>NDL Search</title>
    <openSearch:totalResults>0</openSearch:totalResults>
  </channel>
</rss>'''.encode('utf-8')

NDL_XML_EMPTY_TITLE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title></title>
    </item>
  </channel>
</rss>'''.encode('utf-8')


def _mock_ndl_response(content, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.content = content
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_google_response(json_data, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class FetchBookFromNDLTest(TestCase):
    """NDLサーチAPI連携のテスト"""

    @patch('books.services.requests.get')
    def test_success(self, mock_get):
        mock_get.return_value = _mock_ndl_response(NDL_XML_WITH_ITEM)
        result = fetch_book_from_ndl('9784000000001')
        self.assertEqual(result['title'], 'テストブック')
        self.assertIsNone(result['cover_image_url'])

    @patch('books.services.requests.get')
    def test_no_item(self, mock_get):
        mock_get.return_value = _mock_ndl_response(NDL_XML_NO_ITEM)
        result = fetch_book_from_ndl('9784000000001')
        self.assertIsNone(result)

    @patch('books.services.requests.get')
    def test_empty_title(self, mock_get):
        mock_get.return_value = _mock_ndl_response(NDL_XML_EMPTY_TITLE)
        result = fetch_book_from_ndl('9784000000001')
        self.assertIsNone(result)

    @patch('books.services.requests.get')
    def test_invalid_xml(self, mock_get):
        mock_get.return_value = _mock_ndl_response(b'not xml at all')
        result = fetch_book_from_ndl('9784000000001')
        self.assertIsNone(result)

    @patch('books.services.requests.get')
    def test_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_resp
        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_book_from_ndl('9784000000001')

    @patch('books.services.requests.get')
    def test_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(requests.exceptions.Timeout):
            fetch_book_from_ndl('9784000000001')


class FetchCoverFromGoogleBooksTest(TestCase):
    """Google Books API連携のテスト"""

    @patch('books.services.requests.get')
    def test_success_thumbnail(self, mock_get):
        mock_get.return_value = _mock_google_response({
            'totalItems': 1,
            'items': [{'volumeInfo': {'imageLinks': {
                'thumbnail': 'https://example.com/thumb.jpg',
            }}}],
        })
        result = fetch_cover_from_google_books('9784000000001')
        self.assertEqual(result, 'https://example.com/thumb.jpg')

    @patch('books.services.requests.get')
    def test_success_small_thumbnail_fallback(self, mock_get):
        mock_get.return_value = _mock_google_response({
            'totalItems': 1,
            'items': [{'volumeInfo': {'imageLinks': {
                'smallThumbnail': 'https://example.com/small.jpg',
            }}}],
        })
        result = fetch_cover_from_google_books('9784000000001')
        self.assertEqual(result, 'https://example.com/small.jpg')

    @patch('books.services.requests.get')
    def test_http_to_https_conversion(self, mock_get):
        mock_get.return_value = _mock_google_response({
            'totalItems': 1,
            'items': [{'volumeInfo': {'imageLinks': {
                'thumbnail': 'http://example.com/thumb.jpg',
            }}}],
        })
        result = fetch_cover_from_google_books('9784000000001')
        self.assertEqual(result, 'https://example.com/thumb.jpg')

    @patch('books.services.requests.get')
    def test_no_items(self, mock_get):
        mock_get.return_value = _mock_google_response({'totalItems': 0})
        result = fetch_cover_from_google_books('9784000000001')
        self.assertIsNone(result)

    @patch('books.services.requests.get')
    def test_empty_items_list(self, mock_get):
        mock_get.return_value = _mock_google_response({
            'totalItems': 1,
            'items': [],
        })
        result = fetch_cover_from_google_books('9784000000001')
        self.assertIsNone(result)

    @patch('books.services.requests.get')
    def test_no_image_links(self, mock_get):
        mock_get.return_value = _mock_google_response({
            'totalItems': 1,
            'items': [{'volumeInfo': {}}],
        })
        result = fetch_cover_from_google_books('9784000000001')
        self.assertIsNone(result)

    @patch('books.services.requests.get')
    def test_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(requests.exceptions.Timeout):
            fetch_cover_from_google_books('9784000000001')


class LookupBookByISBNTest(TestCase):
    """lookup_book_by_isbn フォールバック動作のテスト"""

    @patch('books.services.fetch_cover_from_google_books')
    @patch('books.services.fetch_book_from_ndl')
    def test_ndl_found_google_cover(self, mock_ndl, mock_google):
        mock_ndl.return_value = {'title': 'テスト本', 'cover_image_url': None}
        mock_google.return_value = 'https://example.com/cover.jpg'
        result = lookup_book_by_isbn('9784000000001')
        self.assertEqual(result['title'], 'テスト本')
        self.assertEqual(result['cover_image_url'], 'https://example.com/cover.jpg')

    @patch('books.services.fetch_cover_from_google_books')
    @patch('books.services.fetch_book_from_ndl')
    def test_ndl_found_google_no_cover(self, mock_ndl, mock_google):
        mock_ndl.return_value = {'title': 'テスト本', 'cover_image_url': None}
        mock_google.return_value = None
        result = lookup_book_by_isbn('9784000000001')
        self.assertEqual(result['title'], 'テスト本')
        self.assertIsNone(result['cover_image_url'])

    @patch('books.services.fetch_cover_from_google_books')
    @patch('books.services.fetch_book_from_ndl')
    def test_ndl_found_google_fails_gracefully(self, mock_ndl, mock_google):
        mock_ndl.return_value = {'title': 'テスト本', 'cover_image_url': None}
        mock_google.side_effect = requests.exceptions.Timeout()
        result = lookup_book_by_isbn('9784000000001')
        # Google Books失敗でもタイトルは返る
        self.assertEqual(result['title'], 'テスト本')
        self.assertIsNone(result['cover_image_url'])

    @patch('books.services.fetch_cover_from_google_books')
    @patch('books.services.fetch_book_from_ndl')
    def test_ndl_not_found(self, mock_ndl, mock_google):
        mock_ndl.return_value = None
        result = lookup_book_by_isbn('9784000000099')
        self.assertIsNone(result)
        mock_google.assert_not_called()

    @patch('books.services.fetch_cover_from_google_books')
    @patch('books.services.fetch_book_from_ndl')
    def test_ndl_has_cover_skips_google(self, mock_ndl, mock_google):
        mock_ndl.return_value = {
            'title': 'テスト本',
            'cover_image_url': 'https://ndl.go.jp/cover.jpg',
        }
        result = lookup_book_by_isbn('9784000000001')
        self.assertEqual(result['cover_image_url'], 'https://ndl.go.jp/cover.jpg')
        mock_google.assert_not_called()
