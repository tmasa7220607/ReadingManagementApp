from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'isbn', 'title', 'cover_image_url', 'created_at']
        read_only_fields = ['id', 'title', 'cover_image_url', 'created_at']


class ISBNSerializer(serializers.Serializer):
    isbn = serializers.CharField(max_length=13, min_length=10)

    def validate_isbn(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('ISBNは数字のみで入力してください')
        if len(value) not in (10, 13):
            raise serializers.ValidationError('ISBNは10桁または13桁で入力してください')
        return value
