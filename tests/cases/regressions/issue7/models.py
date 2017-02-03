from django.db import models


class A(models.Model):
    study_id = models.CharField(max_length=20,
                                unique=True,
                                db_column='study_id')

    class Meta:
        db_table = 'a'


class B(models.Model):
    study_id = models.ForeignKey('A',
                                 to_field='study_id',
                                 unique=True,
                                 db_column='study_id')

    class Meta:
        db_table = 'b'


class C(models.Model):
    id = models.IntegerField(primary_key=True, db_column='c_id')
    bs = models.ManyToManyField('B', through='CB')

    class Meta:
        db_table = 'c'


class CB(models.Model):
    c = models.ForeignKey('C', db_column='some_c_id')
    sid = models.ForeignKey('B',
                            to_field='study_id',
                            db_column='study_id')

    class Meta:
        db_table = 'cb'
