from django.shortcuts import render,redirect,get_object_or_404
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
# Create your views here.
from .models import WildlifeDetection
import math
import base64
from datetime import datetime
from django.core.files.base import ContentFile

ANIMAL_CLASSES   = {"Elephant", "Lion", "Tiger", "Bear", "Wild Boar"}
ALERT_RADIUS_KM  = 10
 
 
# ── Helpers ─────────────────────────────────────────────────────────────────
 
def _distance_km(lat1, lon1, lat2, lon2):
    
    R  = 6371.0
    p1 = math.radians(float(lat1))
    p2 = math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lon2) - float(lon1))
    a  = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
 
 
def _filter_nearby(queryset, lat, lon, email_field="email"):
    
    results = []
    for obj in queryset:
        if obj.latitude and obj.longitude:
            if _distance_km(lat, lon, obj.latitude, obj.longitude) <= ALERT_RADIUS_KM:
                results.append(getattr(obj, email_field))
    return results
 
 
def _email_body(animal_name, confidence, address, lat, lon, detected_at):
    maps = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "N/A"
    dt   = detected_at.strftime("%Y-%m-%d %H:%M:%S") if detected_at else "N/A"
    return (
        f"WILDLIFE DETECTION ALERT\n"
        f"{'─' * 40}\n\n"
        f"Animal    : {animal_name}\n"
        f"Confidence: {confidence}%\n"
        f"Date/Time : {dt}\n"
        f"Location  : {address or 'Unknown'}\n"
        f"Map Link  : {maps}\n\n"
        f"A {animal_name} was detected within {ALERT_RADIUS_KM} km of your location.\n"
        f"Please take immediate precautionary action.\n\n"
        f"— Wildlife Detection System"
    )
 
 
# ── Views ────────────────────────────────────────────────────────────────────
 
def detection_view(request):
    return render(request, "detection.html")
 
 
def ping_server(request):
    return JsonResponse({"status": "ok"})
 
 
@csrf_exempt
# def send_alert_email(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST only"}, status=405)
 
#     try:
#         data = json.loads(request.body)
#     except (json.JSONDecodeError, AttributeError):
#         return JsonResponse({"error": "Invalid JSON"}, status=400)
 
#     animal        = data.get("detectedClass", "").strip()
#     confidence    = data.get("confidence", "N/A")
#     lat           = data.get("latitude")
#     lon           = data.get("longitude")
#     address       = data.get("locationAddress", "")
#     image_url     = data.get("imageDataUrl", "")
 
#     if not animal:
#         return JsonResponse({"error": "detectedClass required"}, status=400)
#     if animal not in ANIMAL_CLASSES:
#         return JsonResponse({"error": f"'{animal}' not an alert class"}, status=400)
 
#     # ── Save detection record ─────────────────────────────
#     detection = WildlifeDetection(
#         animal_name=animal,
#         confidence=float(confidence) if confidence != "N/A" else 0.0,
#         latitude=lat,
#         longitude=lon,
#         location_address=address,
#     )
 
#     if image_url and image_url.startswith("data:image"):
#         try:
#             _, b64 = image_url.split(",", 1)
#             fname  = f"{animal}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
#             detection.animal_image.save(fname, ContentFile(base64.b64decode(b64)), save=False)
#         except Exception:
#             pass
 
#     detection.save()
 
#     # ── Collect nearby email addresses ────────────────────
#     emails = []
#     if lat and lon:
#         emails += _filter_nearby(Userdb.objects.all(),                          lat, lon, "email")
#         emails += _filter_nearby(ForestOfficer.objects.filter(status=True),     lat, lon, "email")
#         emails += _filter_nearby(WildlifeProtectionTeam.objects.filter(status=True), lat, lon, "contact_email")
#     else:
#         emails = list(getattr(settings, "ALERT_EMAIL_RECIPIENTS", []))
 
#     # ── Send emails ───────────────────────────────────────
#     subject = f"⚠️ Wildlife Alert — {animal} Detected!"
#     body    = _email_body(animal, confidence, address, lat, lon, detection.detected_at)
#     sent    = 0
#     errors  = []
 
#     for email in emails:
#         try:
#             send_mail(subject, body, settings.EMAIL_HOST_USER, [email], fail_silently=False)
#             sent += 1
#         except Exception as e:
#             errors.append(f"{email}: {e}")
 
#     return JsonResponse({
#         "success":      True,
#         "detectedClass": animal,
#         "confidence":   confidence,
#         "detectionId":  detection.id,
#         "emailsSent":   sent,
#         "errors":       errors,
#     })

def send_alert_email(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # ── Parse request body ────────────────────────────────
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    animal     = data.get("detectedClass", "").strip()
    confidence = data.get("confidence", "N/A")
    lat        = data.get("latitude")
    lon        = data.get("longitude")
    address    = data.get("locationAddress", "")
    image_url  = data.get("imageDataUrl", "")

    if not animal:
        return JsonResponse({"error": "detectedClass required"}, status=400)
    if animal not in ANIMAL_CLASSES:
        return JsonResponse({"error": f"'{animal}' not an alert class"}, status=400)

    # ── Save detection record ─────────────────────────────
    try:
        detection = WildlifeDetection(
            animal_name=animal,
            confidence=float(confidence) if confidence != "N/A" else 0.0,
            latitude=lat,
            longitude=lon,
            location_address=address,
        )

        if image_url and image_url.startswith("data:image"):
            try:
                _, b64 = image_url.split(",", 1)
                fname  = f"{animal}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                detection.animal_image.save(
                    fname, ContentFile(base64.b64decode(b64)), save=False
                )
            except (ValueError, base64.binascii.Error) as img_err:
                # Log image error but continue saving the detection
                print(f"[WARNING] Failed to decode/save image: {img_err}")

        detection.save()

    except Exception as db_err:
        return JsonResponse(
            {"error": f"Failed to save detection record: {str(db_err)}"}, status=500
        )

    # ── Collect nearby email addresses ────────────────────
    try:
        emails = []
        if lat and lon:
            emails += _filter_nearby(Userdb.objects.all(),                               lat, lon, "email")
            emails += _filter_nearby(ForestOfficer.objects.filter(status=True),          lat, lon, "email")
            emails += _filter_nearby(WildlifeProtectionTeam.objects.filter(status=True), lat, lon, "contact_email")
        else:
            emails = list(getattr(settings, "ALERT_EMAIL_RECIPIENTS", []))

    except Exception as filter_err:
        return JsonResponse(
            {"error": f"Failed to fetch recipient list: {str(filter_err)}"}, status=500
        )

    # ── Send emails ───────────────────────────────────────
    subject = f"⚠️ Wildlife Alert — {animal} Detected!"
    body    = _email_body(animal, confidence, address, lat, lon, detection.detected_at)
    sent    = 0
    errors  = []

    for email in emails:
        try:
            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            sent += 1
        except Exception as mail_err:
            errors.append(f"{email}: {mail_err}")

    return JsonResponse({
        "success":       True,
        "detectedClass": animal,
        "confidence":    confidence,
        "detectionId":   detection.id,
        "emailsSent":    sent,
        "errors":        errors,
    })



from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import Userdb, ForestOfficer, WildlifeProtectionTeam, SOSReport
from django.utils import timezone
import math
from django.views.decorators.http import require_POST

def index(request):
    return render(request, 'index.html')

def logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')

# ==================== User Views ====================

def user_register(request):
    if request.method == 'POST':
        name         = request.POST.get('name', '').strip()
        email        = request.POST.get('email', '').strip()
        phone        = request.POST.get('phone', '').strip()
        gender       = request.POST.get('gender', '').strip()
        location     = request.POST.get('location', '').strip()   # human-readable address
        lat_raw      = request.POST.get('latitude', '').strip()
        lng_raw      = request.POST.get('longitude', '').strip()
        accuracy_raw = request.POST.get('location_accuracy', '').strip()
        password     = request.POST.get('password', '')
        confirm      = request.POST.get('confirm_password', '')
        profile      = request.FILES.get('profile_image')
 
        # ── Required field check ─────────────────────────────────────────────────
        if not all([name, email, phone, gender, location, password, confirm]):
            messages.error(request, 'All fields are required.')
            return render(request, 'user_register.html', {'form_data': request.POST})
 
        # ── Password checks ──────────────────────────────────────────────────────
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'user_register.html', {'form_data': request.POST})
 
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'user_register.html', {'form_data': request.POST})
 
        # ── Unique email check ───────────────────────────────────────────────────
        if Userdb.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'user_register.html', {'form_data': request.POST})
 
        # ── Phone validation (model uses IntegerField) ───────────────────────────
        # Strip any spaces or dashes before parsing
        phone_digits = phone.replace(' ', '').replace('-', '')
        try:
            phone_int = int(phone_digits)
        except ValueError:
            messages.error(request, 'Phone number must contain only digits.')
            return render(request, 'user_register.html', {'form_data': request.POST})
 
        # ── Parse optional lat / lng / accuracy ──────────────────────────────────
        latitude  = None
        longitude = None
        accuracy  = None
 
        try:
            latitude = float(lat_raw) if lat_raw else None
        except ValueError:
            pass
 
        try:
            longitude = float(lng_raw) if lng_raw else None
        except ValueError:
            pass
 
        try:
            accuracy = float(accuracy_raw) if accuracy_raw else None
        except ValueError:
            pass
 
        # ── Save ─────────────────────────────────────────────────────────────────
        user = Userdb(
            name              = name,
            email             = email,
            phone             = phone_int,
            gender            = gender,
            location_address  = location,   # ← correct model field
            latitude          = latitude,   # ← correct model field
            longitude         = longitude,  # ← correct model field
            location_accuracy = accuracy,   # ← correct model field
            password          = make_password(password),
        )
 
        if profile:
            user.profile_image = profile
 
        user.save()
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('user_login')
 
    return render(request, 'user_register.html')

def user_login(request):
    
    if request.session.get('user_id'):
        return redirect('user_login')   

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        
        if not email or not password:
            messages.error(request, 'Both email and password are required.')
            return render(request, 'user_login.html', {'form_data': request.POST})

        
        try:
            user = Userdb.objects.get(email=email)
        except Userdb.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
            return render(request, 'user_login.html', {'form_data': request.POST})

        
        if not check_password(password, user.password):
            messages.error(request, 'Incorrect password. Please try again.')
            return render(request, 'user_login.html', {'form_data': request.POST})

        
        request.session['user_id']   = user.id
        request.session['user_name'] = user.name
        request.session['user_email']= user.email

        messages.success(request, f'Welcome back, {user.name}!')
        return redirect('user_home')  

    return render(request, 'user_login.html')

def user_home(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
    user = Userdb.objects.get(id=request.session.get('user_id'))
    return render(request, 'user_home.html', {'user': user})

def user_profile(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
    user = Userdb.objects.get(id=request.session.get('user_id'))
    return render(request, 'user_profile.html', {'user': user})
 
 
def user_edit_profile(request, user_id):
    if not request.session.get('user_id'):
        return redirect('user_login')
    user = Userdb.objects.get(id=user_id)
    if request.method == 'POST':
        user.name     = request.POST.get('name', user.name)
        user.email    = request.POST.get('email', user.email)
        user.phone    = request.POST.get('phone', user.phone)
        user.gender   = request.POST.get('gender', user.gender)
        user.location_address = request.POST.get('location', user.location_address)
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        user.save()
        return redirect('user_profile')
    return render(request, 'user_edit_profile.html', {'user': user})


def sos_report(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
    user = Userdb.objects.get(id=request.session.get('user_id'))

    if request.method == "POST":
        # ── Collect form data ──────────────────────────────────────────────
        reporter_name  = request.POST.get("reporter_name", "").strip()
        reporter_email = request.POST.get("reporter_email", "").strip()
        reporter_phone = request.POST.get("reporter_phone", "").strip()
        animal_name    = request.POST.get("animal_name", "").strip()
        description    = request.POST.get("description", "").strip()
        severity       = request.POST.get("severity", "high")
        latitude       = request.POST.get("latitude") or None
        longitude      = request.POST.get("longitude") or None
        location_address  = request.POST.get("location_address", "").strip()
        location_accuracy = request.POST.get("location_accuracy") or None

        # ── Basic validation ───────────────────────────────────────────────
        errors = []
        if not animal_name:
            errors.append("Animal name is required.")
        if not description:
            errors.append("Description is required.")
        if severity not in ("critical", "high", "medium", "low"):
            severity = "high"

        if errors:
            return render(request, "sos_report.html", {
                "errors": errors,
                "form_data": request.POST,
                "user": user,
                "today": timezone.now(),
            })

        # ── Save ───────────────────────────────────────────────────────────
        SOSReport.objects.create(
            reporter_name=reporter_name,
            reporter_email=reporter_email,
            reporter_phone=reporter_phone,
            animal_name=animal_name,
            description=description,
            severity=severity,
            latitude=latitude,
            longitude=longitude,
            location_address=location_address,
            location_accuracy=float(location_accuracy) if location_accuracy else None,
        )

        messages.success(request, "SOS report submitted successfully. Authorities have been notified.")
        return redirect("sos_success")   # map this URL name in urls.py

    # ── GET ────────────────────────────────────────────────────────────────
    return render(request, "sos_report.html", {
        "user": user,
        "today": timezone.now(),
    })


def sos_success(request):
    
    return render(request, "sos_success.html", {
        "today": timezone.now(),
    })

def user_danger_zone(request):
 
    # Group detections by exact lat/lon pair, count occurrences
    grouped = (
        WildlifeDetection.objects
        .filter(latitude__isnull=False, longitude__isnull=False)
        .values("latitude", "longitude", "location_address")
        .annotate(detection_count=Count("id"))
        .order_by("-detection_count")
    )
 
    zones = []
    for g in grouped:
        count = g["detection_count"]
        lat   = float(g["latitude"])
        lon   = float(g["longitude"])
        addr  = g["location_address"] or f"{lat:.4f}, {lon:.4f}"
 
        # Determine severity
        if count >= 5:
            severity = "critical"
        elif count >= 2:
            severity = "danger"
        else:
            severity = "safe"          # single detection — shown but not a danger zone
 
        # Most recent detection & animals at this spot
        detections_here = WildlifeDetection.objects.filter(
            latitude=g["latitude"], longitude=g["longitude"]
        ).order_by("-detected_at")
 
        animals = list(
            detections_here.values_list("animal_name", flat=True).distinct()
        )
        latest = detections_here.first()
 
        zones.append({
            "lat":            lat,
            "lon":            lon,
            "address":        addr,
            "count":          count,
            "severity":       severity,
            "is_danger_zone": count >= 2,
            "animals":        animals,
            "latest_at":      latest.detected_at if latest else None,
            "latest_image":   latest.animal_image.url if latest and latest.animal_image else None,
        })
 
    # Summary stats
    total_zones    = len([z for z in zones if z["is_danger_zone"]])
    critical_zones = len([z for z in zones if z["severity"] == "critical"])
    total_detections = WildlifeDetection.objects.count()
 
    context = {
        "zones":            zones,
        "zones_json":       _zones_to_json(zones),
        "total_zones":      total_zones,
        "critical_zones":   critical_zones,
        "total_detections": total_detections,
    }
    return render(request, "user_danger_zone.html", context)

from django.db.models import Count
 
def _zones_to_json(zones):
    
    safe = []
    for z in zones:
        safe.append({
            "lat":       z["lat"],
            "lon":       z["lon"],
            "address":   z["address"],
            "count":     z["count"],
            "severity":  z["severity"],
            "is_danger": z["is_danger_zone"],
            "animals":   z["animals"],
            "latest_at": z["latest_at"].strftime("%Y-%m-%d %H:%M") if z["latest_at"] else "—",
            "image":     z["latest_image"] or "",
        })
    return json.dumps(safe)

def user_report(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
    user = Userdb.objects.get(id=request.session.get('user_id'))
    reports = SOSReport.objects.filter(reporter_email=user.email)
 
    return render(request, 'user_report.html', {'reports': reports, 'user': user})

def haversine_distance(lat1, lon1, lat2, lon2):
    
    R = 6371  # Earth's radius in km
 
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
 
    dlat = lat2 - lat1
    dlon = lon2 - lon1
 
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
 
    return R * c
 
 
def user_alerts_list(request):
    if not request.session.get('user_id'):
        return redirect('user_login')
 
    user = Userdb.objects.get(id=request.session.get('user_id'))
 
    search_query = request.GET.get('q', '').strip()
 
    all_detections = WildlifeDetection.objects.all()
 
    # Filter by search query if provided
    if search_query:
        all_detections = all_detections.filter(animal_name__icontains=search_query)
 
    nearby_alerts = []
    out_of_range_alerts = []
 
    for detection in all_detections:
        distance = None
        is_nearby = False
 
        # Calculate distance if both user and detection have coordinates
        if (user.latitude and user.longitude and
                detection.latitude and detection.longitude):
            distance = haversine_distance(
                user.latitude, user.longitude,
                detection.latitude, detection.longitude
            )
            is_nearby = distance <= 10.0  # 10 km radius
        else:
            # If coordinates unavailable, include in nearby by default
            is_nearby = True
 
        alert_data = {
            'detection': detection,
            'distance': round(distance, 2) if distance is not None else None,
            'is_nearby': is_nearby,
        }
 
        if is_nearby:
            nearby_alerts.append(alert_data)
        else:
            out_of_range_alerts.append(alert_data)
 
    # Sort nearby alerts by distance (closest first), None distances go last
    nearby_alerts.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
 
    context = {
        'user': user,
        'nearby_alerts': nearby_alerts,
        'total_nearby': len(nearby_alerts),
        'search_query': search_query,
        'user_lat': float(user.latitude) if user.latitude else None,
        'user_lng': float(user.longitude) if user.longitude else None,
    }
 
    return render(request, 'user_alerts_list.html', context)

# ==================== Forest Officer Views ====================

def officer_register(request):
    if request.method == 'POST':
        name            = request.POST.get('name', '').strip()
        officer_id      = request.POST.get('officer_id', '').strip()
        email           = request.POST.get('email', '').strip()
        phone           = request.POST.get('phone', '').strip()
        designation     = request.POST.get('designation', '').strip()
        forest_range    = request.POST.get('forest_range', '').strip()
        office_location = request.POST.get('office_location', '').strip()  # human-readable address
        lat_raw         = request.POST.get('latitude', '').strip()
        lng_raw         = request.POST.get('longitude', '').strip()
        accuracy_raw    = request.POST.get('location_accuracy', '').strip()
        password        = request.POST.get('password', '')
        confirm         = request.POST.get('confirm_password', '')
        profile         = request.FILES.get('profile_image')
 
        # ── Validation ──────────────────────────────────────────────────────────
        if not all([name, officer_id, email, phone, designation, forest_range,
                    office_location, password, confirm]):
            messages.error(request, 'All fields are required.')
            return render(request, 'officer_register.html', {'form_data': request.POST})
 
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'officer_register.html', {'form_data': request.POST})
 
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'officer_register.html', {'form_data': request.POST})
 
        if ForestOfficer.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'officer_register.html', {'form_data': request.POST})
 
        if ForestOfficer.objects.filter(officer_id=officer_id).exists():
            messages.error(request, 'An account with this Officer ID already exists.')
            return render(request, 'officer_register.html', {'form_data': request.POST})
 
        # ── Parse optional lat/lng/accuracy ─────────────────────────────────────
        latitude  = None
        longitude = None
        accuracy  = None
 
        try:
            latitude = float(lat_raw) if lat_raw else None
        except ValueError:
            pass
 
        try:
            longitude = float(lng_raw) if lng_raw else None
        except ValueError:
            pass
 
        try:
            accuracy = float(accuracy_raw) if accuracy_raw else None
        except ValueError:
            pass
 
        # ── Save ─────────────────────────────────────────────────────────────────
        officer = ForestOfficer(
            name              = name,
            officer_id        = officer_id,
            email             = email,
            phone             = phone,
            designation       = designation,
            forest_range      = forest_range,
            location_address  = office_location,   
            latitude          = latitude,           
            longitude         = longitude,          
            location_accuracy = accuracy,           
            password          = make_password(password),
        )
 
        if profile:
            officer.profile_image = profile
 
        officer.save()
        messages.success(request, 'Officer account created successfully! Please log in.')
        return redirect('officer_login')
 
    return render(request, 'officer_register.html')

def officer_login(request):
    if request.session.get('officer_id'):
        return redirect('officer_home')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Both email and password are required.')
            return render(request, 'officer_login.html', {'form_data': request.POST})

        try:
            officer = ForestOfficer.objects.get(email=email)
        except ForestOfficer.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
            return render(request, 'officer_login.html', {'form_data': request.POST})

        if not officer.status:
            messages.error(request, 'Your account has been deactivated. Please contact admin.')
            return render(request, 'officer_login.html', {'form_data': request.POST})

        if not check_password(password, officer.password):
            messages.error(request, 'Incorrect password. Please try again.')
            return render(request, 'officer_login.html', {'form_data': request.POST})

        request.session['officer_id']          = officer.id
        request.session['officer_name']        = officer.name
        request.session['officer_email']       = officer.email
        request.session['officer_designation'] = officer.designation

        messages.success(request, f'Welcome back, Officer {officer.name}!')
        return redirect('officer_home')

    return render(request, 'officer_login.html')

def officer_home(request):
    if not request.session.get('officer_id'):
        return redirect('officer_login')
    officer = ForestOfficer.objects.get(id=request.session.get('officer_id'))
    return render(request, 'officer_home.html', {'officer': officer})

def officer_profile(request):
    if not request.session.get('officer_id'):
        return redirect('officer_login')
    officer = ForestOfficer.objects.get(id=request.session.get('officer_id'))
    return render(request, 'officer_profile.html', {'officer': officer})
 
 
def officer_edit_profile(request, officer_id):
    if not request.session.get('officer_id'):
        return redirect('officer_login')
    # Ensure officer can only edit their own profile
    if request.session.get('officer_id') != officer_id:
        return redirect('officer_home')
    officer = ForestOfficer.objects.get(id=officer_id)
    if request.method == 'POST':
        officer.name             = request.POST.get('name', officer.name)
        officer.password            = request.POST.get('password', officer.password)
        officer.phone            = request.POST.get('phone', officer.phone)
        officer.designation      = request.POST.get('designation', officer.designation)
        officer.forest_range     = request.POST.get('forest_range', officer.forest_range)
        officer.location_address  = request.POST.get('office_location', officer.location_address)
        if 'profile_image' in request.FILES:
            officer.profile_image = request.FILES['profile_image']
        officer.save()
        return redirect('officer_profile')
    return render(request, 'officer_edit_profile.html', {'officer': officer})

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lam = math.radians(float(lon2) - float(lon1))
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def officer_sos_report_list(request):
    
    officer_id = request.session.get("officer_id")
    officer = None
    nearby_reports = []
    error_msg = None
 
    status_filter = request.GET.get("status", "")  # optional filter
 
    STATUS_CHOICES = SOSReport.STATUS_CHOICES
    SEVERITY_CHOICES = SOSReport.SEVERITY_CHOICES
 
    if officer_id:
        try:
            officer = ForestOfficer.objects.get(id=officer_id)
        except ForestOfficer.DoesNotExist:
            error_msg = "Officer account not found."
 
    if officer and officer.latitude and officer.longitude:
        # Fetch all reports ordered newest first
        qs = SOSReport.objects.all().order_by("-created_at")
 
        if status_filter and status_filter in dict(STATUS_CHOICES):
            qs = qs.filter(status=status_filter)
 
        # Filter by 10 km radius using haversine
        for report in qs:
            if report.latitude and report.longitude:
                dist = haversine_km(
                    officer.latitude, officer.longitude,
                    report.latitude, report.longitude
                )
                if dist <= 10:
                    report.distance_km = round(dist, 2)
                    nearby_reports.append(report)
            else:
                # Include reports without coordinates (can't compute distance)
                report.distance_km = None
                nearby_reports.append(report)
 
        # Sort: reports with distance first (closest), then no-coords at end
        nearby_reports.sort(key=lambda r: (r.distance_km is None, r.distance_km or 9999))
 
    elif officer and not (officer.latitude and officer.longitude):
        error_msg = "Your location is not set. Please update your profile with coordinates."
 
    # Counts for summary bar
    all_nearby_qs = nearby_reports  # already filtered list
    counts = {
        "total":     len(all_nearby_qs),
        "pending":   sum(1 for r in all_nearby_qs if r.status == "pending"),
        "reviewing": sum(1 for r in all_nearby_qs if r.status == "reviewing"),
        "resolved":  sum(1 for r in all_nearby_qs if r.status == "resolved"),
        "critical":  sum(1 for r in all_nearby_qs if r.severity == "critical"),
    }
 
    return render(request, "officer_sos_report_list.html", {
        "officer":        officer,
        "reports":        nearby_reports,
        "counts":         counts,
        "status_filter":  status_filter,
        "status_choices": STATUS_CHOICES,
        "error_msg":      error_msg,
    })

@csrf_exempt
def officer_sos_update_status(request, report_id):
    
    if request.method not in ("POST", "GET"):
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)
 
    report = get_object_or_404(SOSReport, id=report_id)
 
    # Support both POST body and GET query param
    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()
    else:
        new_status = request.GET.get("status", "").strip()
 
    if not new_status:
        return JsonResponse({"success": False, "error": "No status provided."}, status=400)
 
    valid_statuses = [s[0] for s in SOSReport.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({"success": False, "error": "Invalid status value."}, status=400)
 
    report.status = new_status
    report.save(update_fields=["status"])
 
    return JsonResponse({
        "success":        True,
        "report_id":      report.id,
        "status":         report.status,
        "status_display": report.get_status_display(),
    })

def _zones_to_json(zones):
    safe = []
    for z in zones:
        safe.append({
            "lat":       z["lat"],
            "lon":       z["lon"],
            "address":   z["address"],
            "count":     z["count"],
            "severity":  z["severity"],
            "is_danger": z["is_danger_zone"],
            "animals":   z["animals"],
            "latest_at": z["latest_at"].strftime("%Y-%m-%d %H:%M") if z["latest_at"] else "—",
            "image":     z["latest_image"] or "",
        })
    return json.dumps(safe)
 
 
def officer_danger_zone(request):
    if not request.session.get('officer_id'):
        return redirect('officer_login')
 
    officer = ForestOfficer.objects.get(id=request.session.get('officer_id'))

    grouped = (
        WildlifeDetection.objects
        .filter(latitude__isnull=False, longitude__isnull=False)
        .values("latitude", "longitude", "location_address")
        .annotate(detection_count=Count("id"))
        .order_by("-detection_count")
    )
 
    zones = []
    for g in grouped:
        count = g["detection_count"]
        lat   = float(g["latitude"])
        lon   = float(g["longitude"])
        addr  = g["location_address"] or f"{lat:.4f}, {lon:.4f}"
 
        # Determine severity
        if count >= 5:
            severity = "critical"
        elif count >= 2:
            severity = "danger"
        else:
            severity = "safe"   # single detection — shown but not a danger zone
 
        # Most recent detection & animals at this spot
        detections_here = WildlifeDetection.objects.filter(
            latitude=g["latitude"], longitude=g["longitude"]
        ).order_by("-detected_at")
 
        animals = list(
            detections_here.values_list("animal_name", flat=True).distinct()
        )
        latest = detections_here.first()
 
        zones.append({
            "lat":            lat,
            "lon":            lon,
            "address":        addr,
            "count":          count,
            "severity":       severity,
            "is_danger_zone": count >= 2,
            "animals":        animals,
            "latest_at":      latest.detected_at if latest else None,
            "latest_image":   latest.animal_image.url if latest and latest.animal_image else None,
        })
 
    # Summary stats
    total_zones      = len([z for z in zones if z["is_danger_zone"]])
    critical_zones   = len([z for z in zones if z["severity"] == "critical"])
    danger_zones     = len([z for z in zones if z["severity"] == "danger"])
    safe_zones       = len([z for z in zones if z["severity"] == "safe"])
    total_detections = WildlifeDetection.objects.count()
 
    context = {
        "officer":  officer,
        "zones":            zones,
        "zones_json":       _zones_to_json(zones),
        "total_zones":      total_zones,
        "critical_zones":   critical_zones,
        "danger_zones":     danger_zones,
        "safe_zones":       safe_zones,
        "total_detections": total_detections,
    }
    return render(request, "officer_danger_zone.html", context)

def officer_alerts_list(request):
    if not request.session.get('officer_id'):
        return redirect('officer_login')
 
    officer = ForestOfficer.objects.get(id=request.session.get('officer_id'))
 
    search_query = request.GET.get('q', '').strip()
    filter_confidence = request.GET.get('conf', 'all')   # all | high | mid | low
 
    detections = WildlifeDetection.objects.all()
 
    if search_query:
        detections = detections.filter(animal_name__icontains=search_query)
 
    # Confidence filter
    if filter_confidence == 'high':
        detections = detections.filter(confidence__gte=75)
    elif filter_confidence == 'mid':
        detections = detections.filter(confidence__gte=45, confidence__lt=75)
    elif filter_confidence == 'low':
        detections = detections.filter(confidence__lt=45)
 
    nearby_alerts = []
 
    for detection in detections:
        distance = None
        is_nearby = False
 
        if (officer.latitude and officer.longitude and
                detection.latitude and detection.longitude):
            distance = haversine_distance(
                officer.latitude, officer.longitude,
                detection.latitude, detection.longitude
            )
            is_nearby = distance <= 10.0
        else:
            # Include if coordinates are unavailable
            is_nearby = True
 
        if is_nearby:
            nearby_alerts.append({
                'detection': detection,
                'distance': round(distance, 2) if distance is not None else None,
            })
 
    # Sort by distance (closest first)
    nearby_alerts.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
 
    # Counts for stat cards
    high_conf  = sum(1 for a in nearby_alerts if a['detection'].confidence >= 75)
    mid_conf   = sum(1 for a in nearby_alerts if 45 <= a['detection'].confidence < 75)
    low_conf   = sum(1 for a in nearby_alerts if a['detection'].confidence < 45)
 
    context = {
        'officer': officer,
        'nearby_alerts': nearby_alerts,
        'total_nearby': len(nearby_alerts),
        'high_conf': high_conf,
        'mid_conf': mid_conf,
        'low_conf': low_conf,
        'search_query': search_query,
        'filter_confidence': filter_confidence,
        'officer_lat': float(officer.latitude) if officer.latitude else None,
        'officer_lng': float(officer.longitude) if officer.longitude else None,
    }
 
    return render(request, 'officer_alerts_list.html', context)

# ==================== Wildlife Views ====================

def wildlife_register(request):
    if request.method == 'POST':
        team_name         = request.POST.get('team_name', '').strip()
        team_id           = request.POST.get('team_id', '').strip()
        leader_name       = request.POST.get('leader_name', '').strip()
        contact_email     = request.POST.get('contact_email', '').strip()
        contact_phone     = request.POST.get('contact_phone', '').strip()
        location          = request.POST.get('location', '').strip()      # human-readable address
        lat_raw           = request.POST.get('latitude', '').strip()
        lng_raw           = request.POST.get('longitude', '').strip()
        accuracy_raw      = request.POST.get('location_accuracy', '').strip()
        number_raw        = request.POST.get('number_of_members', '').strip()
        vehicle_number    = request.POST.get('vehicle_number', '').strip()
        password          = request.POST.get('password', '')
        confirm           = request.POST.get('confirm_password', '')
        profile           = request.FILES.get('profile_image')
 
        # ── Required field check ─────────────────────────────────────────────────
        if not all([team_name, team_id, leader_name, contact_email,
                    contact_phone, location, number_raw, password, confirm]):
            messages.error(request, 'All fields are required.')
            return render(request, 'wildlife_register.html', {'form_data': request.POST})
 
        # ── Password checks ──────────────────────────────────────────────────────
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'wildlife_register.html', {'form_data': request.POST})
 
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'wildlife_register.html', {'form_data': request.POST})
 
        # ── Unique checks ────────────────────────────────────────────────────────
        if WildlifeProtectionTeam.objects.filter(contact_email=contact_email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'wildlife_register.html', {'form_data': request.POST})
 
        if WildlifeProtectionTeam.objects.filter(team_id=team_id).exists():
            messages.error(request, 'An account with this Team ID already exists.')
            return render(request, 'wildlife_register.html', {'form_data': request.POST})
 
        # ── Parse number_of_members ──────────────────────────────────────────────
        try:
            number_of_members = int(number_raw)
            if number_of_members < 1:
                raise ValueError
        except ValueError:
            messages.error(request, 'Number of members must be a positive integer.')
            return render(request, 'wildlife_register.html', {'form_data': request.POST})
 
        # ── Parse optional lat / lng / accuracy ──────────────────────────────────
        latitude  = None
        longitude = None
        accuracy  = None
 
        try:
            latitude = float(lat_raw) if lat_raw else None
        except ValueError:
            pass
 
        try:
            longitude = float(lng_raw) if lng_raw else None
        except ValueError:
            pass
 
        try:
            accuracy = float(accuracy_raw) if accuracy_raw else None
        except ValueError:
            pass
 
        # ── Save ─────────────────────────────────────────────────────────────────
        team = WildlifeProtectionTeam(
            team_name         = team_name,
            team_id           = team_id,
            leader_name       = leader_name,
            contact_email     = contact_email,
            contact_phone     = contact_phone,
            location_address  = location,          
            latitude          = latitude,           
            longitude         = longitude,          
            location_accuracy = accuracy,           
            number_of_members = number_of_members,  
            vehicle_number    = vehicle_number or None,
            password          = make_password(password),
        )
 
        if profile:
            team.profile_image = profile
 
        team.save()
        messages.success(request, 'Wildlife Protection Team account created successfully! Please log in.')
        return redirect('wildlife_login')
 
    return render(request, 'wildlife_register.html')


def wildlife_login(request):
    if request.session.get('team_id'):
        return redirect('wildlife_home')

    if request.method == 'POST':
        contact_email = request.POST.get('contact_email', '').strip()
        password      = request.POST.get('password', '')

        if not contact_email or not password:
            messages.error(request, 'Both email and password are required.')
            return render(request, 'wildlife_login.html', {'form_data': request.POST})

        try:
            team = WildlifeProtectionTeam.objects.get(contact_email=contact_email)
        except WildlifeProtectionTeam.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
            return render(request, 'wildlife_login.html', {'form_data': request.POST})

        if not team.status:
            messages.error(request, 'Your account has been deactivated. Please contact admin.')
            return render(request, 'wildlife_login.html', {'form_data': request.POST})

        if not check_password(password, team.password):
            messages.error(request, 'Incorrect password. Please try again.')
            return render(request, 'wildlife_login.html', {'form_data': request.POST})

        request.session['team_id']      = team.id
        request.session['team_name']    = team.team_name
        request.session['team_email']   = team.contact_email
        request.session['leader_name']  = team.leader_name

        messages.success(request, f'Welcome back, {team.team_name}!')
        return redirect('wildlife_home')

    return render(request, 'wildlife_login.html')

def wildlife_home(request):
    if not request.session.get('team_id'):
        return redirect('wildlife_login')  
    team = WildlifeProtectionTeam.objects.get(id=request.session.get('team_id'))
    return render(request, 'wildlife_home.html', {'team': team})

def wildlife_profile(request):
    if not request.session.get('team_id'):
        return redirect('wildlife_login')
    team = WildlifeProtectionTeam.objects.get(id=request.session.get('team_id'))
    return render(request, 'wildlife_profile.html', {'team': team})
 
 
def wildlife_edit_profile(request, team_id):
    if not request.session.get('team_id'):
        return redirect('wildlife_login')
    # Ensure the logged-in team can only edit their own profile
    if request.session.get('team_id') != team_id:
        return redirect('wildlife_home')
    team = WildlifeProtectionTeam.objects.get(id=team_id)
    if request.method == 'POST':
        team.team_name = request.POST.get('team_name', team.team_name)
        team.leader_name = request.POST.get('leader_name', team.leader_name)
        team.contact_email = request.POST.get('contact_email', team.contact_email)
        team.contact_phone = request.POST.get('contact_phone', team.contact_phone)
        team.location_address = request.POST.get('location', team.location_address)
        team.number_of_members = request.POST.get('number_of_members', team.number_of_members)
        team.vehicle_number = request.POST.get('vehicle_number', team.vehicle_number)
        if 'profile_image' in request.FILES:
            team.profile_image = request.FILES['profile_image']
        team.save()
        return redirect('wildlife_profile')
    return render(request, 'wildlife_edit_profile.html', {'team': team})

def wildlife_sos_report_list(request):
    
 
    team_id     = request.session.get("team_id")
    team        = None
    nearby_reports = []
    error_msg   = None
 
    status_filter   = request.GET.get("status", "").strip()
    STATUS_CHOICES  = SOSReport.STATUS_CHOICES
    SEVERITY_CHOICES = SOSReport.SEVERITY_CHOICES
 
    # ── Resolve team from session ──────────────────────────────────────────
    if team_id:
        try:
            team = WildlifeProtectionTeam.objects.get(id=team_id)
        except WildlifeProtectionTeam.DoesNotExist:
            error_msg = "Wildlife team account not found."
 
    # ── Filter reports by 10km radius ─────────────────────────────────────
    if team and team.latitude and team.longitude:
        qs = SOSReport.objects.all().order_by("-created_at")
 
        if status_filter and status_filter in dict(STATUS_CHOICES):
            qs = qs.filter(status=status_filter)
 
        for report in qs:
            if report.latitude and report.longitude:
                dist = haversine_km(
                    team.latitude, team.longitude,
                    report.latitude, report.longitude
                )
                if dist <= 10:
                    report.distance_km = round(dist, 2)
                    nearby_reports.append(report)
            else:
                # No coordinates — include at bottom
                report.distance_km = None
                nearby_reports.append(report)
 
        nearby_reports.sort(key=lambda r: (r.distance_km is None, r.distance_km or 9999))
 
    elif team and not (team.latitude and team.longitude):
        error_msg = "Your team location is not set. Please update your profile with coordinates."
 
    # ── Summary counts ────────────────────────────────────────────────────
    counts = {
        "total":     len(nearby_reports),
        "pending":   sum(1 for r in nearby_reports if r.status == "pending"),
        "reviewing": sum(1 for r in nearby_reports if r.status == "reviewing"),
        "resolved":  sum(1 for r in nearby_reports if r.status == "resolved"),
        "critical":  sum(1 for r in nearby_reports if r.severity == "critical"),
    }
 
    return render(request, "wildlife_sos_report_list.html", {
        "team":           team,
        "reports":        nearby_reports,
        "counts":         counts,
        "status_filter":  status_filter,
        "status_choices": STATUS_CHOICES,
        "error_msg":      error_msg,
    })

def _zones_to_json(zones):
    safe = []
    for z in zones:
        safe.append({
            "lat":       z["lat"],
            "lon":       z["lon"],
            "address":   z["address"],
            "count":     z["count"],
            "severity":  z["severity"],
            "is_danger": z["is_danger_zone"],
            "animals":   z["animals"],
            "latest_at": z["latest_at"].strftime("%Y-%m-%d %H:%M") if z["latest_at"] else "—",
            "image":     z["latest_image"] or "",
        })
    return json.dumps(safe)
 
 
def wildlife_danger_zone(request):
    # Get the logged-in wildlife team from session
    team_id = request.session.get("wildlife_team_id")
    team = WildlifeProtectionTeam.objects.filter(id=team_id).first() if team_id else None
 
    # Group detections by exact lat/lon pair, count occurrences
    grouped = (
        WildlifeDetection.objects
        .filter(latitude__isnull=False, longitude__isnull=False)
        .values("latitude", "longitude", "location_address")
        .annotate(detection_count=Count("id"))
        .order_by("-detection_count")
    )
 
    zones = []
    for g in grouped:
        count = g["detection_count"]
        lat   = float(g["latitude"])
        lon   = float(g["longitude"])
        addr  = g["location_address"] or f"{lat:.4f}, {lon:.4f}"
 
        # Determine severity
        if count >= 5:
            severity = "critical"
        elif count >= 2:
            severity = "danger"
        else:
            severity = "safe"   # single detection — shown but not a danger zone
 
        # Most recent detection & animals at this spot
        detections_here = WildlifeDetection.objects.filter(
            latitude=g["latitude"], longitude=g["longitude"]
        ).order_by("-detected_at")
 
        animals = list(
            detections_here.values_list("animal_name", flat=True).distinct()
        )
        latest = detections_here.first()
 
        zones.append({
            "lat":            lat,
            "lon":            lon,
            "address":        addr,
            "count":          count,
            "severity":       severity,
            "is_danger_zone": count >= 2,
            "animals":        animals,
            "latest_at":      latest.detected_at if latest else None,
            "latest_image":   latest.animal_image.url if latest and latest.animal_image else None,
        })
 
    # Summary stats
    total_zones      = len([z for z in zones if z["is_danger_zone"]])
    critical_zones   = len([z for z in zones if z["severity"] == "critical"])
    danger_zones     = len([z for z in zones if z["severity"] == "danger"])
    safe_zones       = len([z for z in zones if z["severity"] == "safe"])
    total_detections = WildlifeDetection.objects.count()
 
    context = {
        "team":             team,
        "zones":            zones,
        "zones_json":       _zones_to_json(zones),
        "total_zones":      total_zones,
        "critical_zones":   critical_zones,
        "danger_zones":     danger_zones,
        "safe_zones":       safe_zones,
        "total_detections": total_detections,
    }
    return render(request, "wildlife_danger_zone.html", context)

def wildlife_alerts_list(request):
    if not request.session.get('team_id'):
        return redirect('wildlife_login')
 
    team = WildlifeProtectionTeam.objects.get(id=request.session.get('team_id'))
 
    search_query      = request.GET.get('q', '').strip()
    filter_confidence = request.GET.get('conf', 'all')   # all | high | mid | low
 
    detections = WildlifeDetection.objects.all()
 
    if search_query:
        detections = detections.filter(animal_name__icontains=search_query)
 
    if filter_confidence == 'high':
        detections = detections.filter(confidence__gte=75)
    elif filter_confidence == 'mid':
        detections = detections.filter(confidence__gte=45, confidence__lt=75)
    elif filter_confidence == 'low':
        detections = detections.filter(confidence__lt=45)
 
    nearby_alerts = []
 
    for detection in detections:
        distance  = None
        is_nearby = False
 
        if (team.latitude and team.longitude and
                detection.latitude and detection.longitude):
            distance  = haversine_distance(
                team.latitude, team.longitude,
                detection.latitude, detection.longitude
            )
            is_nearby = distance <= 10.0
        else:
            is_nearby = True   # include when coords unavailable
 
        if is_nearby:
            nearby_alerts.append({
                'detection': detection,
                'distance':  round(distance, 2) if distance is not None else None,
            })
 
    # Sort by distance (closest first; None distances go last)
    nearby_alerts.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
 
    # Pre-computed counts for stat cards & topbar dots
    high_conf = sum(1 for a in nearby_alerts if a['detection'].confidence >= 75)
    mid_conf  = sum(1 for a in nearby_alerts if 45 <= a['detection'].confidence < 75)
    low_conf  = sum(1 for a in nearby_alerts if a['detection'].confidence < 45)
 
    context = {
        'team':             team,
        'nearby_alerts':    nearby_alerts,
        'total_nearby':     len(nearby_alerts),
        'high_conf':        high_conf,
        'mid_conf':         mid_conf,
        'low_conf':         low_conf,
        'search_query':     search_query,
        'filter_confidence': filter_confidence,
        'team_lat':         float(team.latitude)  if team.latitude  else None,
        'team_lng':         float(team.longitude) if team.longitude else None,
    }
 
    return render(request, 'wildlife_alerts_list.html', context)

# ==================== Admin Views ====================

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == 'admin' and password == 'admin':
            return redirect('admin_home')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'admin_login.html')

    return render(request, 'admin_login.html')

def admin_home(request):
    total_users_count = Userdb.objects.count()
    total_officers_count = ForestOfficer.objects.count()
    total_wildlife_count = WildlifeProtectionTeam.objects.count()
    emergency_count = SOSReport.objects.count()
    total_alerts_count = WildlifeDetection.objects.count()
    return render(request, 'admin_home.html', {'total_users_count': total_users_count, 'total_officers_count': total_officers_count, 'total_wildlife_count': total_wildlife_count, 'emergency_count': emergency_count, 'total_alerts_count': total_alerts_count})

def user_list(request):
    users = Userdb.objects.all()
    return render(request, 'user_list.html', {'users': users})

def delete_user(request, user_id):
    user = Userdb.objects.get(id=user_id)
    user.delete()
    messages.success(request, 'User deleted successfully')
    return redirect('user_list')

def officer_list(request):
    officers = ForestOfficer.objects.all()
    return render(request, 'officer_list.html', {'officers': officers})

def delete_officer(request, officer_id):

    officer = get_object_or_404(ForestOfficer, id=officer_id)

    officer_name = officer.name 
    officer.delete()

    messages.success(request, f"Officer '{officer_name}' has been permanently deleted.")
    return redirect('officer_list')


def officer_update_status(request, officer_id):

    officer = get_object_or_404(ForestOfficer, id=officer_id)

    officer.status = not officer.status  
    officer.save(update_fields=['status'])

    status_label = "activated" if officer.status else "deactivated"
    messages.success(request, f"Officer '{officer.name}' has been {status_label}.")
    return redirect('officer_list')

def wildlife_list(request):
    teams = WildlifeProtectionTeam.objects.all()
    return render(request, 'wildlife_list.html', {'teams': teams})

def delete_wildlife_team(request, team_id):
    
    team = get_object_or_404(WildlifeProtectionTeam, id=team_id)

    team_name = team.team_name  
    team.delete()

    messages.success(request, f"Wildlife protection team '{team_name}' has been permanently deleted.")
    return redirect('wildlife_list')


def wildlife_team_update_status(request, team_id):
    
    team = get_object_or_404(WildlifeProtectionTeam, id=team_id)

    team.status = not team.status  
    team.save(update_fields=['status'])

    status_label = "activated" if team.status else "deactivated"
    messages.success(request, f"Team '{team.team_name}' has been {status_label}.")
    return redirect('wildlife_list')

def admin_danger_zones(request):
    zones = WildlifeDetection.objects.all()
    return render(request, 'admin_danger_zones.html', {'zones': zones})

def admin_sos_report_list(request):
    sos_reports = SOSReport.objects.all()
    return render(request, 'admin_sos_report_list.html', {'sos_reports': sos_reports})

def admin_all_alerts(request):
    alerts = WildlifeDetection.objects.all()
    return render(request, 'admin_all_alerts.html', {'alerts': alerts})