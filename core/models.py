from django.db import models


class TimeStampedModel(models.Model):
    """
    Base model for domain entities.

    Main application models should inherit from this class to keep the
    `created_at` and `updated_at` audit fields required by the PRD.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
