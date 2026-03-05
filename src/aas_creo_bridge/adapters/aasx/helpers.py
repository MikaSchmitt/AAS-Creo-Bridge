"""A module for representing and comparing software version identifiers.

This module defines the `Version` class, which provides functionality to
parse, store, and compare version information typically formatted as
`<name>-<major>.<minor>.<patch>`. The class supports equality and ordering
comparisons based on the semantic structure of the versions.
"""
import re
from typing import LiteralString


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

    def __init__(self, qualifier: str) -> None:
        """Parse a version qualifier string into its component parts."""
        normalized_qualifier = (qualifier
                     .replace("-", "")
                     .replace("_", ""))
        remainder = normalized_qualifier

        match = re.findall(r"[A-Za-z]+", normalized_qualifier)
        self.name = ("" if match.__len__() is 0 else match[0])
        if self.name != "":
            remainder = remainder.replace(self.name, " ").strip()

        version_match = re.match(r"(\d+(\.*\d+){0,2})", remainder)
        version = "" if version_match is None else version_match.group(1)
        remainder = remainder.replace(version, " ")
        if remainder.strip() != "":
            raise ValueError(f"Invalid version qualifier: {qualifier} cannot parse {remainder}")

        versions: list[int] = [int(v) for v in version.split(".")]
        versions.extend([0,0,0])

        self.major, self.minor, self.patch = versions[0:3]

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
