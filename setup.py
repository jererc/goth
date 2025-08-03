from setuptools import setup, find_packages

setup(
    name='goth',
    version='2025.08.03.152548',
    author='jererc',
    author_email='jererc@gmail.com',
    url='https://github.com/jererc/goth',
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.10',
    install_requires=[
        'google-auth-oauthlib',
        'playwright',
        # 'svcutils @ git+https://github.com/jererc/svcutils.git@main#egg=svcutils',
        'svcutils @ https://github.com/jererc/svcutils/archive/refs/heads/main.zip',
    ],
    extras_require={
        'dev': ['flake8', 'pytest'],
    },
    include_package_data=True,
)
