# myapp/serializers.py
from rest_framework import serializers

class AuthorSubmissionSerializer(serializers.Serializer):
    data = serializers.JSONField(required=True)