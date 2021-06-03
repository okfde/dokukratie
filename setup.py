from setuptools import setup, find_packages


setup(
    name="dokukratie",
    version="0.1",
    classifiers=[],
    keywords="",
    packages=find_packages("dokukratie"),
    package_dir={"dokukratie": "dokukratie"},
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "memorious @ git+https://github.com/alephdata/memorious",  # FIXME
        "mmmeta",
        "furl",
        "pyicu",
    ],
)
