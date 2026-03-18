from django.db import models

# Create your models here.

class Userdb(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.IntegerField()

    gender_choices = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others'),
    ]
    gender = models.CharField(max_length=10, choices=gender_choices)

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_address = models.TextField(blank=True, help_text="Human-readable address if available")
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    profile_image = models.ImageField(upload_to='user_profiles/', null=True, blank=True)

    password = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ForestOfficer(models.Model):
    name = models.CharField(max_length=100)
    officer_id = models.CharField(max_length=50, unique=True)

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)

    designation = models.CharField(max_length=100)
    forest_range = models.CharField(max_length=150)

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_address = models.TextField(blank=True, help_text="Human-readable address if available")
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")

    profile_image = models.ImageField(upload_to='forest_officers/', null=True, blank=True)

    password = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class WildlifeProtectionTeam(models.Model):
    team_name = models.CharField(max_length=150)
    team_id = models.CharField(max_length=50, unique=True)

    leader_name = models.CharField(max_length=100)

    contact_email = models.EmailField(unique=True)
    contact_phone = models.CharField(max_length=15)

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_address = models.TextField(blank=True, help_text="Human-readable address if available")
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")

    number_of_members = models.IntegerField()

    vehicle_number = models.CharField(max_length=50, null=True, blank=True)

    profile_image = models.ImageField(upload_to='wildlife_teams/', null=True, blank=True)

    password = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    status = models.BooleanField(default=False)

    def __str__(self):
        return self.team_name

class SOSReport(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'),
        ('false_alarm', 'False Alarm'),
    ]

    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    # Reporter info (pulled from session, not FK to User to keep it simple)
    reporter_name = models.CharField(max_length=255, blank=True)
    reporter_email = models.CharField(max_length=255, blank=True)
    reporter_phone = models.CharField(max_length=30, blank=True)

    # Animal / incident details
    animal_name = models.CharField(max_length=255, help_text="Name of the animal (e.g. Elephant, Tiger)")
    description = models.TextField(help_text="Describe the emergency situation in detail")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='high')

    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_address = models.TextField(blank=True, help_text="Human-readable address if available")
    location_accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")

    # Meta
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SOS Report'
        verbose_name_plural = 'SOS Reports'

    def __str__(self):
        return f"[{self.severity.upper()}] {self.animal_name} — {self.reporter_name} ({self.created_at.strftime('%d %b %Y %H:%M')})"

class WildlifeDetection(models.Model):
    animal_name     = models.CharField(max_length=100)
    animal_image    = models.ImageField(upload_to="detections/", null=True, blank=True)
    confidence      = models.FloatField()
    latitude        = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude       = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_address = models.TextField(blank=True)
    detected_at     = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-detected_at"]
 
    def __str__(self):
        return f"{self.animal_name} — {self.detected_at:%Y-%m-%d %H:%M:%S}"