from setuptools import setup, find_packages

setup(
    name='goth',
    version='2025.04.20.085826',
    author='jererc',
    author_email='jererc@gmail.com',
    url='https://github.com/jererc/goth',
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.10',
    install_requires=[
        'google-auth-oauthlib',
        'playwright',
    ],
    extras_require={
        'dev': ['flake8', 'pytest'],
    },
    include_package_data=True,
)
