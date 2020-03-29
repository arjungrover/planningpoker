from django.db import models


class BaseModel(models.Model):
    """
    This model will store common fields which will be used by all models
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "{} : {}".format(self.created_at, self.updated_at)
