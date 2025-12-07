from rest_framework import serializers
from .models import TutorProfile, Resume, ParentReview, Group, Student


class TutorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TutorProfile
        fields = "__all__"


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = "__all__"


class ParentReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentReview
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"


class TutorRegisterRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    tutor_branch_id = serializers.CharField(max_length=255)


class TutorLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)


class ResumeUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False)
    is_verified = serializers.BooleanField(required=False)


class ResumeCreateSerializer(serializers.Serializer):
    student_crm_id = serializers.CharField(max_length=255)
    content = serializers.CharField()
    is_verified = serializers.BooleanField(default=False)


class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    token_type = serializers.CharField()
