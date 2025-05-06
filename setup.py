from setuptools import setup, find_packages

setup(
    name="artefact",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["rich", "argparse"],
    entry_points={
        "console_scripts": ["artefact = artefact.cli:main"]
    },
    description="A minimalist toolkit with dark-mode aesthetics.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
)