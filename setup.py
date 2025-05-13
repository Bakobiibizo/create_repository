from setuptools import setup, find_packages

setup(
    name="comai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "substrate-interface>=1.1.2",
        "websocket-client>=1.3.3",
    ],
)
