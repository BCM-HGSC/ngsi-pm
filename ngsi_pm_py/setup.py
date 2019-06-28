"""A setuptools based setup module for bhaou_intake."""


from os import path
# Always prefer setuptools over distutils
from setuptools import setup, find_packages

HERE = path.abspath(path.dirname(__file__))
NAME = "ngsi_pm_py"

# Load the version
with open(path.join(HERE, NAME, "version.py")) as version_file:
    exec(version_file.read())

# Get the long description from the README file
with open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

REQUIREMENTS = [
    "openpyxl"
]

TEST_REQUIREMENTS = [
    "pytest==3.0.7",
]

SETUP_REQUIREMENTS = [
    "pytest-runner",
]

setup(
    name=NAME,
    version=__version__,
    description="Highly customized scrips for working with NGSI metadata.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Baylor College of Medicine Human Genome Sequencing Center",
    author_email="questions@hgsc.bcm.edu",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    setup_requires=SETUP_REQUIREMENTS,
    entry_points={
        "console_scripts": [
            "annotate_worklist=ngsi_pm_py.annotate_worklist:main",
            "cram_worklist=ngsi_pm_py.cram_worklist:main",
            "dump_js_barcodes=ngsi_pm_py.dump_js_barcodes:main",
            "dump_rgs=ngsi_pm_py.dump_rgs:main",
            "dump_xl_bam_paths=ngsi_pm_py.dump_xl_bam_paths:main",
            "dump_xl_barcodes=ngsi_pm_py.dump_xl_barcodes:main",
            "dump_xl_cram_paths=ngsi_pm_py.dump_xl_cram_paths:main",
            "globus_worklist=ngsi_pm_py.globus_worklist:main",
            "gmkf_worklist=ngsi_pm_py.gmkf_worklist:main",
            "mplx_qc=ngsi_pm_py.mplx_qc:main",
            "mplx_worklist=ngsi_pm_py.mplx_worklist:main",
            "topmed_worklist=ngsi_pm_py.topmed_worklist:main",
            "vcf_worklist=ngsi_pm_py.vcf_worklist:main"
        ],
    },
)
