from django.urls import path

from . import views

urlpatterns = [
    path('books/', views.book_list_create, name='book-list-create'),
    path('books/<int:pk>/', views.book_delete, name='book-delete'),
    path('books/search/', views.book_search, name='book-search'),
]
