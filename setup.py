from os import path
import sys

from setuptools import setup

# Open encoding isn't available for Python 2.7 (sigh)
if sys.version_info < (3, 0):
    from io import open


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='pytest-tinybird',
    description='A pytest plugin to report test results to tinybird',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['pytest_tinybird'],
    author='jlmadurga',
    author_email='jlmadurga@gmail.com',
    version='0.1.0',
    url='https://github.com/jlmadurga/pytest-tinybird',
    license='MIT',
    install_requires=[
        'pytest>=3.8.0',
        'requests>=2.28.1'
    ],
    entry_points={
        'pytest11': [
            'pytest_tinybird = pytest_tinybird.plugin',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Pytest',
    ],
)
