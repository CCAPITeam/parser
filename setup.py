from setuptools import setup

setup(
    name='apispecs',
    version='0.1',
    description='A parser for Swagger 2.0 API specification documents',
    url='https://github.com/CCAPITeam/parser',
    author='Derzsi Daniel',
    author_email='daniel.derzsi@cognitivecreators.com',
    license='MIT',
    packages=['apispecs'],
    install_requires=['PyYAML', 'marshmallow'],
    zip_safe=False
)