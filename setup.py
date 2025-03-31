from setuptools import setup

setup(name='epynet',
      version='1.2',
      description='Vitens EPANET 2.2 wrapper and utilities',
      url='https://github.com/vitenstc/epynet',
      author='Abel Heinsbroek','Ton Blom',
      author_email='abel.heinsbroek@vitens.nl',
      license='Apache Licence 2.0',
      packages=['epynet'],
      package_data={'epynet': ['lib/*']},
      install_requires = [
          'pandas'
      ],
      zip_safe=False)
