from rest_framework import serializers


class APIInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    version = serializers.CharField()
    status = serializers.CharField()


class LivenessSerializer(serializers.Serializer):
    status = serializers.CharField()


class ReadinessChecksSerializer(serializers.Serializer):
    database = serializers.BooleanField()
    cache = serializers.BooleanField()
    celery_broker = serializers.BooleanField()


class ReadinessSerializer(serializers.Serializer):
    status = serializers.CharField()
    checks = ReadinessChecksSerializer()
