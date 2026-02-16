from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in his/__init__.py
from his import __version__ as version

setup(
	name="his",
	version=version,
	description="Rasiin HIS",
	author="Rasiin Tech",
	author_email="rasiin",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
