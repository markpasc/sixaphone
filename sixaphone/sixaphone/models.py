from django.db import models

class Tag(models.Model):
    tag = models.CharField(max_length=50)  # tag text
    asset = models.CharField(max_length=30)  # xid

    by = models.CharField(max_length=30)  # xid
    by_name = models.CharField(max_length=50)  # display name
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('tag', 'asset'),)
