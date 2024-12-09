from setuptools import find_packages, setup

setup(
    name="heurist-python-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "openai",
        "typing-extensions",
        "python-dotenv",
    ],
    python_requires=">=3.7",
    description="Unofficial python SDK for Heurist API",
    author="rex",
)
