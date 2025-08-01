from django.shortcuts import render

# Create your views here.
from django.core.management import call_command
from rest_framework import viewsets
from .models import Article
from .serializers import ArticleSerializer

def my_own_view_funct(request):
    var1 = 2
    call_command('fetch_articles_aiohttp')
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

