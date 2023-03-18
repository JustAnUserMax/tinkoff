from __future__ import unicode_literals

from django.conf.urls import url

from .views import Notification

urlpatterns = [
    url(r'^notification/', Notification.as_view(), name='notification'),
]
