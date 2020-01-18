#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "tempserver",
    version = "0.0.1",
    author = "Jonatan Pålsson",
    author_email = "jonatan.p@gmail.com",
    description = "Temperature server for home brewing",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "http://github.com/jonte/tempserver",
    packages = setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating system :: Linux",
    ],
    python_requires ='>=3.6',
    install_requires = [
        "connexion[swagger-ui] >= 2.3.0, < 3",
        "simple-pid >= 0.2.4",
        "gpiozero >= 1.5.1",
        "w1thermsensor >= 1.3.0",
        "APscheduler >= 3.6.1",
    ],
    entry_points = {
        'console_scripts': [
            'tempserver = tempserver.main:main'
        ],
    },
    package_data = {
        'tempserver': [
            'data/openapi/*.yaml',
            'data/web-ui/static/*.js',
            'data/web-ui/templates/*.html',
        ]
    },
)
