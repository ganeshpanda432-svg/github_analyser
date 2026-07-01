from django.db import models

# Create your models here.
class RepoAnalysis(models.Model):
    repo_url=models.URLField()
    owner = models.CharField()
    repo_name=models.CharField()
    stars = models.IntegerField(default=0)
    forks = models.IntegerField(default=0)
    language_data = models.JSONField(default=dict) 
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner}/{self.repo_name}"