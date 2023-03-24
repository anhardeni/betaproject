from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in singlecore_apps/__init__.py
from singlecore_apps import __version__ as version

setup(
	name="singlecore_apps",
	version=version,
	description="Single Interface To Ceisa40 dan perijinan",
	author="AnharDeni",
	author_email="anhardeni@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
