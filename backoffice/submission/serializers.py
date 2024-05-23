# myapp/serializers.py
from rest_framework import serializers

class AuthorSubmissionSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)