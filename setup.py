from distutils.core import setup
from setuptools import find_packages

setup(name='django-bundles',
      version='0.6.0',
      description='Another Django media bundler',
      author='Sam Cooke',
      author_email='sam.cooke@xylate.com',
      url='https://github.com/sdcooke/django_bundles',
      packages=find_packages(),
      include_package_data=True,
      license="MIT license, see LICENSE file",
)
