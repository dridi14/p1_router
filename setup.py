from setuptools import setup, find_packages

setup(
    name="p1_router",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pillow",
        "opencv-python",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "p1_router_launcher=launcher:P1RouterLauncher.main",
            "p1_router_main=p1_router.main:main",
        ],
    },
    author="P1 Router Team",
    description="P1 Routing Module for lighting control",
    python_requires=">=3.6",
) 