from setuptools import setup, find_packages

version = "1.0.0"

setup(
    name="senaite.hgumba",
    version=version,
    description="Customizacoes Hospital Geral Umba para SENAITE",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["senaite"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "senaite.core",
        "archetypes.schemaextender",
        "reportlab",
        "matplotlib",
        "Pillow",
    ],
    entry_points={},
)
