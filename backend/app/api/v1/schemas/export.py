"""Pydantic schemas for SARIF v2.1.0 Exporter and GitHub Webhook Integration."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# SARIF v2.1.0 Standard Schemas (OASIS Specification)
# ---------------------------------------------------------------------------


class SarifMessage(BaseModel):
    text: str


class SarifArtifactLocation(BaseModel):
    uri: str


class SarifRegion(BaseModel):
    startLine: int = Field(..., ge=1)
    endLine: int | None = Field(default=None, ge=1)
    startColumn: int | None = Field(default=1, ge=1)


class SarifPhysicalLocation(BaseModel):
    artifactLocation: SarifArtifactLocation
    region: SarifRegion | None = None


class SarifLocation(BaseModel):
    physicalLocation: SarifPhysicalLocation


class SarifReportingDescriptor(BaseModel):
    id: str
    name: str | None = None
    shortDescription: SarifMessage
    fullDescription: SarifMessage | None = None
    helpUri: str | None = None
    defaultConfiguration: dict[str, Any] = Field(default_factory=lambda: {"level": "warning"})


class SarifToolComponent(BaseModel):
    name: str = "CodeSentinel AI"
    version: str = "1.0.0"
    informationUri: str = "https://github.com/farazrasul0-cmd/CodeSentinel"
    rules: list[SarifReportingDescriptor] = Field(default_factory=list)


class SarifTool(BaseModel):
    driver: SarifToolComponent


class SarifReplacement(BaseModel):
    deletedRegion: SarifRegion
    insertedContent: SarifMessage


class SarifArtifactChange(BaseModel):
    artifactLocation: SarifArtifactLocation
    replacements: list[SarifReplacement] = Field(default_factory=list)


class SarifFix(BaseModel):
    description: SarifMessage
    artifactChanges: list[SarifArtifactChange] = Field(default_factory=list)


class SarifResult(BaseModel):
    ruleId: str
    level: Literal["error", "warning", "note", "none"] = "warning"
    message: SarifMessage
    locations: list[SarifLocation] = Field(default_factory=list)
    fixes: list[SarifFix] | None = None


class SarifRun(BaseModel):
    tool: SarifTool
    results: list[SarifResult] = Field(default_factory=list)


class SarifLog(BaseModel):
    """Root SARIF v2.1.0 document format for GitHub Code Scanning ingestion."""

    schema_uri: str = Field(
        default="https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        alias="$schema",
    )
    version: str = "2.1.0"
    runs: list[SarifRun] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


# ---------------------------------------------------------------------------
# GitHub Webhook Schemas
# ---------------------------------------------------------------------------


class GitHubHeadBase(BaseModel):
    sha: str
    ref: str


class GitHubPullRequest(BaseModel):
    number: int
    title: str
    head: GitHubHeadBase
    base: GitHubHeadBase
    html_url: str | None = None


class GitHubRepoInfo(BaseModel):
    id: int
    name: str
    full_name: str
    clone_url: str
    default_branch: str = "main"


class GitHubWebhookPayload(BaseModel):
    action: str
    pull_request: GitHubPullRequest | None = None
    repository: GitHubRepoInfo
    sender: dict[str, Any] = Field(default_factory=dict)
