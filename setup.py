from os.path import abspath, dirname, join
from setuptools import find_packages, setup


ENTRY_POINTS = """
[invisibleroads]
edit = invisibleroads_scripts:EditMissionScript
"""
FOLDER = dirname(abspath(__file__))
DESCRIPTION = '\n\n'.join(open(join(FOLDER, x)).read().strip() for x in [
    'README.rst', 'CHANGES.rst'])
setup(
    name='invisibleroads-scripts',
    version='2.0.3',
    description='Command-line scripts for managing your goals',
    long_description=DESCRIPTION,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    author='Roy Hyunjin Han',
    author_email='rhh@crosscompute.com',
    url='https://github.com/invisibleroads/invisibleroads-scripts',
    keywords='invisibleroads',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'invisibleroads',
        'invisibleroads-macros',
        'networkx',
        'psycopg2',
        'psycopg2-binary',
        'pytz',
        'sqlalchemy',
    ],
    entry_points=ENTRY_POINTS)
