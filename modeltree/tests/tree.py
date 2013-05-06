import django
from django.test import TestCase
from modeltree.tree import trees
from modeltree.tests import models

__all__ = ('LazyTreesTestCase', 'ModelTreeTestCase')

get_join_type = lambda: django.VERSION < (1, 5) and 'INNER JOIN' or 'LEFT OUTER JOIN'


class LazyTreesTestCase(TestCase):
    def test(self):
        # From settings...
        self.assertEqual(len(trees.modeltrees), 2)
        # None initialized..
        self.assertEqual(len(trees), 0)

        # Compare different variations..
        self.assertEqual(trees.default, trees[models.Employee])
        self.assertEqual(trees.default, trees['tests.employee'])

        self.assertEqual(len(trees), 1)
        self.assertEqual(trees._model_aliases[models.Employee], 'default')


class ModelTreeTestCase(TestCase):
    def setUp(self):
        self.office_mt = trees.create(models.Office)
        self.title_mt = trees.create(models.Title)
        self.employee_mt = trees.create(models.Employee)
        self.project_mt = trees.create(models.Project)
        self.meeting_mt = trees.create(models.Meeting)

    def test_get_model(self):
        self.assertEqual(self.employee_mt.get_model('tests.Employee'),
            models.Employee)
        self.assertEqual(self.employee_mt.get_model('employee', 'tests'),
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

    def test_get_join_types(self):
        self.office_mt = trees.create(models.Office)

        title_qs, alias = self.office_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tests_office"."id", "tests_office"."location" FROM "tests_office" LEFT OUTER JOIN "tests_employee" ON ("tests_office"."id" = "tests_employee"."office_id") {join} "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id")'.format(join=get_join_type()))

        employee_qs, alias = self.office_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tests_office"."id", "tests_office"."location" FROM "tests_office" LEFT OUTER JOIN "tests_employee" ON ("tests_office"."id" = "tests_employee"."office_id")')

        project_qs, alias = self.office_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tests_office"."id", "tests_office"."location" FROM "tests_office" LEFT OUTER JOIN "tests_employee" ON ("tests_office"."id" = "tests_employee"."office_id") LEFT OUTER JOIN "tests_project_employees" ON ("tests_employee"."id" = "tests_project_employees"."employee_id") LEFT OUTER JOIN "tests_project" ON ("tests_project_employees"."project_id" = "tests_project"."id")')

        meeting_qs, alias = self.office_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tests_office"."id", "tests_office"."location" FROM "tests_office" LEFT OUTER JOIN "tests_meeting" ON ("tests_office"."id" = "tests_meeting"."office_id")')


        self.title_mt = trees.create(models.Title)

        office_qs, alias = self.title_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tests_title"."id", "tests_title"."name", "tests_title"."salary" FROM "tests_title" LEFT OUTER JOIN "tests_employee" ON ("tests_title"."id" = "tests_employee"."title_id") {join} "tests_office" ON ("tests_employee"."office_id" = "tests_office"."id")'.format(join=get_join_type()))

        employee_qs, alias = self.title_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tests_title"."id", "tests_title"."name", "tests_title"."salary" FROM "tests_title" LEFT OUTER JOIN "tests_employee" ON ("tests_title"."id" = "tests_employee"."title_id")')

        project_qs, alias = self.title_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tests_title"."id", "tests_title"."name", "tests_title"."salary" FROM "tests_title" LEFT OUTER JOIN "tests_employee" ON ("tests_title"."id" = "tests_employee"."title_id") LEFT OUTER JOIN "tests_project_employees" ON ("tests_employee"."id" = "tests_project_employees"."employee_id") LEFT OUTER JOIN "tests_project" ON ("tests_project_employees"."project_id" = "tests_project"."id")')

        meeting_qs, alias = self.title_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tests_title"."id", "tests_title"."name", "tests_title"."salary" FROM "tests_title" LEFT OUTER JOIN "tests_employee" ON ("tests_title"."id" = "tests_employee"."title_id") LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_employee"."id" = "tests_meeting_attendees"."employee_id") LEFT OUTER JOIN "tests_meeting" ON ("tests_meeting_attendees"."meeting_id" = "tests_meeting"."id")')


        self.employee_mt = trees.create(models.Employee)

        title_qs, alias = self.employee_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id")')

        office_qs, alias = self.employee_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" INNER JOIN "tests_office" ON ("tests_employee"."office_id" = "tests_office"."id")')

        project_qs, alias = self.employee_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" LEFT OUTER JOIN "tests_project_employees" ON ("tests_employee"."id" = "tests_project_employees"."employee_id") LEFT OUTER JOIN "tests_project" ON ("tests_project_employees"."project_id" = "tests_project"."id")')

        meeting_qs, alias = self.employee_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tests_employee"."id", "tests_employee"."firstName", "tests_employee"."last_name", "tests_employee"."title_id", "tests_employee"."office_id", "tests_employee"."manager_id" FROM "tests_employee" LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_employee"."id" = "tests_meeting_attendees"."employee_id") LEFT OUTER JOIN "tests_meeting" ON ("tests_meeting_attendees"."meeting_id" = "tests_meeting"."id")')


        self.project_mt = trees.create(models.Project)

        title_qs, alias = self.project_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tests_project"."id", "tests_project"."name", "tests_project"."manager_id", "tests_project"."due_date" FROM "tests_project" LEFT OUTER JOIN "tests_project_employees" ON ("tests_project"."id" = "tests_project_employees"."project_id") LEFT OUTER JOIN "tests_employee" ON ("tests_project_employees"."employee_id" = "tests_employee"."id") {join} "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id")'.format(join=get_join_type()))

        office_qs, alias = self.project_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tests_project"."id", "tests_project"."name", "tests_project"."manager_id", "tests_project"."due_date" FROM "tests_project" LEFT OUTER JOIN "tests_project_employees" ON ("tests_project"."id" = "tests_project_employees"."project_id") LEFT OUTER JOIN "tests_employee" ON ("tests_project_employees"."employee_id" = "tests_employee"."id") {join} "tests_office" ON ("tests_employee"."office_id" = "tests_office"."id")'.format(join=get_join_type()))

        employee_qs, alias = self.project_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tests_project"."id", "tests_project"."name", "tests_project"."manager_id", "tests_project"."due_date" FROM "tests_project" LEFT OUTER JOIN "tests_project_employees" ON ("tests_project"."id" = "tests_project_employees"."project_id") LEFT OUTER JOIN "tests_employee" ON ("tests_project_employees"."employee_id" = "tests_employee"."id")')

        meeting_qs, alias = self.project_mt.add_joins(models.Meeting)
        self.assertEqual(str(meeting_qs.query), 'SELECT "tests_project"."id", "tests_project"."name", "tests_project"."manager_id", "tests_project"."due_date" FROM "tests_project" LEFT OUTER JOIN "tests_meeting" ON ("tests_project"."id" = "tests_meeting"."project_id")')


        self.meeting_mt = trees.create(models.Meeting)

        title_qs, alias = self.meeting_mt.add_joins(models.Title)
        self.assertEqual(str(title_qs.query), 'SELECT "tests_meeting"."id", "tests_meeting"."project_id", "tests_meeting"."office_id", "tests_meeting"."start_time", "tests_meeting"."end_time" FROM "tests_meeting" LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_meeting"."id" = "tests_meeting_attendees"."meeting_id") LEFT OUTER JOIN "tests_employee" ON ("tests_meeting_attendees"."employee_id" = "tests_employee"."id") {join} "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id")'.format(join=get_join_type()))

        office_qs, alias = self.meeting_mt.add_joins(models.Office)
        self.assertEqual(str(office_qs.query), 'SELECT "tests_meeting"."id", "tests_meeting"."project_id", "tests_meeting"."office_id", "tests_meeting"."start_time", "tests_meeting"."end_time" FROM "tests_meeting" INNER JOIN "tests_office" ON ("tests_meeting"."office_id" = "tests_office"."id")')

        employee_qs, alias = self.meeting_mt.add_joins(models.Employee)
        self.assertEqual(str(employee_qs.query), 'SELECT "tests_meeting"."id", "tests_meeting"."project_id", "tests_meeting"."office_id", "tests_meeting"."start_time", "tests_meeting"."end_time" FROM "tests_meeting" LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_meeting"."id" = "tests_meeting_attendees"."meeting_id") LEFT OUTER JOIN "tests_employee" ON ("tests_meeting_attendees"."employee_id" = "tests_employee"."id")')

        project_qs, alias = self.meeting_mt.add_joins(models.Project)
        self.assertEqual(str(project_qs.query), 'SELECT "tests_meeting"."id", "tests_meeting"."project_id", "tests_meeting"."office_id", "tests_meeting"."start_time", "tests_meeting"."end_time" FROM "tests_meeting" LEFT OUTER JOIN "tests_project" ON ("tests_meeting"."project_id" = "tests_project"."id")')

    def test_add_select(self):
        location = self.office_mt.get_field('location', models.Office)
        salary = self.office_mt.get_field('salary', models.Title)
        name = self.office_mt.get_field('name', models.Project)
        start_time = self.office_mt.get_field('start_time', models.Meeting)

        fields = [location, salary, name, start_time]

        qs = self.office_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tests_office"."id", "tests_office"."location", "tests_title"."salary", "tests_project"."name", "tests_meeting"."start_time" FROM "tests_office" LEFT OUTER JOIN "tests_employee" ON ("tests_office"."id" = "tests_employee"."office_id") {join} "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") LEFT OUTER JOIN "tests_project_employees" ON ("tests_employee"."id" = "tests_project_employees"."employee_id") LEFT OUTER JOIN "tests_project" ON ("tests_project_employees"."project_id" = "tests_project"."id") LEFT OUTER JOIN "tests_meeting" ON ("tests_office"."id" = "tests_meeting"."office_id")'.format(join=get_join_type()))

        qs = self.title_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tests_title"."id", "tests_office"."location", "tests_title"."salary", "tests_project"."name", "tests_meeting"."start_time" FROM "tests_title" LEFT OUTER JOIN "tests_employee" ON ("tests_title"."id" = "tests_employee"."title_id") {join} "tests_office" ON ("tests_employee"."office_id" = "tests_office"."id") LEFT OUTER JOIN "tests_project_employees" ON ("tests_employee"."id" = "tests_project_employees"."employee_id") LEFT OUTER JOIN "tests_project" ON ("tests_project_employees"."project_id" = "tests_project"."id") LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_employee"."id" = "tests_meeting_attendees"."employee_id") LEFT OUTER JOIN "tests_meeting" ON ("tests_meeting_attendees"."meeting_id" = "tests_meeting"."id")'.format(join=get_join_type()))

        qs = self.employee_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tests_employee"."id", "tests_office"."location", "tests_title"."salary", "tests_project"."name", "tests_meeting"."start_time" FROM "tests_employee" INNER JOIN "tests_office" ON ("tests_employee"."office_id" = "tests_office"."id") INNER JOIN "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") LEFT OUTER JOIN "tests_project_employees" ON ("tests_employee"."id" = "tests_project_employees"."employee_id") LEFT OUTER JOIN "tests_project" ON ("tests_project_employees"."project_id" = "tests_project"."id") LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_employee"."id" = "tests_meeting_attendees"."employee_id") LEFT OUTER JOIN "tests_meeting" ON ("tests_meeting_attendees"."meeting_id" = "tests_meeting"."id")')

        qs = self.project_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tests_project"."id", "tests_office"."location", "tests_title"."salary", "tests_project"."name", "tests_meeting"."start_time" FROM "tests_project" LEFT OUTER JOIN "tests_project_employees" ON ("tests_project"."id" = "tests_project_employees"."project_id") LEFT OUTER JOIN "tests_employee" ON ("tests_project_employees"."employee_id" = "tests_employee"."id") {join} "tests_office" ON ("tests_employee"."office_id" = "tests_office"."id") {join} "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") LEFT OUTER JOIN "tests_meeting" ON ("tests_project"."id" = "tests_meeting"."project_id")'.format(join=get_join_type()))

        qs = self.meeting_mt.add_select(*fields)
        self.assertEqual(str(qs.query), 'SELECT "tests_meeting"."id", "tests_office"."location", "tests_title"."salary", "tests_project"."name", "tests_meeting"."start_time" FROM "tests_meeting" INNER JOIN "tests_office" ON ("tests_meeting"."office_id" = "tests_office"."id") LEFT OUTER JOIN "tests_meeting_attendees" ON ("tests_meeting"."id" = "tests_meeting_attendees"."meeting_id") LEFT OUTER JOIN "tests_employee" ON ("tests_meeting_attendees"."employee_id" = "tests_employee"."id") {join} "tests_title" ON ("tests_employee"."title_id" = "tests_title"."id") LEFT OUTER JOIN "tests_project" ON ("tests_meeting"."project_id" = "tests_project"."id")'.format(join=get_join_type()))
