from django.urls import path
from . import views

urlpatterns = [
    path('', views.objetdefectueux_list, name='objetdefectueux_list'),
    path('create/', views.objetdefectueux_create, name='objetdefectueux_create'),
    path('<int:pk>/', views.objetdefectueux_detail, name='objetdefectueux_detail'),
    path('<int:pk>/edit/', views.objetdefectueux_edit, name='objetdefectueux_edit'),
    path('<int:pk>/delete/', views.objetdefectueux_delete, name='objetdefectueux_delete'),
    path('<int:pk>/restore/', views.objetdefectueux_restore, name='objetdefectueux_restore'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('logs/', views.activity_log, name='activity_log'),
    path('signup/', views.signup_view, name='signup'),
    path('object/<int:pk>/analyze/', views.analyze_image, name='analyze_image'),
    path('object/<int:pk>/ai-analysis/', views.ai_analysis_view, name='ai_analysis'),
    path('object/<int:pk>/clear-analysis/', views.clear_analysis_history, name='clear_analysis_history'),
    path('object/<int:pk>/yolo-analysis/', views.yolo_analysis_view, name='yolo_analysis'),
    path('object/<int:pk>/basic-analysis/', views.basic_analysis_view, name='basic_analysis'),
]
