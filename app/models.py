from django.db import models

# Create your models here.
class Statuses(models.Model):
    message = models.CharField(max_length=999999)
    hometown_name = models.CharField(max_length=200)
    hometown_id = models.BigIntegerField()
