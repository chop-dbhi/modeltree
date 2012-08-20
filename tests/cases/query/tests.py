from django.test import TestCase
from modeltree.query import resolve_lookup, M, InvalidLookup
from modeltree.tree import trees
from .models import Employee, Office, Title, Project, Meeting


class ModelTreeQuerySetTestCase(TestCase):
    def setUp(self):
        trees._modeltrees['default'] = trees.create(Employee)
        trees._modeltrees['project'] = trees.create(Project)

    def tearDown(self):
        trees._modeltrees = {}

    def test_filter(self):
        qs = Employee.objects.filter(title__salary__lt=50000)
        self.assertEqual(str(qs.query), 'SELECT "query_employee"."id", "query_employee"."firstName", "query_employee"."last_name", "query_employee"."title_id", "query_employee"."office_id", "query_employee"."manager_id" FROM "query_employee" INNER JOIN "query_title" ON ("query_employee"."title_id" = "query_title"."id") WHERE "query_title"."salary" < 50000 ')

    def test_exclude(self):
        qs = Employee.objects.exclude(title__salary__lt=50000)
        self.assertEqual(str(qs.query), 'SELECT "query_employee"."id", "query_employee"."firstName", "query_employee"."last_name", "query_employee"."title_id", "query_employee"."office_id", "query_employee"."manager_id" FROM "query_employee" INNER JOIN "query_title" ON ("query_employee"."title_id" = "query_title"."id") WHERE NOT ("query_title"."salary" < 50000 )')

    def test_select(self):
        location = Office._meta.get_field_by_name('location')[0]
        salary = Title._meta.get_field_by_name('salary')[0]
        name = Project._meta.get_field_by_name('name')[0]
        start_time = Meeting._meta.get_field_by_name('start_time')[0]

        qs = Employee.objects.select(location, salary, name, start_time)
        self.assertEqual(str(qs.query), 'SELECT "query_employee"."id", "query_office"."location", "query_title"."salary", "query_project"."name", "query_meeting"."start_time" FROM "query_employee" INNER JOIN "query_office" ON ("query_employee"."office_id" = "query_office"."id") INNER JOIN "query_title" ON ("query_employee"."title_id" = "query_title"."id") LEFT OUTER JOIN "query_project_employees" ON ("query_employee"."id" = "query_project_employees"."employee_id") LEFT OUTER JOIN "query_project" ON ("query_project_employees"."project_id" = "query_project"."id") LEFT OUTER JOIN "query_meeting_attendees" ON ("query_employee"."id" = "query_meeting_attendees"."employee_id") LEFT OUTER JOIN "query_meeting" ON ("query_meeting_attendees"."meeting_id" = "query_meeting"."id")')


class LookupResolverTestCase(TestCase):
    def setUp(self):
        trees._modeltrees['default'] = trees.create(Employee)
        trees._modeltrees['project'] = trees.create(Project)

    def tearDown(self):
        trees._modeltrees = {}

    def test_invalid_model(self):
        self.assertRaises(InvalidLookup, resolve_lookup, 'office', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__office', tree=Office)

        self.assertRaises(InvalidLookup, resolve_lookup, 'title', tree=Title)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__title', tree=Title)

        self.assertRaises(InvalidLookup, resolve_lookup, 'employee', tree=Employee)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__employee', tree=Employee)

        self.assertRaises(InvalidLookup, resolve_lookup, 'project', tree=Project)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__project', tree=Project)

        self.assertRaises(InvalidLookup, resolve_lookup, 'meeting', tree=Meeting)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__meeting', tree=Meeting)

    def test_invalid_local(self):
        self.assertRaises(InvalidLookup, resolve_lookup, 'office__id', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__office__id', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'office__location', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__office__location', tree=Office)

        self.assertRaises(InvalidLookup, resolve_lookup, 'title__id', tree=Title)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__title__id', tree=Title)
        self.assertRaises(InvalidLookup, resolve_lookup, 'title__name', tree=Title)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__title__name', tree=Title)
        self.assertRaises(InvalidLookup, resolve_lookup, 'title__salary', tree=Title)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__title__salary', tree=Title)

        self.assertRaises(InvalidLookup, resolve_lookup, 'employee__id', tree=Employee)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__employee__id', tree=Employee)
        self.assertRaises(InvalidLookup, resolve_lookup, 'employee__first_name', tree=Employee)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__employee__first_name', tree=Employee)
        self.assertRaises(InvalidLookup, resolve_lookup, 'employee__last_name', tree=Employee)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__employee__last_name', tree=Employee)

        self.assertRaises(InvalidLookup, resolve_lookup, 'project__id', tree=Project)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__project__id', tree=Project)
        self.assertRaises(InvalidLookup, resolve_lookup, 'project__name', tree=Project)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__project__name', tree=Project)
        self.assertRaises(InvalidLookup, resolve_lookup, 'project__due_date', tree=Project)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__project__due_date', tree=Project)

        self.assertRaises(InvalidLookup, resolve_lookup, 'meeting__id', tree=Meeting)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__meeting__id', tree=Meeting)
        self.assertRaises(InvalidLookup, resolve_lookup, 'meeting__start_time', tree=Meeting)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__meeting__start_time', tree=Meeting)
        self.assertRaises(InvalidLookup, resolve_lookup, 'meeting__end_time', tree=Meeting)
        self.assertRaises(InvalidLookup, resolve_lookup, 'query__meeting__end_time', tree=Meeting)

    def test_not_found(self):
        self.assertRaises(InvalidLookup, resolve_lookup, 'name', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'salary', tree=Office)

        self.assertRaises(InvalidLookup, resolve_lookup, 'first_name', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'last_name', tree=Office)
        # Also a model name, no exception thrown
        # self.assertRaises(InvalidLookup, resolve_lookup, 'title', tree=Office)
        # Above lookup takes precedence
        # self.assertRaises(InvalidLookup, resolve_lookup, 'office', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'manager', tree=Office)

        # Redundant
        # self.assertRaises(InvalidLookup, resolve_lookup, 'name', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'employees', tree=Office)
        # Redundant
        # self.assertRaises(InvalidLookup, resolve_lookup, 'manager', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'due_date', tree=Office)

        self.assertRaises(InvalidLookup, resolve_lookup, 'attendees', tree=Office)
        # Also a model name, no exception thrown
        # self.assertRaises(InvalidLookup, resolve_lookup, 'project', tree=Office)
        # Above lookup takes precedence
        # self.assertRaises(InvalidLookup, resolve_lookup, 'office', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'start_time', tree=Office)
        self.assertRaises(InvalidLookup, resolve_lookup, 'end_time', tree=Office)

        # TODO finish not found

    def test_local(self):
        self.assertEqual(resolve_lookup('id', tree=Office), 'id')
        self.assertEqual(resolve_lookup('location', tree=Office), 'location')

        self.assertEqual(resolve_lookup('id', tree=Title), 'id')
        self.assertEqual(resolve_lookup('name', tree=Title), 'name')
        self.assertEqual(resolve_lookup('salary', tree=Title), 'salary')

        self.assertEqual(resolve_lookup('id', tree=Employee), 'id')
        self.assertEqual(resolve_lookup('first_name', tree=Employee), 'first_name')
        self.assertEqual(resolve_lookup('last_name', tree=Employee), 'last_name')

        self.assertEqual(resolve_lookup('id', tree=Project), 'id')
        self.assertEqual(resolve_lookup('name', tree=Project), 'name')
        self.assertEqual(resolve_lookup('due_date', tree=Project), 'due_date')

        self.assertEqual(resolve_lookup('id', tree=Meeting), 'id')
        self.assertEqual(resolve_lookup('start_time', tree=Meeting), 'start_time')
        self.assertEqual(resolve_lookup('end_time', tree=Meeting), 'end_time')

    def test_fk(self):
        self.assertEqual(resolve_lookup('title', tree=Employee), 'title')
        self.assertEqual(resolve_lookup('office', tree=Employee), 'office')
        self.assertEqual(resolve_lookup('manager', tree=Employee), 'manager')

        self.assertEqual(resolve_lookup('manager', tree=Project), 'manager')

        self.assertEqual(resolve_lookup('project', tree=Meeting), 'project')
        self.assertEqual(resolve_lookup('office', tree=Meeting), 'office')

    def test_reverse_fk(self):
        self.assertEqual(resolve_lookup('employee', tree=Office), 'employee')
        self.assertEqual(resolve_lookup('meeting', tree=Office), 'meeting')

        self.assertEqual(resolve_lookup('employee', tree=Title), 'employee')

        self.assertEqual(resolve_lookup('managed_employees', tree=Employee), 'managed_employees')
        # Relationship from Project => Employee via the `manager` relationship
        self.assertEqual(resolve_lookup('managed_projects', tree=Employee), 'managed_projects')

        self.assertEqual(resolve_lookup('meeting', tree=Project), 'meeting')

    def test_m2m(self):
        self.assertEqual(resolve_lookup('employees', tree=Project), 'employees')
        self.assertEqual(resolve_lookup('attendees', tree=Meeting), 'attendees')

    def test_reverse_m2m(self):
        self.assertEqual(resolve_lookup('project', tree=Employee), 'project')
        self.assertEqual(resolve_lookup('meeting', tree=Employee), 'meeting')

    def test_arbitrary(self):
        self.assertEqual(resolve_lookup('employee__id', tree=Office), 'employee__id')
        self.assertEqual(resolve_lookup('query__employee__id', tree=Office), 'employee__id')

        self.assertEqual(resolve_lookup('title__id', tree=Office), 'employee__title__id')
        self.assertEqual(resolve_lookup('query__title__id', tree=Office), 'employee__title__id')

        self.assertEqual(resolve_lookup('title__name', tree=Office), 'employee__title__name')
        self.assertEqual(resolve_lookup('query__title__name', tree=Office), 'employee__title__name')

        self.assertEqual(resolve_lookup('title__salary', tree=Office), 'employee__title__salary')
        self.assertEqual(resolve_lookup('query__title__salary', tree=Office), 'employee__title__salary')

        self.assertEqual(resolve_lookup('employee__first_name', tree=Office), 'employee__first_name')
        self.assertEqual(resolve_lookup('query__employee__first_name', tree=Office), 'employee__first_name')

        self.assertEqual(resolve_lookup('employee__last_name', tree=Office), 'employee__last_name')
        self.assertEqual(resolve_lookup('query__employee__last_name', tree=Office), 'employee__last_name')

        self.assertEqual(resolve_lookup('employee__title', tree=Office), 'employee__title')
        self.assertEqual(resolve_lookup('query__employee__title', tree=Office), 'employee__title')

        self.assertEqual(resolve_lookup('employee__office', tree=Office), 'employee__office')
        self.assertEqual(resolve_lookup('query__employee__office', tree=Office), 'employee__office')

        self.assertEqual(resolve_lookup('employee__manager', tree=Office), 'employee__manager')
        self.assertEqual(resolve_lookup('query__employee__manager', tree=Office), 'employee__manager')

        self.assertEqual(resolve_lookup('project__id', tree=Office), 'employee__project__id')
        self.assertEqual(resolve_lookup('query__project__id', tree=Office), 'employee__project__id')

        self.assertEqual(resolve_lookup('project__name', tree=Office), 'employee__project__name')
        self.assertEqual(resolve_lookup('query__project__name', tree=Office), 'employee__project__name')

        self.assertEqual(resolve_lookup('project__manager', tree=Office), 'employee__project__manager')
        self.assertEqual(resolve_lookup('query__project__manager', tree=Office), 'employee__project__manager')

        self.assertEqual(resolve_lookup('project__due_date', tree=Office), 'employee__project__due_date')
        self.assertEqual(resolve_lookup('query__project__due_date', tree=Office), 'employee__project__due_date')

        self.assertEqual(resolve_lookup('project__employees', tree=Office), 'employee__project__employees')
        self.assertEqual(resolve_lookup('query__project__employees', tree=Office), 'employee__project__employees')

        self.assertEqual(resolve_lookup('meeting__id', tree=Office), 'meeting__id')
        self.assertEqual(resolve_lookup('query__meeting__id', tree=Office), 'meeting__id')

        self.assertEqual(resolve_lookup('meeting__project', tree=Office), 'meeting__project')
        self.assertEqual(resolve_lookup('query__meeting__project', tree=Office), 'meeting__project')

        self.assertEqual(resolve_lookup('meeting__office', tree=Office), 'meeting__office')
        self.assertEqual(resolve_lookup('query__meeting__office', tree=Office), 'meeting__office')

        # TODO finish arbitrary lookups


class MTestCase(TestCase):
    def setUp(self):
        trees._modeltrees['default'] = trees.create(Employee)
        trees._modeltrees['project'] = trees.create(Project)

    def tearDown(self):
        trees._modeltrees = {}

    def test_variations(self):
        tests = [
            # basic, no operator
            (M(office__location='Outer Space'),
                "(AND: ('office__location', 'Outer Space'))"),
            # full, no operator
            (M(query__office__location='Outer Space'),
                "(AND: ('office__location', 'Outer Space'))"),
            # full, operator
            (M(query__office__location__iexact='Outer Space'),
                "(AND: ('office__location__iexact', 'Outer Space'))"),

            # alternate root, basic, no operator
            (M('project', title__salary=100000),
                "(AND: ('employees__title__salary', 100000))"),
            # alternate root, basic, operator
            (M('project', title__salary__gt=100000),
                "(AND: ('employees__title__salary__gt', 100000))"),
            # alternate root, full, no operator
            (M('project', query__title__salary=100000),
                "(AND: ('employees__title__salary', 100000))"),

            # complex
            (M('project', title__salary=100000) & M(office__location='Outer Space'),
                "(AND: ('employees__title__salary', 100000), ('office__location', 'Outer Space'))"),

            (M('project', title__salary=100000) | M(office__location='Outer Space'),
                "(OR: ('employees__title__salary', 100000), ('office__location', 'Outer Space'))"),
        ]

        for m, s in tests:
            self.assertEqual(str(m), s)
