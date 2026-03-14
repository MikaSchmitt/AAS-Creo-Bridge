"""A module for representing and comparing software version identifiers.

This module defines the `Version` class, which provides functionality to
parse, store, and compare version information typically formatted as
`<name>-<major>.<minor>.<patch>`. The class supports equality and ordering
comparisons based on the semantic structure of the versions.
"""

import logging
import os
import tempfile
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path
from typing import Optional, TypeVar

from basyx.aas import model
from basyx.aas.model import base

from aas_adapter.models import FileFormat

T = TypeVar("T")

_logger = logging.getLogger(__name__)


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


def check_expected_model(value: object, expected_type: type[T]) -> T:
    """
    Validate that ``value`` is an instance of ``expected_type`` and return it
    as the expected type.

    This helper is mainly used when reading loosely typed AAS model objects and
    narrowing them to the concrete type required by the caller.

    :param value: The object to validate.
    :type value: object
    :param expected_type: The expected runtime type of ``value``.
    :type expected_type: type[T]
    :return: ``value`` cast to ``T`` if the type check succeeds.
    :rtype: T
    :raises ValueError: If ``value`` is not an instance of ``expected_type``.
    """
    if not isinstance(value, expected_type):
        raise ValueError(
            f"Invalid file: expected {expected_type.__name__}, got {type(value).__name__}  "
            f"Please check the validity of the AAS."
        )
    return value


CACHE_DIR = Path(tempfile.mkdtemp(prefix="aas_adapter_"))
CACHE_FILE = os.path.join(CACHE_DIR, 'cadenas_list.xml')
TTL = 86400  # 1 day in seconds
URL_CADENAS_FORMAT_LIST = 'https://cadenas-admin.partcommunity.com/PARTcommunityManagement/FormatList?portal=3dfindit'


def get_cadenas_list():
    """
    Fetches the Cadenas format list XML from the online source if the cache is expired or missing.
    Returns the root element of the XML tree, or ``None`` if neither a valid
    online response nor a readable cached file is available.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    def _load_cached_root():
        """Try to load and parse the cached XML file, returning its root or None on failure."""
        if not os.path.exists(CACHE_FILE):
            return None
        try:
            tree = ET.parse(CACHE_FILE)
            return tree.getroot()
        except (ET.ParseError, OSError) as exc:
            _logger.warning("Failed to parse cached Cadenas format list '%s': %s", CACHE_FILE, exc)
            return None

    # Use cache if it exists and is still within TTL
    if os.path.exists(CACHE_FILE) and time.time() - os.path.getmtime(CACHE_FILE) < TTL:
        cached_root = _load_cached_root()
        if cached_root is not None:
            return cached_root
        # If cache is invalid, fall through to try network fetch

    try:
        with urllib.request.urlopen(URL_CADENAS_FORMAT_LIST, timeout=10) as response:
            response_text = response.read().decode("utf-8")
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(response_text)
        return ET.fromstring(response_text)
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, ET.ParseError) as exc:
        _logger.warning(
            "Failed to fetch or parse online Cadenas format list from '%s': %s",
            URL_CADENAS_FORMAT_LIST,
            exc,
        )
        # Fall back to any cached data (even if stale)
        cached_root = _load_cached_root()
        if cached_root is not None:
            return cached_root
        # As a last resort, return None so callers can handle missing data
        return None


def mcad_doc_name_to_cadenas_format(doc_name: str) -> FileFormat | None:
    cadenas_list = get_cadenas_list()
    if cadenas_list is None:
        return None

    search_query = doc_name.lower().strip()

    for fmt in cadenas_list.findall("format"):
        fmt_name = (fmt.findtext("name") or "").strip()
        fmt_version = (fmt.findtext("version") or "").strip()
        fmt_qualifier = (fmt.findtext("qualifier") or "").strip()

        full_name = f"{fmt_name} {fmt_version}".strip().lower()
        qualifier = f"{fmt_qualifier}".strip().lower()

        if full_name in search_query or qualifier in search_query:
            return FileFormat(fmt_name, fmt_version, fmt_qualifier)

    return None
