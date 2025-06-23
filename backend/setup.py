from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="tessellate-ai",
    version="1.0.0",
    description="AI-powered jigsaw puzzle generator",
    author="Patrick Kalkman",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tessellate=cli:main",
        ],
    },
    python_requires=">=3.8",
)