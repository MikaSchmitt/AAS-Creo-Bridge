"""A module for representing and comparing software version identifiers.

This module defines the `Version` class, which provides functionality to
parse, store, and compare version information typically formatted as
`<name>-<major>.<minor>.<patch>`. The class supports equality and ordering
comparisons based on the semantic structure of the versions.
"""

import logging
import re
from collections.abc import Iterable
from typing import Optional

from basyx.aas import model
from basyx.aas.model import base

_logger = logging.getLogger(__name__)


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

    def __init__(self, qualifier: str) -> None:
        """
        Initialize a new Version instance by parsing a qualifier string.

        The qualifier string is expected to be in a format like `<name>-<major>.<minor>.<patch>`,
        but it can also be just a version number or a name followed by a version number.
        Dashes and underscores are removed during normalization.

        :param qualifier: The version qualifier string to parse.
        :type qualifier: str
        :raises ValueError: If the version qualifier cannot be parsed.
        """
        normalized_qualifier = qualifier.replace("-", "").replace("_", "")
        remainder = normalized_qualifier

        match = re.findall(r"[A-Za-z]+", normalized_qualifier)
        self.name = "" if match.__len__() == 0 else match[0]
        if self.name != "":
            remainder = remainder.replace(self.name, " ").strip()

        version_match = re.match(r"(\d+(\.*\d+){0,2})", remainder)
        version = "" if version_match is None else version_match.group(1)
        remainder = remainder.replace(version, " ")
        if remainder.strip() != "":
            raise ValueError(
                f"Invalid version qualifier: {qualifier} cannot parse {remainder}"
            )

        versions: list[int] = [int(v) for v in version.split(".")]
        versions.extend([0, 0, 0])

        self.major, self.minor, self.patch = versions[0:3]

    def __eq__(self, other: object) -> bool:
        """
        Check if two Version instances are equal.

        :param other: The other object to compare with.
        :type other: object
        :return: True if both instances are equal, False otherwise.
        :rtype: bool
        """
        if isinstance(other, Version):
            return (
                self.name == other.name
                and self.major == other.major
                and self.minor == other.minor
                and self.patch == other.patch
            )
        return False

    def __le__(self, other: object) -> bool:
        """
        Check if this version is less than or equal to another.

        Comparison is performed component-wise: name, major, minor, then patch.

        :param other: The other version to compare with.
        :type other: object
        :return: True if this version is less than or equal to other, False otherwise.
        :rtype: bool
        """
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
        """
        Check if this version is greater than or equal to another.

        Comparison is performed component-wise: name, major, minor, then patch.

        :param other: The other version to compare with.
        :type other: object
        :return: True if this version is greater than or equal to other, False otherwise.
        :rtype: bool
        """
        if isinstance(other, Version):
            if self.name != other.name:
                return False
            if self.major != other.major:
                return self.major >= other.major
            if self.minor != other.minor:
                return self.minor >= other.minor
            return self.patch >= other.patch
        return False


def get_value(
    element: (
        model.Property
        | model.MultiLanguageProperty
        | model.Blob
        | model.File
        | model.ReferenceElement
        | model.SubmodelElementCollection
        | model.SubmodelElementList
    ),
    key: str | None = None,
) -> (
    Optional[base.ValueDataType]
    | Optional[base.MultiLanguageTextType]
    | Optional[base.BlobType]
    | Optional[base.PathType]
    | Optional[base.Reference]
    | Iterable[model.SubmodelElement]
    | None
):
    """
    Return the ``value`` of a Submodel Element, optionally resolving a nested element first.

    This helper provides convenient read-access to BaSyx AAS submodel elements:

    * If ``element`` is a namespace/container (implements :class:`basyx.aas.model.UniqueIdShortNamespace`)
      and ``key`` is provided, the function resolves the nested referable via
      ``element.get_referable(key)`` and returns that referable's ``value``.
    * Otherwise, it returns ``element.value`` directly.

    Note:
        This function does **not** catch lookup errors. If ``key`` cannot be resolved,
        any exception raised by ``get_referable`` (or by accessing ``.value``) will
        propagate to the caller.

    :param element: A submodel element (e.g., Property, File, Blob, Collection, List) or
        a container/namespace that can resolve nested referables by idShort.
    :type element: model.Property | model.MultiLanguageProperty | model.Blob | model.File |
        model.ReferenceElement | model.SubmodelElementCollection | model.SubmodelElementList
    :param key: Optional idShort of a nested referable to resolve when ``element`` is a
        ``UniqueIdShortNamespace``. Ignored when ``element`` is not a namespace/container.
    :type key: str | None
    :return: The element's resolved ``value`` (may be ``None`` depending on the element type).
    :rtype: Optional[base.ValueDataType] | Optional[base.MultiLanguageTextType] |
        Optional[base.BlobType] | Optional[base.PathType] | Optional[base.Reference] |
        Iterable[model.SubmodelElement] | None
    """

    sme = element

    # Prefer resolving nested elements by idShort when a key is provided.
    # BaSyx containers implement UniqueIdShortNamespace, but test doubles may only
    # provide a compatible get_referable() method.
    if key:
        if isinstance(element, model.UniqueIdShortNamespace) or hasattr(
            element, "get_referable"
        ):
            sme = element.get_referable(key)

    # Be defensive: some objects (e.g., collections) may not have a .value attribute.
    return getattr(sme, "value", None)
