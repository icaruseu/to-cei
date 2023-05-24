from codecs import open
from os import path

from setuptools import setup

pwd = path.abspath(path.dirname(__file__))

with open(path.join(pwd, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# This call to setup() does all the work
setup(
    name="to_cei",
    version="0.1.7",
    description="to-CEI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/icaruseu/to-cei",
    author="Daniel Jeller",
    author_email="it@icar-us.eu",
    license="GPL 3.0",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    packages=["to_cei"],
    include_package_data=True,
    install_requires=["astropy", "lxml", "requests", "xmlschema"],
)
