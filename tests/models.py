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
    manager = models.ForeignKey('self', null=True,
                                related_name='managed_employees')

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


# Router Test Models.. no relation to the above models
# The raw model tree looks like this:
#        A
#       / \                                                       # noqa: W605
#      C   B
#      |  / \                                                     # noqa: W605
#       D    G
#      / \   |                                                    # noqa: W605
#     E   F  |
#      \ / \ |                                                    # noqa: W605
#       J   H
#       |   |
#       K   I

class A(models.Model):
    pass


class B(models.Model):
    a = models.ForeignKey(A)


class C(models.Model):
    a = models.ForeignKey(A)


class D(models.Model):
    b = models.ForeignKey(B)
    c = models.ForeignKey(C)


class E(models.Model):
    d = models.ManyToManyField(D)
    d1 = models.ManyToManyField(D, related_name='e1_set')


class F(models.Model):
    d = models.OneToOneField(D)


class G(models.Model):
    b = models.ForeignKey(B)


class H(models.Model):
    g = models.ForeignKey(G)
    f = models.ForeignKey(F)


class I(models.Model):                                            # noqa: E742
    i = models.ManyToManyField(H)


class J(models.Model):
    f = models.ForeignKey(F)
    e = models.ForeignKey(E)


class K(models.Model):
    j = models.ForeignKey(J)
