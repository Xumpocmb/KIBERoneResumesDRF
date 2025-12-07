from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import TutorProfile, Resume, ParentReview, Group, Student
from .serializers import (
    TutorProfileSerializer,
    ResumeSerializer,
    ParentReviewSerializer,
    GroupSerializer,
    StudentSerializer,
    TutorRegisterRequestSerializer,
    TutorLoginSerializer,
    ResumeUpdateSerializer,
    ResumeCreateSerializer,
    TokenSerializer,
)
from app_resumes.crm_integration import get_tutor_data_from_crm, get_client_data_from_crm, get_group_clients_from_crm, get_all_groups
import jwt
from django.conf import settings
from datetime import datetime, timedelta


# JWT token creation utility
def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str):
    """Decode JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def get_current_user_from_request(request):
    """Extract current user from request using JWT token"""
    token = None
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    if auth_header:
        try:
            token = auth_header.split(" ")[1]  # Bearer <token>
        except IndexError:
            return None

    if token:
        payload = decode_access_token(token)
        if payload:
            phone_number = payload.get("sub")
            if phone_number:
                try:
                    return TutorProfile.objects.get(phone_number=phone_number)
                except TutorProfile.DoesNotExist:
                    return None
    return None


def get_current_active_tutor(request):
    """Get current active tutor from request"""
    return get_current_user_from_request(request)


def get_current_senior_tutor(request):
    """Get current senior tutor from request"""
    tutor = get_current_user_from_request(request)
    if tutor and tutor.is_senior:
        return tutor
    return None


def authenticate_tutor(phone_number: str):
    """Authenticate tutor by phone number"""
    try:
        return TutorProfile.objects.get(phone_number=phone_number)
    except TutorProfile.DoesNotExist:
        return None


def get_tutor_by_phone_number(phone_number: str):
    """Get tutor by phone number"""
    try:
        return TutorProfile.objects.get(phone_number=phone_number)
    except TutorProfile.DoesNotExist:
        return None


# Health check endpoint
@api_view(["GET"])
def health_check(request):
    """Health check endpoint"""
    return Response({"status": "ok", "message": "Backend is working"})


# Test endpoint
@api_view(["GET"])
def test_endpoint(request):
    """Test endpoint"""
    return Response({"message": "Hello from Django REST Framework"})


# Tutor registration
@api_view(["POST"])
def register_tutor(request):
    """
    Register a new tutor

    This endpoint registers a new tutor by validating their phone number and tutor branch ID,
    fetching their data from the CRM system, and creating a new TutorProfile in the database.

    Required parameters:
    - phone_number: The tutor's phone number for identification
    - tutor_branch_id: The branch ID where the tutor is registered in the CRM

    Returns:
    - 201 Created: If the tutor is successfully registered with their profile data
    - 400 Bad Request: If the phone number is already registered or validation fails
    - 404 Not Found: If the tutor is not found in the CRM system

    Example request body:
    {
        "phone_number": "+79991234567",
        "tutor_branch_id": 1
    }
    """
    serializer = TutorRegisterRequestSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data["phone_number"]
        tutor_branch_id = serializer.validated_data["tutor_branch_id"]

        # Check if tutor with this phone number already exists
        existing_phone_tutor = get_tutor_by_phone_number(phone_number)
        if existing_phone_tutor:
            return Response({"detail": "Phone number already registered"}, status=status.HTTP_400_BAD_REQUEST)

        # Get tutor data from CRM
        tutor_data = get_tutor_data_from_crm(phone_number, tutor_branch_id)

        if not tutor_data:
            return Response({"detail": "Tutor not found in CRM"}, status=status.HTTP_404_NOT_FOUND)

        # Extract all fields from CRM data with proper error handling
        tutor_crm_id = tutor_data.get("id", None)
        tutor_name = tutor_data.get("name", None)
        branch_ids = tutor_data.get("branch_ids", None)
        dob = tutor_data.get("dob", None)
        gender = tutor_data.get("gender", None)
        streaming_id = tutor_data.get("streaming_id", None)
        note = tutor_data.get("note", None)
        e_date = tutor_data.get("e_date", None)
        avatar_url = tutor_data.get("avatar_url", None)
        phone = tutor_data.get("phone", None)
        email = tutor_data.get("email", None)
        web = tutor_data.get("web", None)
        addr = tutor_data.get("addr", None)
        teacher_to_skill = tutor_data.get("teacher-to-skill", None)

        # Validate required fields to avoid potential database errors
        if tutor_crm_id is not None:
            try:
                tutor_crm_id = int(tutor_crm_id) if str(tutor_crm_id).isdigit() else None
            except (ValueError, TypeError):
                tutor_crm_id = None

        # Create or update tutor profile with all CRM data
        db_tutor = TutorProfile.objects.create(
            tutor_crm_id=tutor_crm_id,
            tutor_name=tutor_name,
            branch=tutor_branch_id,
            is_senior=False,
            phone_number=phone_number,
            # Additional fields from CRM
            branch_ids=branch_ids,
            dob=dob,
            gender=gender,
            streaming_id=streaming_id,
            note=note,
            e_date=e_date,
            avatar_url=avatar_url,
            phone=phone,
            email=email,
            web=web,
            addr=addr,
            teacher_to_skill=teacher_to_skill,
        )

        tutor_serializer = TutorProfileSerializer(db_tutor)
        return Response(tutor_serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Tutor login
@api_view(["POST"])
def login_tutor(request):
    """
    Login a tutor

    This endpoint logs in a tutor by validating their phone number,
    fetching their updated data from the CRM system, and creating a JWT token
    for authentication in subsequent requests.

    Required parameters:
    - phone_number: The tutor's phone number for identification

    Returns:
    - 200 OK: If the tutor is successfully authenticated with JWT token
    - 400 Bad Request: If validation fails
    - 401 Unauthorized: If the phone number is incorrect or tutor not found

    Example request body:
    {
        "phone_number": "+79991234567"
    }
    """
    serializer = TutorLoginSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data["phone_number"]
        tutor = authenticate_tutor(phone_number)
        if not tutor:
            return Response({"detail": "Incorrect phone number"}, status=status.HTTP_401_UNAUTHORIZED)

        # Get updated tutor data from CRM and update DB record
        if tutor.branch:
            tutor_data = get_tutor_data_from_crm(tutor.phone_number, tutor.branch)
            if tutor_data:
                # Update tutor profile with latest CRM data
                update_data = {}
                update_data["tutor_crm_id"] = tutor_data.get("id")
                update_data["tutor_name"] = tutor_data.get("name")
                update_data["branch_ids"] = tutor_data.get("branch_ids")
                update_data["dob"] = tutor_data.get("dob")
                update_data["gender"] = tutor_data.get("gender")
                update_data["streaming_id"] = tutor_data.get("streaming_id")
                update_data["note"] = tutor_data.get("note")
                update_data["e_date"] = tutor_data.get("e_date")
                update_data["avatar_url"] = tutor_data.get("avatar_url")
                update_data["phone"] = tutor_data.get("phone")
                update_data["email"] = tutor_data.get("email")
                update_data["web"] = tutor_data.get("web")
                update_data["addr"] = tutor_data.get("addr")
                update_data["teacher_to_skill"] = tutor_data.get("teacher-to-skill")

                # Update the tutor record with new CRM data
                for field, value in update_data.items():
                    setattr(tutor, field, value)

                tutor.save()

        # Create JWT token
        access_token = create_access_token(data={"sub": tutor.phone_number})
        token_serializer = TokenSerializer(data={"access_token": access_token, "token_type": "bearer"})
        if token_serializer.is_valid():
            return Response({"access_token": access_token, "token_type": "bearer"})
        else:
            return Response({"access_token": access_token, "token_type": "bearer"})
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_tutor_groups(request):
    """
    Get tutor groups

    This endpoint returns the list of groups associated with the authenticated tutor.
    Senior tutors can see all groups, while regular tutors can only see groups they are assigned to.

    Authentication:
    - Requires a valid JWT token in the Authorization header
    - Token is obtained through the login endpoint

    Returns:
    - 200 OK: List of groups associated with the tutor
    - 401 Unauthorized: If the tutor is not authenticated

    Response format:
    [
        {
            "id": group_id,
            "branch_ids": [branch_id1, branch_id2, ...],
            "teacher_ids": [teacher_id1, teacher_id2, ...],
            "name": "Group Name",
            "level_id": level_id,
            "status_id": status_id,
            "company_id": company_id,
            "streaming_id": streaming_id,
            "limit": max_students_count,
            "note": "Additional notes",
            "b_date": "start_date",
            "e_date": "end_date",
            "created_at": "creation_timestamp",
            "updated_at": "update_timestamp",
            "custom_aerodromnaya": "custom_field_value"
        },
        ...
    ]
    """
    current_tutor = get_current_active_tutor(request)
    if not current_tutor:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    # Get tutor's groups from the database
    if current_tutor.is_senior:
        # Senior tutors can see all groups
        groups = Group.objects.all()
    else:
        # Regular tutors see only their groups (based on tutor_crm_id)
        # Find groups where the tutor is listed as a teacher by checking tutor_crm_id in the teacher_ids JSON field
        groups = Group.objects.filter(teacher_ids__contains=current_tutor.tutor_crm_id)

    # Convert to the same format as the CRM response for consistency
    groups_data = []
    for group in groups:
        # Create a format similar to what the CRM API returns
        group_data = {
            "id": group.crm_group_id,
            "branch_ids": group.branch_ids,
            "teacher_ids": group.teacher_ids,
            "name": group.name,
            "level_id": group.level_id,
            "status_id": group.status_id,
            "company_id": group.company_id,
            "streaming_id": group.streaming_id,
            "limit": group.limit,
            "note": group.note,
            "b_date": group.b_date,
            "e_date": group.e_date,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "custom_aerodromnaya": group.custom_aerodromnaya,
        }
        groups_data.append(group_data)

    return Response(groups_data if groups_data else {"groups": []})


@api_view(["GET"])
def get_group_clients(request):
    """Get clients in a group"""
    group_id = request.GET.get("group_id", "")
    current_tutor = get_current_active_tutor(request)
    if not current_tutor:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        # Convert group_id to integer for database query
        group_id_int = int(group_id)

        # Get the group from database
        group = Group.objects.get(id=group_id_int)

        # Get all students associated with this group
        students = Student.objects.filter(group=group)

        # Format the response to match the expected structure
        clients_data = []
        for student in students:
            client_data = {"customer_id": student.student_crm_id, "client_name": student.student_name}
            clients_data.append(client_data)

        return Response(clients_data if clients_data else {"clients": []})
    except ValueError:
        # Handle case where group_id is not a valid integer
        return Response({"clients": []})
    except Group.DoesNotExist:
        return Response({"clients": []})
    except Exception as e:
        # Handle any other errors
        return Response({"clients": []})


# Resume endpoints
class ResumeListView(generics.ListAPIView):
    """Get resumes for a specific client"""

    serializer_class = ResumeSerializer

    def get_queryset(self):
        current_tutor = get_current_active_tutor(self.request)
        if not current_tutor:
            return Resume.objects.none()

        student_crm_id = self.request.query_params.get("student_crm_id", "")
        return Resume.objects.filter(student_crm_id=student_crm_id)


class ResumeDetailView(APIView):
    """Update a specific resume"""

    def put(self, request, resume_id):
        current_tutor = get_current_active_tutor(request)
        if not current_tutor:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        resume = get_object_or_404(Resume, id=resume_id)

        serializer = ResumeUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # Update the resume
            if "content" in serializer.validated_data:
                resume.content = serializer.validated_data["content"]
            if "is_verified" in serializer.validated_data:
                resume.is_verified = serializer.validated_data["is_verified"]

            resume.save()
            resume_serializer = ResumeSerializer(resume)
            return Response(resume_serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyResumeView(APIView):
    """Verify a specific resume (requires senior tutor)"""

    def post(self, request, resume_id):
        current_tutor = get_current_senior_tutor(request)
        if not current_tutor:
            return Response({"detail": "Senior tutor access required"}, status=status.HTTP_403_FORBIDDEN)

        resume = get_object_or_404(Resume, id=resume_id)

        # Update the resume verification status
        resume.is_verified = True
        resume.save()
        resume_serializer = ResumeSerializer(resume)
        return Response(resume_serializer.data)


class UnverifiedResumesView(generics.ListAPIView):
    """Get all unverified resumes"""

    serializer_class = ResumeSerializer

    def get_queryset(self):
        current_tutor = get_current_active_tutor(self.request)
        if not current_tutor:
            return Resume.objects.none()

        return Resume.objects.filter(is_verified=False)


@api_view(["POST"])
def create_resume(request):
    """Create a new resume"""
    current_tutor = get_current_active_tutor(request)
    if not current_tutor:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = ResumeCreateSerializer(data=request.data)
    if serializer.is_valid():
        resume = Resume.objects.create(
            student_crm_id=serializer.validated_data["student_crm_id"],
            content=serializer.validated_data["content"],
            is_verified=serializer.validated_data.get("is_verified", False),
        )
        resume_serializer = ResumeSerializer(resume)
        return Response(resume_serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_resume(request, resume_id):
    """Delete a specific resume"""
    current_tutor = get_current_active_tutor(request)
    if not current_tutor:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    resume = get_object_or_404(Resume, id=resume_id)
    resume.delete()
    return Response({"message": "Resume deleted successfully"})


# Review endpoints
class ParentReviewsView(generics.ListAPIView):
    """Get parent reviews for a specific student"""

    serializer_class = ParentReviewSerializer

    def get_queryset(self):
        current_tutor = get_current_active_tutor(self.request)
        if not current_tutor:
            return ParentReview.objects.none()

        student_crm_id = self.kwargs.get("student_crm_id", "")
        return ParentReview.objects.filter(student_crm_id=student_crm_id)


# Tutor detail endpoint
@api_view(["GET"])
def get_tutor_detail(request):
    """Get tutor details"""
    current_tutor = get_current_active_tutor(request)
    if not current_tutor:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    # Return tutor details from the local database
    return Response(
        {
            "id": current_tutor.tutor_crm_id,
            "name": current_tutor.tutor_name,
            "branch_ids": current_tutor.branch_ids,
            "branch": current_tutor.branch,
            "dob": current_tutor.dob,
            "gender": current_tutor.gender,
            "streaming_id": current_tutor.streaming_id,
            "note": current_tutor.note,
            "e_date": current_tutor.e_date,
            "avatar_url": current_tutor.avatar_url,
            "phone": current_tutor.phone,
            "email": current_tutor.email,
            "web": current_tutor.web,
            "addr": current_tutor.addr,
            "teacher-to-skill": current_tutor.teacher_to_skill,
            "is_senior": current_tutor.is_senior,
        }
    )


# Tutor promotion endpoint
@api_view(["POST"])
def promote_to_senior(request, tutor_id):
    """Promote a tutor to senior status (requires an existing senior tutor)"""
    current_senior_tutor = get_current_senior_tutor(request)
    if not current_senior_tutor:
        return Response({"detail": "Senior tutor access required"}, status=status.HTTP_403_FORBIDDEN)

    tutor = get_object_or_404(TutorProfile, id=tutor_id)

    tutor.is_senior = True
    tutor.save()
    tutor_serializer = TutorProfileSerializer(tutor)
    return Response(tutor_serializer.data)


# Client detail endpoint
@api_view(["GET"])
def get_client_detail(request):
    """Get client details"""
    current_tutor = get_current_active_tutor(request)
    if not current_tutor:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    student_crm_id = request.GET.get("student_crm_id", "")

    # Integrate with CRM to get client details
    if current_tutor.branch:
        client_data = get_client_data_from_crm(student_crm_id, current_tutor.branch)
        if client_data:
            return Response(client_data)

    # Fallback response if CRM integration fails
    return Response({"client_detail": {}})


# Group synchronization endpoint
@api_view(["GET"])
def sync_all_groups(request):
    """Fetch all groups from CRM and synchronize them with the database (Available only to senior tutors)"""
    current_tutor = get_current_senior_tutor(request)
    if not current_tutor:
        return Response({"detail": "Senior tutor access required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        groups_data = get_all_groups()
        if not groups_data:
            return Response({"message": "No groups found in CRM", "synced_count": 0})

        synced_count = 0
        for group_data in groups_data:
            # Extract fields from CRM data
            crm_group_id = group_data.get("id")
            branch_ids = group_data.get("branch_ids")
            teacher_ids = group_data.get("teacher_ids")
            name = group_data.get("name")
            level_id = group_data.get("level_id")
            status_id = group_data.get("status_id")
            company_id = group_data.get("company_id")
            streaming_id = group_data.get("streaming_id")
            limit = group_data.get("limit")
            note = group_data.get("note")
            b_date = group_data.get("b_date")
            e_date = group_data.get("e_date")
            created_at = group_data.get("created_at")
            updated_at = group_data.get("updated_at")
            custom_aerodromnaya = group_data.get("custom_aerodromnaya")

            # Try to get existing group or create new one
            group, created = Group.objects.get_or_create(
                crm_group_id=crm_group_id,
                defaults={
                    "branch_ids": branch_ids,
                    "teacher_ids": teacher_ids,
                    "name": name,
                    "level_id": level_id,
                    "status_id": status_id,
                    "company_id": company_id,
                    "streaming_id": streaming_id,
                    "limit": limit,
                    "note": note,
                    "b_date": b_date,
                    "e_date": e_date,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "custom_aerodromnaya": custom_aerodromnaya,
                },
            )

            # If the group already existed, update its fields
            if not created:
                group.branch_ids = branch_ids
                group.teacher_ids = teacher_ids
                group.name = name
                group.level_id = level_id
                group.status_id = status_id
                group.company_id = company_id
                group.streaming_id = streaming_id
                group.limit = limit
                group.note = note
                group.b_date = b_date
                group.e_date = e_date
                group.created_at = created_at
                group.updated_at = updated_at
                group.custom_aerodromnaya = custom_aerodromnaya
                group.save()

            synced_count += 1

        return Response({"message": f"Successfully synchronized {synced_count} groups", "synced_count": synced_count})

    except Exception as e:
        return Response({"detail": f"An error occurred while synchronizing groups: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Student synchronization endpoint
@api_view(["GET"])
def sync_students_with_groups(request):
    """Fetch all students from CRM for each group and synchronize them with the database (Available only to senior tutors)"""
    current_tutor = get_current_senior_tutor(request)
    if not current_tutor:
        return Response({"detail": "Senior tutor access required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        # Get all groups from the database
        groups = Group.objects.all()

        if not groups:
            return Response({"message": "No groups found in database", "synced_count": 0})

        total_synced = 0

        for group in groups:
            # Get students for this group from CRM
            group_clients = get_group_clients_from_crm(str(group.crm_group_id), current_tutor.branch)

            if group_clients:
                for client in group_clients:
                    customer_id = client.get("customer_id")
                    client_name = client.get("client_name")

                    if customer_id and client_name:
                        # Create or update student record with group relationship
                        student, created = Student.objects.get_or_create(student_crm_id=customer_id, defaults={"student_name": client_name, "group_id": group.id})

                        # If student already exists, update the group relationship
                        if not created and student.group_id != group.id:
                            student.group_id = group.id
                            student.save()

                        total_synced += 1

        return Response({"message": f"Successfully synchronized {total_synced} students", "synced_count": total_synced})

    except Exception as e:
        return Response({"detail": f"An error occurred while synchronizing students: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
