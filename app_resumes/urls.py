from django.urls import path
from . import views


urlpatterns = [
    # Health and test endpoints
    path("health/", views.health_check, name="health-check"),
    path("test/", views.test_endpoint, name="test-endpoint"),
    # Tutor endpoints
    path("tutors/register/", views.register_tutor, name="tutor-register"),
    path("tutors/login/", views.login_tutor, name="tutor-login"),
    path("tutors/groups/", views.get_tutor_groups, name="tutor-groups"),
    path("tutors/detail/", views.get_tutor_detail, name="tutor-detail"),
    path("tutors/<int:tutor_id>/promote-to-senior/", views.promote_to_senior, name="promote-to-senior"),
    # Group endpoints
    path("groups/clients/", views.get_group_clients, name="group-clients"),
    path("groups/sync/", views.sync_all_groups, name="sync-groups"),
    # Student endpoints
    path("students/sync/", views.sync_students_with_groups, name="sync-students"),
    path("clients/detail/", views.get_client_detail, name="client-detail"),
    # Resume endpoints
    path("resumes/client/", views.ResumeListView.as_view(), name="client-resumes"),
    path("resumes/<int:resume_id>/", views.ResumeDetailView.as_view(), name="resume-detail"),
    path("resumes/<int:resume_id>/verify/", views.VerifyResumeView.as_view(), name="verify-resume"),
    path("resumes/unverified/", views.UnverifiedResumesView.as_view(), name="unverified-resumes"),
    path("resumes/", views.create_resume, name="create-resume"),
    path("resumes/<int:resume_id>/", views.delete_resume, name="delete-resume"),
    # Review endpoints
    path("reviews/<str:student_crm_id>/", views.ParentReviewsView.as_view(), name="parent-reviews"),
]
