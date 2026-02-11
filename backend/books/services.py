import logging
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger(__name__)

API_TIMEOUT = 5

# NDLサーチ OpenSearch APIの名前空間
NS = {
    'rss': 'http://purl.org/rss/1.0/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'openSearch': 'http://a9.com/-/spec/opensearchrss/1.0/',
}


def fetch_book_from_ndl(isbn):
    """NDLサーチ OpenSearch APIからISBNで書籍情報を取得する"""
    url = 'https://ndlsearch.ndl.go.jp/api/opensearch'
    params = {'isbn': isbn}

    response = requests.get(url, params=params, timeout=API_TIMEOUT)
    response.raise_for_status()

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        logger.warning('NDL API returned invalid XML for ISBN: %s', isbn)
        return None

    item = root.find('.//rss:item', NS)
    if item is None:
        return None

    title_elem = item.find('rss:title', NS)
    title = title_elem.text if title_elem is not None else None
    if not title:
        return None

    cover_image_url = None

    return {
        'title': title,
        'cover_image_url': cover_image_url,
    }


def fetch_cover_from_google_books(isbn):
    """Google Books APIからISBNで表紙画像URLを取得する"""
    url = 'https://www.googleapis.com/books/v1/volumes'
    params = {'q': f'isbn:{isbn}'}

    response = requests.get(url, params=params, timeout=API_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    if data.get('totalItems', 0) == 0:
        return None

    items = data.get('items', [])
    if not items:
        return None

    volume_info = items[0].get('volumeInfo', {})
    image_links = volume_info.get('imageLinks', {})

    # thumbnail → smallThumbnailの順で取得を試みる
    cover_url = image_links.get('thumbnail') or image_links.get('smallThumbnail')

    # HTTPをHTTPSに変換
    if cover_url and cover_url.startswith('http://'):
        cover_url = cover_url.replace('http://', 'https://', 1)

    return cover_url


def lookup_book_by_isbn(isbn):
    """ISBNから書籍情報を検索する（NDL→Google Booksのフォールバック）

    Returns:
        dict: {'title': str, 'cover_image_url': str|None} or None
    """
    # 1. NDLサーチAPIで書籍情報を取得
    book_info = fetch_book_from_ndl(isbn)

    if book_info is None:
        return None

    # 2. 表紙画像がない場合、Google Books APIでフォールバック
    if not book_info['cover_image_url']:
        try:
            cover_url = fetch_cover_from_google_books(isbn)
            book_info['cover_image_url'] = cover_url
        except requests.exceptions.RequestException:
            logger.warning('Google Books API failed for ISBN: %s', isbn)

    return book_info
