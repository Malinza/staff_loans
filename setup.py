from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in staff_loans/__init__.py
from staff_loans import __version__ as version

setup(
	name="staff_loans",
	version=version,
	description="An App that manages staff loans and loan rescheduling",
	author="VV System Developers LTD",
	author_email="ibrahim@vvsdtz.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
