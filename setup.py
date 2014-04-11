from setuptools import setup, find_packages
import modeltree

kwargs = {
    # Packages
    'packages': find_packages(exclude=['tests', '*.tests', '*.tests.*', 'tests.*']),
    'include_package_data': True,

    # Dependencies
    'install_requires': ['django>=1.4,<1.6'],

    'test_suite': 'test_suite',

    # Metadata
    'version': modeltree.__version__,
    'name': 'modeltree',
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'Django ORM metaprogramming layer',
    'license': 'BSD',
    'keywords': 'Django meta ORM dynamic runtime',
    'url': 'http://cbmi.github.com/modeltree/',
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
    ],
}

setup(**kwargs)
