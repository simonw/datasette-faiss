from setuptools import setup
import os

VERSION = "0.2"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-faiss",
    description="Maintain a FAISS index for specified Datasette tables",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-faiss",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-faiss/issues",
        "CI": "https://github.com/simonw/datasette-faiss/actions",
        "Changelog": "https://github.com/simonw/datasette-faiss/releases",
    },
    license="Apache License, Version 2.0",
    classifiers=[
        "Framework :: Datasette",
        "License :: OSI Approved :: Apache Software License",
    ],
    version=VERSION,
    packages=["datasette_faiss"],
    entry_points={"datasette": ["faiss = datasette_faiss"]},
    install_requires=["datasette", "faiss-cpu", "numpy"],
    extras_require={"test": ["pytest", "pytest-asyncio"]},
    python_requires=">=3.7",
)
