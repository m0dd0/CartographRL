import setuptools

setuptools.setup(
    name="carthographRL",
    version="0.0.1",
    author="Moritz Hesche",
    author_email="mo.hesche@gmail.com",
    # description="",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    # url="",
    classifiers=["Programming Language :: Python :: 3"],
    packages=setuptools.find_packages(),
    python_requires="~=3.10",
    install_requires=[
        "numpy",
        "scikit-image",
        "gymnasium",
        "nptyping",
        "matplotlib",
        "flask",
    ],
    extras_require={"dev": ["black", "pylint", "jupyter", "ipykernel"]},
    include_package_data=True,
    use_scm_version=True,
)
