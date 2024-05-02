# Radon Copyright 2021, University of Oxford
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from setuptools import setup, find_packages


setup(
    name="radon-web",
    version="1.1.0",
    description="Radon web interfaces",
    long_description="Different Radon Web interfaces and APIs for Radon",
    author="Jerome Fuselier",
    license="Apache License, Version 2.0",
    url="https://github.com/radon-provenance/radon-web",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
    ],
    package_dir={"": "."},
    packages=find_packages(where="."),
)

