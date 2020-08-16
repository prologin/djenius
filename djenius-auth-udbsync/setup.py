from setuptools import setup, find_packages

setup(
    name="djenius-auth-udbsync",
    author="Alexandre Macabies",
    version="1.0",
    description="A Prologin SADM auth provider for djenius.",
    url="https://github.com/prologin/djenius/",
    packages=find_packages(),
    install_requires=["ProloginSADM", "djenius-base~=1.0"],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
