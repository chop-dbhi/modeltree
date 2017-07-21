from django.db import models


class OtherModel(models.Model):
    pass


class Target(models.Model):
    other_model = models.OneToOneField(OtherModel, related_name="other_model")
    m2m = models.ManyToManyField(OtherModel, related_name="other_model_m2m")
    fk = models.ForeignKey(OtherModel, related_name="other_model_fk")


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
