from setuptools import setup, find_packages

setup(
    name='goth',
    version='2026.01.22.082009',
    author='jererc',
    author_email='jererc@gmail.com',
    url='https://github.com/jererc/goth',
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.10',
    install_requires=[
        'google-auth-oauthlib',
        # 'webutils @ git+https://github.com/jererc/webutils.git@main#egg=webutils',
        'webutils @ https://github.com/jererc/webutils/archive/refs/heads/main.zip',
    ],
    extras_require={
        'dev': ['flake8', 'pytest'],
    },
    include_package_data=True,
)
