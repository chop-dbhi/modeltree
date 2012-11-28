from django.db import models
from modeltree.managers import ModelTreeManager

class Office(models.Model):
    location = models.CharField(max_length=50)


class Title(models.Model):
    name = models.CharField(max_length=50)
    salary = models.IntegerField()


class Employee(models.Model):
    # Different db_column to ensure the corrent name is used
    first_name = models.CharField(max_length=50, db_column='firstName')
    last_name = models.CharField(max_length=50)
    title = models.ForeignKey(Title)
    office = models.ForeignKey(Office)
    manager = models.ForeignKey('self', null=True, related_name='managed_employees')

    objects = models.Manager()
    branches = ModelTreeManager()


class Project(models.Model):
    name = models.CharField(max_length=50)
    employees = models.ManyToManyField(Employee)
    # Disabled reverse accessor for Employee to Project
    manager = models.ForeignKey(Employee, related_name='+')
    due_date = models.DateField()


class Meeting(models.Model):
    attendees = models.ManyToManyField(Employee)
    project = models.ForeignKey(Project, null=True)
    office = models.ForeignKey(Office)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
