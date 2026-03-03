from dataclasses import dataclass, field

from aas_creo_bridge.adapters.aasx.helpers import Version


@dataclass(frozen=True, slots=True)
class ConsumingApplication:
    application_name: str
    application_version: str
    application_qualifier: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ConsumingApplication):
            return (self.application_name == other.application_name
                    and self.application_version == other.application_version
                    and self.application_qualifier == other.application_qualifier)
        return False

    def __le__(self, other: object) -> bool:
        if isinstance(other, ConsumingApplication):
            return (self.application_name == other.application_name
                    and Version(self.application_version) <= Version(self.application_version))
        return False

    def __ge__(self, other: object) -> bool:
        if isinstance(other, ConsumingApplication):
            return (self.application_name == other.application_name
                    and Version(self.application_version) >= Version(other.application_version))
        return False

@dataclass(frozen=True, slots=True)
class FileFormat:
    format_name: str
    format_version: str
    format_qualifier: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FileFormat):
            return (self.format_name == other.format_name
                    and self.format_version == other.format_version
                    and self.format_qualifier == other.format_qualifier)
        return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, FileFormat):
            return (self.format_name == other.format_name
                    and self.format_version <= other.format_version)
        return False

    def __gt__(self, other: object) -> bool:
        if isinstance(other, FileFormat):
            return (self.format_name == other.format_name
                    and self.format_version >= other.format_version)
        return False

@dataclass(frozen=True, slots=True)
class FileMetadata:
    file_version: str
    filepath: str
    file_content_type: str
    file_format: FileFormat

@dataclass(slots=True)
class FileData:
    consuming_applications: list[ConsumingApplication] = field(default_factory=list)
    metadata: list[FileMetadata] = field(default_factory=list)

    def add_application(self, app: ConsumingApplication) -> "FileData":
        self.consuming_applications.append(app)
        return self

    def add_metadata(self, meta: FileMetadata) -> "FileData":
        self.metadata.append(meta)
        return self