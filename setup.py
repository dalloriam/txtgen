from setuptools import setup, find_packages
import re

version = ""
with open("txtgen/__init__.py") as f:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE
    ).group(1)

if not version:
    raise RuntimeError("Version is not set")

readme = "See https://github.com/dalloriam/txtgen for README."

setup(
    name="txtgen",
    author="dalloriam",
    author_email="dalloriam@gmail.com",
    url="https://github.com/dalloriam/txtgen",
    version=version,
    packages=find_packages(),
    license="MIT",
    description="Blazing-fast text generation DSL.",
    long_description=readme,
    install_requires=[],
)
