from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="website-scraper",
    version="0.1.4",
    author="Misha Lubich",
    author_email="michaelle.lubich@gmail.com",
    description="A robust, multiprocessing-enabled web scraper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ml-lubich/website-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "fake-useragent>=0.1.11",
        "tqdm>=4.50.0",
        "lxml>=4.9.0",
        "aiohttp>=3.9.0",
        "aiofiles>=23.0.0",
        "playwright>=1.40.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.900",
            "build>=0.7.0",
        ],
        "undetected": [
            "undetected-chromedriver>=3.5.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'website-scraper=website_scraper.cli:main',
        ],
    },
) 