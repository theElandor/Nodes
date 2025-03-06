# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name="Nodes",  # Required
    version="1.0.0",  # Required
    description="Distributed Algorithms Python Framework",  # Optional
    author="Matteo Eros Lugli",  # Optional
    author_email="283122@studenti.unimore.it",  # Optional
    classifiers=[  # Optional
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(include=['Nodes']),
    python_requires=">=3.7, <4",
    install_requires=["networkx", "matplotlib", "art", "pause", "prettytable"],  # Optional
)
