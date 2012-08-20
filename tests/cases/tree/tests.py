from django.test import TestCase
from modeltree.tree import trees
from . import models


class ModelTreeTestCase(TestCase):

    def setUp(self):
        self.office_mt = trees.create(models.Office)
        self.title_mt = trees.create(models.Title)
        self.employee_mt = trees.create(models.Employee)
        self.project_mt = trees.create(models.Project)
        self.meeting_mt = trees.create(models.Meeting)

    def test_get_model(self):
        self.assertEqual(self.employee_mt.get_model('tree.Employee'),
            models.Employee)
        self.assertEqual(self.employee_mt.get_model('employee', 'tree'),
            models.Employee)

    def test_query_string_for_field(self):
        location = self.office_mt.get_field('location', models.Office)
        salary = self.office_mt.get_field('salary', models.Title)
        name = self.office_mt.get_field('name', models.Project)
        start_time = self.office_mt.get_field('start_time', models.Meeting)

        # office modeltree
        qstr = self.office_mt.query_string_for_field(location)
        self.assertEqual(qstr, 'location')

        qstr = self.office_mt.query_string_for_field(salary)
        self.assertEqual(qstr, 'employee__title__salary')

        qstr = self.office_mt.query_string_for_field(name)
        self.assertEqual(qstr, 'employee__project__name')

        qstr = self.office_mt.query_string_for_field(start_time)
        self.assertEqual(qstr, 'meeting__start_time')

        # title modeltree
        qstr = self.title_mt.query_string_for_field(location)
        self.assertEqual(qstr, 'employee__office__location')

        qstr = self.title_mt.query_string_for_field(salary)
        self.assertEqual(qstr, 'salary')

        qstr = self.title_mt.query_string_for_field(name)
        self.assertEqual(qstr, 'employee__project__name')

        qstr = self.title_mt.query_string_for_field(start_time)
        self.assertEqual(qstr, 'employee__meeting__start_time')

        # employee modeltree
        qstr = self.employee_mt.query_string_for_field(location)
        self.assertEqual(qstr, 'office__location')

        qstr = self.employee_mt.query_string_for_field(salary)
        self.assertEqual(qstr, 'title__salary')

        qstr = self.employee_mt.query_string_for_field(name)
        self.assertEqual(qstr, 'project__name')

        qstr = self.employee_mt.query_string_for_field(start_time)
        self.assertEqual(qstr, 'meeting__start_time')

        # project modeltree
        qstr = self.project_mt.query_string_for_field(location)
        self.assertEqual(qstr, 'employees__office__location')

        qstr = self.project_mt.query_string_for_field(salary)
        self.assertEqual(qstr, 'employees__title__salary')

        qstr = self.project_mt.query_string_for_field(name)
        self.assertEqual(qstr, 'name')

        qstr = self.project_mt.query_string_for_field(start_time)
        self.assertEqual(qstr, 'meeting__start_time')

        # meeting modeltree
        qstr = self.meeting_mt.query_string_for_field(location)
        self.assertEqual(qstr, 'office__location')

        qstr = self.meeting_mt.query_string_for_field(salary)
        self.assertEqual(qstr, 'attendees__title__salary')

        qstr = self.meeting_mt.query_string_for_field(name)
        self.assertEqual(qstr, 'project__name')

        qstr = self.meeting_mt.query_string_for_field(start_time)
        self.assertEqual(qstr, 'start_time')

    def test_get_joins(self):
        self.office_mt = trees.create(models.Office)

        title_qs, alias = self.office_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tree_office"."id", "tree_office"."location" FROM "tree_office" LEFT OUTER JOIN "tree_employee" ON ("tree_office"."id" = "tree_employee"."office_id") INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id")')

        employee_qs, alias = self.office_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tree_office"."id", "tree_office"."location" FROM "tree_office" LEFT OUTER JOIN "tree_employee" ON ("tree_office"."id" = "tree_employee"."office_id")')

        project_qs, alias = self.office_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tree_office"."id", "tree_office"."location" FROM "tree_office" LEFT OUTER JOIN "tree_employee" ON ("tree_office"."id" = "tree_employee"."office_id") LEFT OUTER JOIN "tree_project_employees" ON ("tree_employee"."id" = "tree_project_employees"."employee_id") LEFT OUTER JOIN "tree_project" ON ("tree_project_employees"."project_id" = "tree_project"."id")')

        meeting_qs, alias = self.office_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tree_office"."id", "tree_office"."location" FROM "tree_office" LEFT OUTER JOIN "tree_meeting" ON ("tree_office"."id" = "tree_meeting"."office_id")')


        self.title_mt = trees.create(models.Title)

        office_qs, alias = self.title_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tree_title"."id", "tree_title"."name", "tree_title"."salary" FROM "tree_title" LEFT OUTER JOIN "tree_employee" ON ("tree_title"."id" = "tree_employee"."title_id") INNER JOIN "tree_office" ON ("tree_employee"."office_id" = "tree_office"."id")')

        employee_qs, alias = self.title_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tree_title"."id", "tree_title"."name", "tree_title"."salary" FROM "tree_title" LEFT OUTER JOIN "tree_employee" ON ("tree_title"."id" = "tree_employee"."title_id")')

        project_qs, alias = self.title_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tree_title"."id", "tree_title"."name", "tree_title"."salary" FROM "tree_title" LEFT OUTER JOIN "tree_employee" ON ("tree_title"."id" = "tree_employee"."title_id") LEFT OUTER JOIN "tree_project_employees" ON ("tree_employee"."id" = "tree_project_employees"."employee_id") LEFT OUTER JOIN "tree_project" ON ("tree_project_employees"."project_id" = "tree_project"."id")')

        meeting_qs, alias = self.title_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tree_title"."id", "tree_title"."name", "tree_title"."salary" FROM "tree_title" LEFT OUTER JOIN "tree_employee" ON ("tree_title"."id" = "tree_employee"."title_id") LEFT OUTER JOIN "tree_meeting_attendees" ON ("tree_employee"."id" = "tree_meeting_attendees"."employee_id") LEFT OUTER JOIN "tree_meeting" ON ("tree_meeting_attendees"."meeting_id" = "tree_meeting"."id")')


        self.employee_mt = trees.create(models.Employee)

        title_qs, alias = self.employee_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tree_employee"."id", "tree_employee"."firstName", "tree_employee"."last_name", "tree_employee"."title_id", "tree_employee"."office_id", "tree_employee"."manager_id" FROM "tree_employee" INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id")')

        office_qs, alias = self.employee_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tree_employee"."id", "tree_employee"."firstName", "tree_employee"."last_name", "tree_employee"."title_id", "tree_employee"."office_id", "tree_employee"."manager_id" FROM "tree_employee" INNER JOIN "tree_office" ON ("tree_employee"."office_id" = "tree_office"."id")')

        project_qs, alias = self.employee_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tree_employee"."id", "tree_employee"."firstName", "tree_employee"."last_name", "tree_employee"."title_id", "tree_employee"."office_id", "tree_employee"."manager_id" FROM "tree_employee" LEFT OUTER JOIN "tree_project_employees" ON ("tree_employee"."id" = "tree_project_employees"."employee_id") LEFT OUTER JOIN "tree_project" ON ("tree_project_employees"."project_id" = "tree_project"."id")')

        meeting_qs, alias = self.employee_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tree_employee"."id", "tree_employee"."firstName", "tree_employee"."last_name", "tree_employee"."title_id", "tree_employee"."office_id", "tree_employee"."manager_id" FROM "tree_employee" LEFT OUTER JOIN "tree_meeting_attendees" ON ("tree_employee"."id" = "tree_meeting_attendees"."employee_id") LEFT OUTER JOIN "tree_meeting" ON ("tree_meeting_attendees"."meeting_id" = "tree_meeting"."id")')


        self.project_mt = trees.create(models.Project)

        title_qs, alias = self.project_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tree_project"."id", "tree_project"."name", "tree_project"."manager_id", "tree_project"."due_date" FROM "tree_project" LEFT OUTER JOIN "tree_project_employees" ON ("tree_project"."id" = "tree_project_employees"."project_id") LEFT OUTER JOIN "tree_employee" ON ("tree_project_employees"."employee_id" = "tree_employee"."id") INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id")')

        office_qs, alias = self.project_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tree_project"."id", "tree_project"."name", "tree_project"."manager_id", "tree_project"."due_date" FROM "tree_project" LEFT OUTER JOIN "tree_project_employees" ON ("tree_project"."id" = "tree_project_employees"."project_id") LEFT OUTER JOIN "tree_employee" ON ("tree_project_employees"."employee_id" = "tree_employee"."id") INNER JOIN "tree_office" ON ("tree_employee"."office_id" = "tree_office"."id")')

        employee_qs, alias = self.project_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tree_project"."id", "tree_project"."name", "tree_project"."manager_id", "tree_project"."due_date" FROM "tree_project" LEFT OUTER JOIN "tree_project_employees" ON ("tree_project"."id" = "tree_project_employees"."project_id") LEFT OUTER JOIN "tree_employee" ON ("tree_project_employees"."employee_id" = "tree_employee"."id")')

        meeting_qs, alias = self.project_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tree_project"."id", "tree_project"."name", "tree_project"."manager_id", "tree_project"."due_date" FROM "tree_project" LEFT OUTER JOIN "tree_meeting" ON ("tree_project"."id" = "tree_meeting"."project_id")')


        self.meeting_mt = trees.create(models.Meeting)

        title_qs, alias = self.meeting_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tree_meeting"."id", "tree_meeting"."project_id", "tree_meeting"."office_id", "tree_meeting"."start_time", "tree_meeting"."end_time" FROM "tree_meeting" LEFT OUTER JOIN "tree_meeting_attendees" ON ("tree_meeting"."id" = "tree_meeting_attendees"."meeting_id") LEFT OUTER JOIN "tree_employee" ON ("tree_meeting_attendees"."employee_id" = "tree_employee"."id") INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id")')

        office_qs, alias = self.meeting_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tree_meeting"."id", "tree_meeting"."project_id", "tree_meeting"."office_id", "tree_meeting"."start_time", "tree_meeting"."end_time" FROM "tree_meeting" INNER JOIN "tree_office" ON ("tree_meeting"."office_id" = "tree_office"."id")')

        employee_qs, alias = self.meeting_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tree_meeting"."id", "tree_meeting"."project_id", "tree_meeting"."office_id", "tree_meeting"."start_time", "tree_meeting"."end_time" FROM "tree_meeting" LEFT OUTER JOIN "tree_meeting_attendees" ON ("tree_meeting"."id" = "tree_meeting_attendees"."meeting_id") LEFT OUTER JOIN "tree_employee" ON ("tree_meeting_attendees"."employee_id" = "tree_employee"."id")')

        project_qs, alias = self.meeting_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tree_meeting"."id", "tree_meeting"."project_id", "tree_meeting"."office_id", "tree_meeting"."start_time", "tree_meeting"."end_time" FROM "tree_meeting" LEFT OUTER JOIN "tree_project" ON ("tree_meeting"."project_id" = "tree_project"."id")')

    def test_add_select(self):
        location = self.office_mt.get_field('location', models.Office)
        salary = self.office_mt.get_field('salary', models.Title)
        name = self.office_mt.get_field('name', models.Project)
        start_time = self.office_mt.get_field('start_time', models.Meeting)

        fields = [location, salary, name, start_time]

        qs = self.office_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tree_office"."id", "tree_office"."location", "tree_title"."salary", "tree_project"."name", "tree_meeting"."start_time" FROM "tree_office" LEFT OUTER JOIN "tree_employee" ON ("tree_office"."id" = "tree_employee"."office_id") INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id") LEFT OUTER JOIN "tree_project_employees" ON ("tree_employee"."id" = "tree_project_employees"."employee_id") LEFT OUTER JOIN "tree_project" ON ("tree_project_employees"."project_id" = "tree_project"."id") LEFT OUTER JOIN "tree_meeting" ON ("tree_office"."id" = "tree_meeting"."office_id")')

        qs = self.title_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tree_title"."id", "tree_office"."location", "tree_title"."salary", "tree_project"."name", "tree_meeting"."start_time" FROM "tree_title" LEFT OUTER JOIN "tree_employee" ON ("tree_title"."id" = "tree_employee"."title_id") INNER JOIN "tree_office" ON ("tree_employee"."office_id" = "tree_office"."id") LEFT OUTER JOIN "tree_project_employees" ON ("tree_employee"."id" = "tree_project_employees"."employee_id") LEFT OUTER JOIN "tree_project" ON ("tree_project_employees"."project_id" = "tree_project"."id") LEFT OUTER JOIN "tree_meeting_attendees" ON ("tree_employee"."id" = "tree_meeting_attendees"."employee_id") LEFT OUTER JOIN "tree_meeting" ON ("tree_meeting_attendees"."meeting_id" = "tree_meeting"."id")')

        qs = self.employee_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tree_employee"."id", "tree_office"."location", "tree_title"."salary", "tree_project"."name", "tree_meeting"."start_time" FROM "tree_employee" INNER JOIN "tree_office" ON ("tree_employee"."office_id" = "tree_office"."id") INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id") LEFT OUTER JOIN "tree_project_employees" ON ("tree_employee"."id" = "tree_project_employees"."employee_id") LEFT OUTER JOIN "tree_project" ON ("tree_project_employees"."project_id" = "tree_project"."id") LEFT OUTER JOIN "tree_meeting_attendees" ON ("tree_employee"."id" = "tree_meeting_attendees"."employee_id") LEFT OUTER JOIN "tree_meeting" ON ("tree_meeting_attendees"."meeting_id" = "tree_meeting"."id")')

        qs = self.project_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tree_project"."id", "tree_office"."location", "tree_title"."salary", "tree_project"."name", "tree_meeting"."start_time" FROM "tree_project" LEFT OUTER JOIN "tree_project_employees" ON ("tree_project"."id" = "tree_project_employees"."project_id") LEFT OUTER JOIN "tree_employee" ON ("tree_project_employees"."employee_id" = "tree_employee"."id") INNER JOIN "tree_office" ON ("tree_employee"."office_id" = "tree_office"."id") INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id") LEFT OUTER JOIN "tree_meeting" ON ("tree_project"."id" = "tree_meeting"."project_id")')

        qs = self.meeting_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tree_meeting"."id", "tree_office"."location", "tree_title"."salary", "tree_project"."name", "tree_meeting"."start_time" FROM "tree_meeting" INNER JOIN "tree_office" ON ("tree_meeting"."office_id" = "tree_office"."id") LEFT OUTER JOIN "tree_meeting_attendees" ON ("tree_meeting"."id" = "tree_meeting_attendees"."meeting_id") LEFT OUTER JOIN "tree_employee" ON ("tree_meeting_attendees"."employee_id" = "tree_employee"."id") INNER JOIN "tree_title" ON ("tree_employee"."title_id" = "tree_title"."id") LEFT OUTER JOIN "tree_project" ON ("tree_meeting"."project_id" = "tree_project"."id")')
