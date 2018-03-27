from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Doc: http://pythonhosted.org/setuptools/setuptools.html#including-data-files.
setup(
    name='kiwix-build',
    version="0.1",
    description=('A tool to build kiwix and openzim projects.'),
    long_description=long_description,
    url='https://github.com/kiwix/kiwix-build/',
    author='Matthieu Gautier',
    author_email='mgautier@kymeria.fr',
    license='GPLv3',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'kiwix-build = kiwixbuild:main'
        ]
    }
)
