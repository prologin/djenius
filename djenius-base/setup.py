from setuptools import setup, find_namespace_packages

setup(
    name="djenius-base",
    author="Alexandre Macabies",
    version="1.0",
    description="A collaborative jukebox for no-Internet environments.",
    url="https://github.com/prologin/djenius/",
    packages=find_namespace_packages(),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
