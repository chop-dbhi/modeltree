from django.test import TestCase
from tests import models

__all__ = ('ModelTreeQuerySetTestCase',)

class ModelTreeQuerySetTestCase(TestCase):

    def test_filter(self):
        qs = models.Employee.branches.filter(title__salary__lt=50000)
        self.assertEqual(str(qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") WHERE "tests_title"."salary" < 50000 ')

    def test_exclude(self):
        qs = models.Employee.branches.exclude(title__salary__lt=50000)
        self.assertEqual(str(qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") WHERE NOT ("tests_title"."salary" < 50000 )')

    def test_select(self):
        location = models.Office._meta.get_field_by_name('location')[0]
        salary = models.Title._meta.get_field_by_name('salary')[0]
        name = models.Project._meta.get_field_by_name('name')[0]
        start_time = models.Meeting._meta.get_field_by_name('start_time')[0]

        qs = models.Employee.branches.select(location, salary, name, start_time)
        self.assertEqual(str(qs.query), 'SELECT "tests_employee"."id", "tests_office"."location", "tests_title"."salary", "tests_project"."name", "tests_meeting"."start_time" FROM "tests_employee" INNER JOIN "tests_office" ON ("tests_employee"."office_id" = "tests_office"."id") INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") LEFT OUTER JOIN "tests_project_employees" ON ("tests_employee"."id" = "tests_project_employees"."employee_id") LEFT OUTER JOIN "tests_project" ON ("tests_project_employees"."project_id" = "tests_project"."id") LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_employee"."id" = "tests_meeting_attendees"."employee_id") LEFT OUTER JOIN "tests_meeting" ON ("tests_meeting_attendees"."meeting_id" = "tests_meeting"."id")')
