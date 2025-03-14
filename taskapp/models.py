from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView


# Create your models here.
class News(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    image = models.ImageField(upload_to="news_images/", blank=True, null=True)
    tags = models.CharField(max_length=255)  # Comma-separated tags
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    def __str__(self):
        return self.title
