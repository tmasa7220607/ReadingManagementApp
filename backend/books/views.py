import logging

import requests
from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Book
from .serializers import BookSerializer, ISBNSerializer
from .services import lookup_book_by_isbn

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
def book_list_create(request):
    """書籍一覧・登録"""
    if request.method == 'GET':
        return _book_list(request)
    return _book_create(request)


def _book_create(request):
    """書籍登録: ISBN受取→外部API検索→DB保存→結果返却"""
    serializer = ISBNSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'ただしいISBNをにゅうりょくしてください'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    isbn = serializer.validated_data['isbn']

    # 重複チェック
    existing = Book.objects.filter(isbn=isbn).first()
    if existing:
        return Response(
            {'error': 'このほんはもうとうろくされています', 'book': BookSerializer(existing).data},
            status=status.HTTP_409_CONFLICT,
        )

    # 外部APIから書籍情報を取得
    try:
        book_info = lookup_book_by_isbn(isbn)
    except requests.exceptions.Timeout:
        return Response(
            {'error': 'みつかりませんでした'},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        return Response(
            {'error': 'つながりませんでした'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except requests.exceptions.RequestException:
        return Response(
            {'error': 'みつかりませんでした'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if book_info is None:
        return Response(
            {'error': 'みつかりませんでした'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # DB保存
    try:
        book = Book.objects.create(
            isbn=isbn,
            title=book_info['title'],
            cover_image_url=book_info.get('cover_image_url'),
        )
    except IntegrityError:
        return Response(
            {'error': 'このほんはもうとうろくされています'},
            status=status.HTTP_409_CONFLICT,
        )
    except Exception:
        logger.exception('Book creation failed')
        return Response(
            {'error': 'エラーがおきました'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(BookSerializer(book).data, status=status.HTTP_201_CREATED)


def _book_list(request):
    """書籍一覧: 並び順パラメータ対応（登録日時順 / タイトル50音順）"""
    ordering = request.query_params.get('ordering', '-created_at')

    if ordering in ('title', '-title', 'created_at', '-created_at'):
        books = Book.objects.all().order_by(ordering)
    else:
        books = Book.objects.all().order_by('-created_at')

    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
def book_delete(request, pk):
    """書籍削除: 指定IDの書籍を削除"""
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        return Response(
            {'error': 'みつかりませんでした'},
            status=status.HTTP_404_NOT_FOUND,
        )

    book.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def book_search(request):
    """書籍検索: タイトル部分一致検索"""
    query = request.query_params.get('q', '').strip()

    if not query:
        return Response([])

    books = Book.objects.filter(title__icontains=query).order_by('-created_at')
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)
