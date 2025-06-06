import uuid
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta

# ✅ Session Year Model
class SessionYearModel(models.Model):
    id = models.AutoField(primary_key=True)
    session_start_year = models.DateField()
    session_end_year = models.DateField()
    objects = models.Manager()

# ✅ Custom User Model
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    user_type = models.CharField(default=1, choices=USER_TYPE_CHOICES, max_length=10)

# ✅ AdminHOD Model
class AdminHOD(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Staff Model
class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Course Model
class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Subject Model
class Subjects(models.Model):
    id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=255)
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE, default=1)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)  # ✅ References Staffs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Student Model
class Students(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    gender = models.CharField(max_length=50, blank=True, null=True)  # ✅ Allow blank
    profile_pic = models.FileField(upload_to="profile_pics/", blank=True, null=True)  # ✅ Allow blank
    address = models.TextField(blank=True, null=True)  # ✅ Allow blank
    course_id = models.ForeignKey(Courses, on_delete=models.DO_NOTHING, default=1)
    session_year_id = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Attendance Model
class Attendance(models.Model):
    id = models.AutoField(primary_key=True)
    subject_id = models.ForeignKey(Subjects, on_delete=models.DO_NOTHING)
    attendance_date = models.DateField()
    session_year_id = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)  # ✅ Include session year
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Attendance QR Code Model
class AttendanceQRCode(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    session_year = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE, default=1)  # ✅ Added default
    qr_code_image = models.ImageField(upload_to="qr_codes/")
    expiry_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    token = models.CharField(max_length=50, unique=True)  # Unique Token for Attendance
    teacher_latitude = models.FloatField(null=True, blank=True)
    teacher_longitude = models.FloatField(null=True, blank=True)
    allowed_radius = models.FloatField(default=100)  # Radius in meters

# ✅ Attendance Report Model
class AttendanceReport(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.DO_NOTHING)
    attendance_id = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    student_latitude = models.FloatField(null=True, blank=True)
    student_longitude = models.FloatField(null=True, blank=True)
    student_accuracy = models.FloatField(null=True, blank=True)  # Location accuracy in meters
    location_verified = models.BooleanField(default=False)
    verification_details = models.JSONField(null=True, blank=True)  # Store detailed verification results
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Student Result Model
class StudentResult(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    subject_exam_marks = models.FloatField(default=0)
    subject_assignment_marks = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

# ✅ Create Profile for New Users
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    # print(instance.user_type)
    if created:
        if instance.user_type == '1':
            AdminHOD.objects.create(admin=instance)
        if instance.user_type == '2':
            Staffs.objects.create(admin=instance)
        if instance.user_type == '3':
            # Get or create a default course if no course exists
            default_course, _ = Courses.objects.get_or_create(
                id=1,
                defaults={'course_name': 'Default Course'}
            )

            # Get or create a default session year if no session year exists
            today = datetime.now()
            next_year = today + timedelta(days=365)
            default_session, _ = SessionYearModel.objects.get_or_create(
                id=1,
                defaults={
                    'session_start_year': today.date(),
                    'session_end_year': next_year.date()
                }
            )

            Students.objects.create(
                admin=instance,
                course_id=default_course,
                session_year_id=default_session
            )

# ✅ Save Profile for Existing Users
@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "adminhod"):
        instance.adminhod.save()
    if hasattr(instance, "staffs"):
        instance.staffs.save()
    if hasattr(instance, "students"):
        instance.students.save()
