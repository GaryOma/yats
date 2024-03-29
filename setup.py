import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="yats",
    version="1.0.0",
    description="A fast lightweight Twitter scraper",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/GaryOma/yats",
    author="Gary SUBLET",
    author_email="gary.sublet@hotmail.fr",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=["yats"],
    include_package_data=True,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "yats = yats.__main__:main",
        ]
    },
)
