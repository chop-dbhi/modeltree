from django.db import models


class OtherModel(models.Model):
    pass


class Target(models.Model):
    other_model = models.OneToOneField(OtherModel)
    m2m = models.ManyToManyField(OtherModel)
    fk = models.ForeignKey(OtherModel)


class TargetProxy(Target):
    class Meta(object):
        proxy = True


class TargetNonProxy(Target):
    pass


class Root(models.Model):
    standard_path = models.ManyToManyField(Target, related_name='path')
    proxy_path = models.ManyToManyField(TargetProxy, related_name='proxy')
    non_proxy_path = models.ManyToManyField(
        TargetNonProxy, related_name='non_proxy')
