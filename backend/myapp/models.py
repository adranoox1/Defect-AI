from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class ObjetDefectueux(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    name = models.CharField(max_length=100, verbose_name="Name")
    inspection_date = models.DateField(verbose_name="Inspection Date")
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Status"
    )
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Defective Object"
        verbose_name_plural = "Defective Objects"

class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Created Object'),
        ('UPDATE', 'Updated Object'),
        ('DELETE', 'Deleted Object'),
        ('RESTORE', 'Restored Object'),
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('VIEW', 'Viewed Object')
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    object_id = models.IntegerField(null=True, blank=True)
    object_name = models.CharField(max_length=255, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.object_name or ''}"

class ImageAnalysis(models.Model):
    ANALYSIS_TYPES = [
        ('YOLO', 'YOLO Analysis'),
        ('BASIC', 'Basic Analysis'),
    ]

    objet_defectueux = models.ForeignKey('ObjetDefectueux', on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='defect_images/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    annotated_image = models.ImageField(
        upload_to='defect_images/annotated/',
        null=True,
        blank=True
    )
    analysis_type = models.CharField(
        max_length=10,
        choices=ANALYSIS_TYPES,
        default='BASIC'
    )
    is_defective = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True)
    detections = models.JSONField(default=dict, blank=True)
    recommendations = models.TextField(blank=True)
    analysis_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-analysis_date']

    def __str__(self):
        return f"Analysis for {self.objet_defectueux} on {self.analysis_date}"

class MonModele(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

