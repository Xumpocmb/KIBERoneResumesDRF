from django.db import models


class TutorProfile(models.Model):
    id = models.AutoField(primary_key=True)
    tutor_crm_id = models.CharField(max_length=255, null=True, unique=True)
    tutor_name = models.CharField(max_length=255, null=True)
    branch = models.CharField(max_length=255, null=True)
    is_senior = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, unique=True)

    # Additional models based on CRM response
    branch_ids = models.JSONField(null=True)  # Corresponds to "branch_ids" in the JSON
    dob = models.CharField(max_length=10, null=True)  # Corresponds to "dob" in the JSON
    gender = models.IntegerField(null=True)  # Corresponds to "gender" in the JSON
    streaming_id = models.IntegerField(null=True)  # Corresponds to "streaming_id" in the JSON
    note = models.TextField(null=True)  # Corresponds to "note" in the JSON
    e_date = models.CharField(max_length=10, null=True)  # Corresponds to "e_date" in the JSON
    avatar_url = models.CharField(max_length=500, null=True)  # Corresponds to "avatar_url" in the JSON
    phone = models.JSONField(null=True)  # Corresponds to "phone" array in the JSON
    email = models.JSONField(null=True)  # Corresponds to "email" array in the JSON
    web = models.JSONField(null=True)  # Corresponds to "web" array in the JSON
    addr = models.JSONField(null=True)  # Corresponds to "addr" array in the JSON
    teacher_to_skill = models.JSONField(null=True)  # Corresponds to "teacher-to-skill" in the JSON


class Resume(models.Model):
    id = models.AutoField(primary_key=True)
    student_crm_id = models.CharField(max_length=255)
    content = models.TextField(null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ParentReview(models.Model):
    id = models.AutoField(primary_key=True)
    student_crm_id = models.CharField(max_length=255)
    content = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Group(models.Model):
    id = models.AutoField(primary_key=True)
    crm_group_id = models.IntegerField(unique=True)  # Corresponds to "id" in the JSON
    branch_ids = models.JSONField()  # Corresponds to "branch_ids" in the JSON
    teacher_ids = models.JSONField()  # Corresponds to "teacher_ids" in the JSON
    name = models.CharField(max_length=500)  # Corresponds to "name" in the JSON
    level_id = models.IntegerField()  # Corresponds to "level_id" in the JSON
    status_id = models.IntegerField()  # Corresponds to "status_id" in the JSON
    company_id = models.IntegerField(null=True)  # Corresponds to "company_id" in the JSON
    streaming_id = models.IntegerField(null=True)  # Corresponds to "streaming_id" in the JSON
    limit = models.IntegerField()  # Corresponds to "limit" in the JSON
    note = models.TextField(null=True)  # Corresponds to "note" in the JSON
    b_date = models.CharField(max_length=10, null=True)  # Corresponds to "b_date" in the JSON
    e_date = models.CharField(max_length=10, null=True)  # Corresponds to "e_date" in the JSON
    created_at = models.CharField(max_length=20, null=True)  # Corresponds to "created_at" in the JSON
    updated_at = models.CharField(max_length=20, null=True)  # Corresponds to "updated_at" in the JSON
    custom_aerodromnaya = models.CharField(max_length=10, null=True)  # Corresponds to "custom_aerodromnaya" in the JSON

    # Relationship to tutors (many-to-many through a separate model if needed)
    tutors = models.ManyToManyField("TutorProfile", related_name="groups", blank=True)


class Student(models.Model):
    id = models.AutoField(primary_key=True)
    student_crm_id = models.IntegerField(unique=True)  # Corresponds to "customer_id" in the JSON
    student_name = models.CharField(max_length=255)  # Corresponds to "client_name" in the JSON
    group = models.ForeignKey("Group", related_name="students", null=True, on_delete=models.CASCADE)
