import setuptools
from DECINT_node import node

setuptools.setup(
    name="DECINT_node",
    version=f"{node.__version__}",
    author="Chris Rae",
    author_email="raecd123@gmail.com",
    packages=setuptools.find_packages(),
    install_requires=["ecdsa", "click", "requests"],
    entry_points={
        "console_scripts":[
            "DECINT = DECINT_node.DECINT:run"
    ]}
)