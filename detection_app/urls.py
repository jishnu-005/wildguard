from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("logout/", views.logout, name="logout"),

    path("detection/", views.detection_view, name="detection"),
    path("ping-server/", views.ping_server, name="ping_server"),
    path("send-alert-email/", views.send_alert_email, name="send_alert_email"),


    path("user_register/", views.user_register, name="user_register"),
    path("user_login/", views.user_login, name="user_login"),
    path("user_home/", views.user_home, name="user_home"),
    path("user_profile/", views.user_profile, name="user_profile"),
    path("user_edit_profile/<int:user_id>/", views.user_edit_profile, name="user_edit_profile"),
    path("sos_report/", views.sos_report, name="sos_report"),
    path("sos_success/", views.sos_success, name="sos_success"),
    path("user_danger_zone/", views.user_danger_zone, name="user_danger_zone"),
    path("user_report/", views.user_report, name="user_report"),
    path("user_alerts_list/", views.user_alerts_list, name="user_alerts_list"),

    path("officer_register/", views.officer_register, name="officer_register"),
    path("officer_login/", views.officer_login, name="officer_login"),
    path("officer_home/", views.officer_home, name="officer_home"),
    path("officer_profile/", views.officer_profile, name="officer_profile"),
    path("officer_edit_profile/<int:officer_id>/", views.officer_edit_profile, name="officer_edit_profile"),
    path("officer_sos_report_list/", views.officer_sos_report_list, name="officer_sos_report_list"),
    path("officer_sos_update_status/<int:report_id>/", views.officer_sos_update_status, name="officer_sos_update_status"),
    path("officer_danger_zone/", views.officer_danger_zone, name="officer_danger_zone"),
    path("officer_alerts_list/", views.officer_alerts_list, name="officer_alerts_list"),

    path("wildlife_register/", views.wildlife_register, name="wildlife_register"),
    path("wildlife_login/", views.wildlife_login, name="wildlife_login"),
    path("wildlife_home/", views.wildlife_home, name="wildlife_home"),
    path("wildlife_profile/", views.wildlife_profile, name="wildlife_profile"),
    path("wildlife_edit_profile/<int:team_id>/", views.wildlife_edit_profile, name="wildlife_edit_profile"),
    path("wildlife_sos_report_list/", views.wildlife_sos_report_list, name="wildlife_sos_report_list"),
    path("wildlife_danger_zone/", views.wildlife_danger_zone, name="wildlife_danger_zone"),
    path("wildlife_alerts_list/", views.wildlife_alerts_list, name="wildlife_alerts_list"),

    path("admin_login/", views.admin_login, name="admin_login"),
    path("admin_home/", views.admin_home, name="admin_home"),
    path("user_list/", views.user_list, name="user_list"),
    path("officer_list/", views.officer_list, name="officer_list"),
    path("wildlife_list/", views.wildlife_list, name="wildlife_list"),
    path("delete_user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("delete_officer/<int:officer_id>/", views.delete_officer, name="delete_officer"),
    path("officer_update_status/<int:officer_id>/", views.officer_update_status, name="officer_update_status"),
    path("delete_wildlife_team/<int:team_id>/", views.delete_wildlife_team, name="delete_wildlife_team"),
    path("wildlife_team_update_status/<int:team_id>/", views.wildlife_team_update_status, name="wildlife_team_update_status"),
    path("admin_danger_zones/", views.admin_danger_zones, name="admin_danger_zones"),
    path("admin_sos_report_list/", views.admin_sos_report_list, name="admin_sos_report_list"),
    path("admin_all_alerts/", views.admin_all_alerts, name="admin_all_alerts"),
]
