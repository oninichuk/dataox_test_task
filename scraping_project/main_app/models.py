from django.db import models

# Create your models here.
class Article(models.Model):
    url = models.CharField(max_length=2048, unique=True)
    title = models.CharField(max_length=500)
    content = models.TextField()
    author = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    # Additional fields
    subtitle = models.CharField(max_length=700, blank=True, default="")
    tags = models.TextField()
    image_url = models.CharField(max_length=2048, blank=True, default="")
    word_count = models.IntegerField(default=0)
    reading_time = models.CharField(max_length=50, blank=True, default="")
    related_articles = models.TextField()

    def __str__(self):
        return f'{self.published_at.strftime("%Y-%m-%d %H:%M:%S")} {self.title}'

    class Meta:
        indexes = [
            models.Index(name='title_index', fields=['title']),
            models.Index(name='author_index', fields=['author']),
            models.Index(name='published_at_index', fields=['published_at']),
            models.Index(name='scraped_at_index', fields=['scraped_at']),
            models.Index(name='word_count_index', fields=['word_count']),
        ]

