from django.contrib import admin
from .models import Userdb, ForestOfficer, WildlifeProtectionTeam, SOSReport, WildlifeDetection
# Register your models here.

admin.site.register(Userdb)
admin.site.register(ForestOfficer)
admin.site.register(WildlifeProtectionTeam)
admin.site.register(WildlifeDetection)
admin.site.register(SOSReport)