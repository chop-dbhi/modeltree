from django.db import models


class Target(models.Model):
    pass


class TargetProxy(Target):
    class Meta(object):
        proxy = True


class Root(models.Model):
    standard_path = models.ManyToManyField(Target, related_name='path')
    proxy_path = models.ManyToManyField(TargetProxy, related_name='proxy')
