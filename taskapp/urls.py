from django.urls import path
from .auth_views import login_request, verify_otp, resend_otp
from .views import PostCreateView
from . import auth_views, views
from .views import (
    CategoryListView,
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    CommentCreateView,
    HomeView, 
    CategoryPostView,
    PostCreateView,
    CategoryListView
    
)

urlpatterns = [
    # path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    # path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('', HomeView.as_view(), name='index'),
    path('post/<slug:slug>/', PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', CategoryPostView.as_view(), name='category_posts'),
    path('search/', views.search, name='search'),
        # Authentication URLs

    path('login/', login_request, name='signin'),
    
    # path('', views.index, name='index'),
    
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    path('technical/review/<int:post_id>/', views.review_post, name='review_post'),

    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('technical/dashboard/', views.technical_dashboard, name='technical_dashboard'),
    path('create-post/', views.create_post, name='create_post'),
    
    path('categories/', CategoryListView.as_view(), name='category-list'),
    

    path('posts/', PostListView.as_view(), name='post-list'),
    
    # urls.py (after)
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    
    path('logout/', views.logout_view, name='logout'),
    
    path('posts/create/', PostCreateView.as_view(), name='post_create'),

    # path('posts/review/<int:pk>/', PostReviewView.as_view(), name='post_review'),

    # path('posts/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<slug:slug>/update/', PostUpdateView.as_view(), name='post-update'),
    path('posts/<slug:slug>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('posts/<slug:slug>/comments/', CommentCreateView.as_view(), name='comment-create'),
]