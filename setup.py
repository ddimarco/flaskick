from setuptools import setup

setup(
    name='flaskick',
    version='0.1',
    description="description",
    url='url',
    packages=['flaskick'],
    entry_points={
        'console_scripts': ['flaskick=flaskick.cli:cli'],
    })
