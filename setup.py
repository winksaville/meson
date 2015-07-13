from setuptools import setup, find_packages

setup(
    name = "meson",
    version = "0.26.0",
    license = "Apache-2.0",
    packages = find_packages(),
    data_files = [
        ("man/man1", ["man/meson.1",
                      "mesonconf.1",
                      "mesongui.1",
                      "mesonintrospect.1",
                      "wraptool.1"]),
    ],
    scripts = ['meson.py'],
    author = "Jussi Pakkanen",
    author_email = "jpakkane@gmail.com",
    maintainer = "Igor Gnatenko",
    maintainer_email = "i.gnatenko.brain@gmail.com",
    description = "The Meson Build System",
    url = "http://mesonbuild.com/",
)
