"""A module for representing and comparing software version identifiers.

This module defines the `Version` class, which provides functionality to
parse, store, and compare version information typically formatted as
`<name>-<major>.<minor>.<patch>`. The class supports equality and ordering
comparisons based on the semantic structure of the versions.
"""
import re

class Version:

    """
    Represents a software version defined by a name and a semantic versioning
    scheme including major, minor, and patch numbers.

    This class allows parsing, comparing, and normalizing software version
    qualifiers. It supports equality and relational comparisons to determine
    the ordering of versions.

    :ivar name: The name associated with the version, typically representing
        the software or library name.
    :type name: str
    :ivar major: The major version component of the version number.
    :type major: int
    :ivar minor: The minor version component of the version number.
    :type minor: int
    :ivar patch: The patch version component of the version number.
    :type patch: int
    """
    def __init__(self,name: str, major: int, minor: int, patch: int) -> None:
        self.name = name
        self.major = major
        self.minor = minor
        self.patch = patch

    """
    Parses a version qualifier string into its component parts.
    """
    def __init__(self, qualifier: str) -> None:
        normalized_qualifier = (qualifier
                     .replace("-", "")
                     .replace("_", ""))

        self.name = re.fullmatch(r"[A-Za-z]+", normalized_qualifier).group(1)
        remainder = re.sub(r"[A-Za-z]+", r"", normalized_qualifier, count=1)

        version = re.fullmatch(r"(\d+\.*)+", remainder).group(1)
        remainder = re.sub(r"(\d+\.*)+", r"", normalized_qualifier)
        if remainder != "":
            raise ValueError(f"Invalid version qualifier: {qualifier}")
        self.major, self.minor, self.patch = version.split(".")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Version):
            return (self.name == other.name
                    and self.major == other.major
                    and self.minor == other.minor
                    and self.patch == other.patch)
        return False

    def __le__(self, other: object) -> bool:
        if isinstance(other, Version):
            if self.name != other.name:
                return False
            if self.major != other.major:
                return self.major <= other.major
            if self.minor != other.minor:
                return self.minor <= other.minor
            return self.patch <= other.patch
        return False

    def __ge__(self, other: object) -> bool:
        if isinstance(other, Version):
            if self.name != other.name:
                return False
            if self.major != other.major:
                return self.major >= other.major
            if self.minor != other.minor:
                return self.minor >= other.minor
            return self.patch >= other.patch
        return False
