import setuptools

if __name__ == "__main__":
    setuptools.setup(
        name="pyre",
        author="Benjamin Sherman",
        author_email="bcanfieldsherman@gmail.com",
        description="Pyre: The Python RetroSheet Event File Parser",
        packages=setuptools.find_packages(),
        python_requires='>=3.8',
        install_requires=[
            'pandas',
        ],
        extras_require={
            'dev': [
                'pytest',
            ]
        }
    )
