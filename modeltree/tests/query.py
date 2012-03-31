from django.test import TestCase
from modeltree.tests.models import Employee

__all__ = ('ModelTreeQuerySetTestCase',)

class ModelTreeQuerySetTestCase(TestCase):

    def test_filter(self):
        qs = Employee.branches.filter(title__salary__lt=50000)
        self.assertEqual(str(qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") WHERE "tests_title"."salary" < 50000 ')

    def test_exclude(self):
        qs = Employee.branches.exclude(title__salary__lt=50000)
        self.assertEqual(str(qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") WHERE NOT ("tests_title"."salary" < 50000 )')

