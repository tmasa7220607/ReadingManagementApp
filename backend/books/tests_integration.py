"""
フロントエンド・バックエンド結合テスト

実行方法（Dockerコンテナ内）:
  python manage.py test books.tests_integration --verbosity=2

外部APIへの実際のリクエストを行い、
ISBN → 外部API検索 → DB保存 → 一覧取得 → 検索 → 削除 の一連のフローを検証する。
"""

import requests
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Book

# テスト用ISBN（実在する書籍）
# 「ぐりとぐら」 ISBN: 9784834000825
TEST_ISBN = '9784834000825'
TEST_TITLE_PARTIAL = 'ぐりとぐら'


class FullFlowIntegrationTest(TestCase):
    """登録→一覧→検索→削除の一連のフローテスト（外部API実呼び出し）"""

    def setUp(self):
        self.client = APIClient()

    def test_full_flow(self):
        # 1. 書籍登録（外部API経由）
        response = self.client.post('/api/books/', {'isbn': TEST_ISBN})
        self.assertIn(response.status_code, [201, 409],
                      f'Registration failed: {response.data}')

        if response.status_code == 409:
            # 既にDBにある場合は削除してリトライ
            Book.objects.filter(isbn=TEST_ISBN).delete()
            response = self.client.post('/api/books/', {'isbn': TEST_ISBN})
            self.assertEqual(response.status_code, 201,
                             f'Registration failed after cleanup: {response.data}')

        book_data = response.data
        book_id = book_data['id']
        self.assertEqual(book_data['isbn'], TEST_ISBN)
        self.assertIn(TEST_TITLE_PARTIAL, book_data['title'])
        self.assertTrue(Book.objects.filter(isbn=TEST_ISBN).exists())

        # 2. 一覧取得で登録した本が含まれるか確認
        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, 200)
        isbns = [b['isbn'] for b in response.data]
        self.assertIn(TEST_ISBN, isbns)

        # 3. タイトル検索で見つかるか確認
        response = self.client.get('/api/books/search/', {'q': TEST_TITLE_PARTIAL})
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertIn(TEST_TITLE_PARTIAL, response.data[0]['title'])

        # 4. 並び替え（タイトル順）が動作するか確認
        response = self.client.get('/api/books/', {'ordering': 'title'})
        self.assertEqual(response.status_code, 200)

        # 5. 削除
        response = self.client.delete(f'/api/books/{book_id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Book.objects.filter(isbn=TEST_ISBN).exists())

        # 6. 削除後に一覧から消えているか確認
        response = self.client.get('/api/books/')
        self.assertEqual(response.status_code, 200)
        isbns = [b['isbn'] for b in response.data]
        self.assertNotIn(TEST_ISBN, isbns)


class DuplicateRegistrationTest(TestCase):
    """重複登録のフローテスト（外部API実呼び出し）"""

    def setUp(self):
        self.client = APIClient()

    def test_duplicate_returns_409(self):
        # 1回目: 登録
        response = self.client.post('/api/books/', {'isbn': TEST_ISBN})
        self.assertIn(response.status_code, [201, 409])

        if response.status_code == 409:
            Book.objects.filter(isbn=TEST_ISBN).delete()
            response = self.client.post('/api/books/', {'isbn': TEST_ISBN})
            self.assertEqual(response.status_code, 201)

        # 2回目: 重複登録 → 409
        response = self.client.post('/api/books/', {'isbn': TEST_ISBN})
        self.assertEqual(response.status_code, 409)
        self.assertIn('book', response.data)
        self.assertEqual(response.data['book']['isbn'], TEST_ISBN)


class FrontendAccessTest(TestCase):
    """フロントエンドの静的ファイルアクセステスト"""

    def test_frontend_reachable(self):
        """フロントエンド(port 3000)がHTTPレスポンスを返すか確認"""
        try:
            response = requests.get('http://frontend:3000/', timeout=5)
            self.assertEqual(response.status_code, 200)
            self.assertIn('ぼくの読書きろく', response.text)
        except requests.exceptions.ConnectionError:
            self.skipTest('Frontend container not reachable (expected in test DB mode)')


class CORSHeaderTest(TestCase):
    """CORSヘッダーのテスト"""

    def setUp(self):
        self.client = APIClient()

    def test_cors_allows_localhost_3000(self):
        response = self.client.get(
            '/api/books/',
            HTTP_ORIGIN='http://localhost:3000',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Access-Control-Allow-Origin'),
            'http://localhost:3000',
        )

    def test_cors_blocks_unknown_origin(self):
        response = self.client.get(
            '/api/books/',
            HTTP_ORIGIN='http://evil.example.com',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get('Access-Control-Allow-Origin'))
