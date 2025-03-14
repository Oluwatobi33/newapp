from django.urls import path
from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    NewsListCreateView,
    NewsDetailDeleteView,
    LikeNewsView,
    DislikeNewsView,
)

urlpatterns = [
    path("", views.index, name="index"),
    path("news/", NewsListCreateView.as_view(), name="news-list-create"),
    path("news/<int:pk>/", NewsDetailDeleteView.as_view(), name="news-detail-delete"),
    path("news/<int:pk>/like/", LikeNewsView.as_view(), name="news-like"),
    path("news/<int:pk>/dislike/", DislikeNewsView.as_view(), name="news-dislike"),
]
# Serve media files during development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
