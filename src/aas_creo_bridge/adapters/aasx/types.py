from dataclasses import dataclass, field

from aas_creo_bridge.adapters.aasx.helpers import Version


@dataclass(frozen=True, slots=True)
class ConsumingApplication:
    """
    Represents an application that can consume a file format.

    :ivar application_name: The name of the application.
    :type application_name: str
    :ivar application_version: The version of the application.
    :type application_version: str
    :ivar application_qualifier: A qualifier for the application version.
    :type application_qualifier: str
    """

    application_name: str
    application_version: str
    application_qualifier: str

    def __eq__(self, other: object) -> bool:
        """
        Check if two ConsumingApplication instances are equal.

        :param other: The other object to compare with.
        :type other: object
        :return: True if both instances are equal, False otherwise.
        :rtype: bool
        """
        if isinstance(other, ConsumingApplication):
            return (
                self.application_name == other.application_name
                and self.application_version == other.application_version
                and self.application_qualifier == other.application_qualifier
            )
        return False

    def __le__(self, other: object) -> bool:
        """
        Check if this application is less than or equal to another.

        Comparison is based on application name and version.

        :param other: The other application to compare with.
        :type other: object
        :return: True if this application is less than or equal to other, False otherwise.
        :rtype: bool
        """
        if isinstance(other, ConsumingApplication):
            return self.application_name == other.application_name and Version(
                self.application_version
            ) <= Version(other.application_version)
        return False

    def __ge__(self, other: object) -> bool:
        """
        Check if this application is greater than or equal to another.

        Comparison is based on application name and version.

        :param other: The other application to compare with.
        :type other: object
        :return: True if this application is greater than or equal to other, False otherwise.
        :rtype: bool
        """
        if isinstance(other, ConsumingApplication):
            return self.application_name == other.application_name and Version(
                self.application_version
            ) >= Version(other.application_version)
        return False


@dataclass(frozen=True, slots=True)
class FileFormat:
    """
    Represents a file format and its version.

    :ivar format_name: The name of the file format (e.g., "STP").
    :type format_name: str
    :ivar format_version: The version of the file format.
    :type format_version: str
    :ivar format_qualifier: A qualifier for the format version.
    :type format_qualifier: str
    """

    format_name: str
    format_version: str
    format_qualifier: str

    def __eq__(self, other: object) -> bool:
        """
        Check if two FileFormat instances are equal.

        :param other: The other object to compare with.
        :type other: object
        :return: True if both instances are equal, False otherwise.
        :rtype: bool
        """
        if isinstance(other, FileFormat):
            return (
                self.format_name == other.format_name
                and self.format_version == other.format_version
                and self.format_qualifier == other.format_qualifier
            )
        return False

    def __lt__(self, other: object) -> bool:
        """
        Check if this format version is less than another.

        :param other: The other format to compare with.
        :type other: object
        :return: True if this format version is less than other's, False otherwise.
        :rtype: bool
        """
        if isinstance(other, FileFormat):
            return (
                self.format_name == other.format_name
                and self.format_version <= other.format_version
            )
        return False

    def __gt__(self, other: object) -> bool:
        """
        Check if this format version is greater than another.

        :param other: The other format to compare with.
        :type other: object
        :return: True if this format version is greater than other's, False otherwise.
        :rtype: bool
        """
        if isinstance(other, FileFormat):
            return (
                self.format_name == other.format_name
                and self.format_version >= other.format_version
            )
        return False


@dataclass(frozen=True, slots=True)
class FileMetadata:
    """
    Metadata associated with a specific version of a file.

    :ivar file_version: The version identifier of the file.
    :type file_version: str
    :ivar filepath: Path to the file.
    :type filepath: str
    :ivar file_content_type: MIME type or content type of the file.
    :type file_content_type: str
    :ivar file_format: Format information for the file.
    :type file_format: FileFormat
    """

    file_version: str
    filepath: str
    file_content_type: str
    file_format: FileFormat


@dataclass(slots=True)
class FileData:
    """
    Collection of metadata and consuming applications for a set of related files.

    :ivar consuming_applications: List of applications that can consume these files.
    :type consuming_applications: list[ConsumingApplication]
    :ivar metadata: List of metadata entries for different versions of the file.
    :type metadata: list[FileMetadata]
    """

    consuming_applications: list[ConsumingApplication] = field(default_factory=list)
    metadata: list[FileMetadata] = field(default_factory=list)

    def add_application(self, app: ConsumingApplication) -> "FileData":
        """
        Add a consuming application to the file data.

        :param app: The application to add.
        :type app: ConsumingApplication
        :return: This instance for chaining.
        :rtype: FileData
        """
        self.consuming_applications.append(app)
        return self

    def add_metadata(self, meta: FileMetadata) -> "FileData":
        """
        Add metadata to the file data.

        :param meta: The metadata entry to add.
        :type meta: FileMetadata
        :return: This instance for chaining.
        :rtype: FileData
        """
        self.metadata.append(meta)
        return self
