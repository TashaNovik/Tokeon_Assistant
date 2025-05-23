from setuptools import setup, find_packages

setup(
    name="tokeon_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.1",
        "python-telegram-bot>=20.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
    ],
) 