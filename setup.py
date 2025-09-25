from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="social_media_monitor",
    version="1.0.0",
    description="Social Media Brand Monitoring & Crisis Detection System",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "social-media-monitor=social_media_monitor.main:run_scheduler",
            "social-media-dashboard=social_media_monitor.dashboard.app:main",
        ],
    },
)