from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="asset_system",
    version="1.0.0",
    description="A fully independent Asset Management System built on Frappe Framework",
    author="Aaron Shenny",
    author_email="",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
