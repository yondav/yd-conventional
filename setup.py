from setuptools import setup

setup(
    name='cz_yd_conventional',
    version='0.1.0',
    py_modules=['cz_yd_conventional'],
    license='Not open source',
    long_description='conventional commits configured for linear',
    install_requires=['commitizen'],
    entry_points={'commitizen.plugin': ['cz_yd_conventional = cz_yd_conventional:YDConventional',],
    },
)
