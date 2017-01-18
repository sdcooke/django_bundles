from distutils.core import setup
from setuptools import find_packages

tests_require = [
    'Django>=1.4,<1.11',
    'tox>=2.3.1,<3.0.0',
]

setup(name='django-bundles',
      version='0.6.6',
      description='Another Django media bundler',
      author='Sam Cooke',
      author_email='sam.cooke@xylate.com',
      url='https://github.com/sdcooke/django_bundles',
      packages=find_packages(),
      include_package_data=True,
      license="MIT license, see LICENSE file",
      tests_require=tests_require,
      test_suite="testrunner.runtests",
)
