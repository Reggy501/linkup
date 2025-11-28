from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html'
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-consistency/', views.update_consistency, name='update_consistency'),
    path('member/<int:pk>/', views.member_detail, name='member_detail'),
    path('create-post/', views.create_post, name='create_post'),
    path('explore/', views.explore, name='explore'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('groups/', views.groups, name='groups'),
    path('create-group/', views.create_group, name='create_group'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('join-group/<int:group_id>/', views.join_group, name='join_group'),
    path('post-in-group/<int:group_id>/', views.post_in_group, name='post_in_group'),
    path('send-message/<int:group_id>/', views.send_message, name='send_message'),
]