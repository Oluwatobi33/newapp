from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import News
from .serializers import NewsSerializer
from django.shortcuts import get_object_or_404


# Create your views here.
def index(request):
    return render(request, "index.html")


class NewsListCreateView(generics.ListCreateAPIView):
    queryset = News.objects.all().order_by("-created_at")
    serializer_class = NewsSerializer


class NewsDetailDeleteView(APIView):
    def get(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.views += 1
        news.save()
        serializer = NewsSerializer(news)
        return Response(serializer.data)

    def delete(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.delete()
        return Response({"message": "News deleted successfully!"})


class AllNewsView(APIView):
    def get(self, request):
        news = News.objects.all().order_by("-created_at")
        serializer = NewsSerializer(news, many=True)
        return Response(serializer.data)


class LikeNewsView(APIView):
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.likes += 1
        news.save()
        return Response({"likes": news.likes})

class NewsStatsView(APIView):
    def get(self, request):
        total_news = News.objects.count()
        total_views = sum(news.views for news in News.objects.all())
        total_likes = sum(news.likes for news in News.objects.all())
        total_dislikes = sum(news.dislikes for news in News.objects.all())

        return JsonResponse({
            "total_news": total_news,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_dislikes": total_dislikes
        })
class DislikeNewsView(APIView):
    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.dislikes += 1
        news.save()
        return Response({"dislikes": news.dislikes})
