from setuptools import setup, find_packages

setup(
    name="spine-analyzer-pro",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        line.strip() for line in open("requirements.txt").readlines()
    ],
    entry_points={
        'console_scripts': [
            'spine-analyzer=app.main:main',
        ],
    },
    package_data={
        'app': ['ui/styles/*.qss', 'reporting/templates/*'],
        'models': ['segmentation/*.pth', 'detection/*.pt'],
    },
    python_requires='>=3.8',
)