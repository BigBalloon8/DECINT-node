import setuptools
import node
setuptools.setup(
    name="DECINT",
    version=f"{node.__version__}",
    author="Chris Rae",
    author_email="raecd123@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=["ecdsa", "numba", "click", "requests"],
    entry_points={
        "console_scripts":[
            "DECINT = DECINT:run"
    ]}
)