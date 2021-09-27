from setuptools import setup, find_packages


setup(
    name="dokukratie",
    version="0.1",
    classifiers=[],
    keywords="",
    packages=find_packages("dokukratie", exclude=["parsers"]),
    package_dir={"dokukratie": "dokukratie"},
    namespace_packages=[],
    include_package_data=True,
    entry_points={"console_scripts": ["dokukratie=dokukratie.cli:cli"]},
    zip_safe=False,
    install_requires=[
        "click<8.0.0",
        "memorious",
        "mmmeta",
        "furl",
        "pyicu",
        "jq",
    ],
)
