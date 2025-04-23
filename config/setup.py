# setup.py
from setuptools import setup

setup(
    name='shadowhunter',
    version='1.0',
    py_modules=['shadowhunter'],
    entry_points={
        'console_scripts': [
            'shadowhunter = shadowhunter:main',
        ],
    },
)
