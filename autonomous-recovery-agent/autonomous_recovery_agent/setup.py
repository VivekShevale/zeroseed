from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
    "Flask>=2.0.0",
    "pymongo>=4.0.0",
    "psutil>=5.9.0",
    "pydantic>=2.0.0",
    "requests>=2.28.0",
    "python-dotenv>=0.20.0",
    "click>=8.1.0",
    "pyyaml>=6.0",
    "watchdog>=3.0.0"
]

setup(
    name="autonomous-recovery-agent",
    version="3.0.4",
    author="Autonomous Recovery Team",
    author_email="support@autonomous-recovery.com",
    description="Autonomous monitoring and recovery agent for Flask + MongoDB applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/autonomous-recovery-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: System :: Monitoring",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "recovery-agent=autonomous_recovery_agent.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "autonomous_recovery_agent": ["templates/*.html", "static/*"],
    },
)
