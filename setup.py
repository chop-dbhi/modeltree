from setuptools import setup, find_packages

kwargs = {
    # Packages
    'packages': find_packages(),
    'include_package_data': True,

    # Dependencies
    'install_requires': ['django>=1.3'],

    # Tests
    'test_suite': 'test_suite',

    # Metadata
    'name': 'modeltree',
    'version': __import__('modeltree').get_version(),
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'Django ORM metaprogramming layer',
    'license': 'BSD',
    'keywords': 'Django meta ORM',
    'url': 'https://github.com/cbmi/modeltree/',
    'classifiers': [
        'Development Status :: 5 - Production',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
}

setup(**kwargs)
