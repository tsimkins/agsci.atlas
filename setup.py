from setuptools import setup, find_packages
import os

version = open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 
    'agsci', 'atlas', 'version.txt')).read().strip()

setup(name='agsci.atlas',
    version=version,
    description="",
    long_description=open("README.txt").read() + "\n" +
                     open("HISTORY.txt").read(),
    # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
      "Framework :: Plone",
      "Programming Language :: Python",
      "Topic :: Software Development :: Libraries :: Python Modules",
      ],
    keywords='',
    author='Tim Simkins',
    author_email='trs22@psu.edu',
    url='http://agsci.psu.edu/',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['agsci'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'plone.app.dexterity',
        'plone.app.lockingbehavior',
        'plone.behavior',
        'zope.schema',
        'zope.interface',
        'zope.component',
        'plone.app.relationfield',
        'requests',
        'plone.app.contenttypes',
        'agsci.api',
        'agsci.leadimage',
        'agsci.person',
        'collective.autopermission',
        'collective.z3cform.datagridfield',
        'reportlab',
        'pyPdf',
        'collective.dexteritytextindexer',
        'Products.WebServerAuth',
        'eea.facetednavigation',
        'google-api-python-client',
        'googlemaps',
        'isodate',
        'xlwt',
        'xlrd',
      ],
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
      """,
    )
