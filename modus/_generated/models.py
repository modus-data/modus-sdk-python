# Auto-generated from the Modus API schema. Do not edit by hand.
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PatSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ..., description='Token id (UUID).', examples=['5f2c1b3a-0000-4000-a000-000000000001']
    )
    owner_user_id: str | None = Field(
        ...,
        alias='ownerUserId',
        description='Clerk user id of the token owner.',
        examples=['user_2abc...'],
    )
    owner_email: str | None = Field(
        ...,
        alias='ownerEmail',
        description='Email of the token owner, resolved from Clerk. Falls back to the owner user id when Clerk cannot resolve an email.',
        examples=['jane@acme.com'],
    )
    name: str | None = Field(..., description='Human-readable name.', examples=['GitHub Actions deploy'])
    prefix: str = Field(
        ...,
        description='The 16-hex prefix segment of the token — its stable lookup identifier.',
        examples=['0123456789abcdef'],
    )
    visible_suffix: str = Field(
        ...,
        alias='visibleSuffix',
        description='Last 4 characters of the token secret, shown so a token can be identified.',
        examples=['A1b2'],
    )
    scopes: list[str] = Field(
        ..., description='Scopes granted to the token.', examples=[['skills:read', 'context:read']]
    )
    expires_at: str | None = Field(
        None,
        alias='expiresAt',
        description='Expiry timestamp. Null for non-expiring tokens.',
        examples=['2027-05-11T00:00:00Z'],
    )
    last_used_at: str | None = Field(
        None,
        alias='lastUsedAt',
        description='Most recent successful authentication using this token. Null if never used.',
        examples=['2026-05-11T11:42:13Z'],
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='When the token was created.',
        examples=['2026-05-11T10:00:00Z'],
    )
    revoked_at: str | None = Field(
        None,
        alias='revokedAt',
        description='When the token was revoked. Null if the token is still active.',
        examples=[None],
    )


class Code(str, Enum):
    validation = 'VALIDATION'
    bad_request = 'BAD_REQUEST'
    unauthorized = 'UNAUTHORIZED'
    forbidden = 'FORBIDDEN'
    not_found = 'NOT_FOUND'
    conflict = 'CONFLICT'
    rate_limited = 'RATE_LIMITED'
    internal_error = 'INTERNAL_ERROR'


class Status(str, Enum):
    invalid_argument = 'INVALID_ARGUMENT'
    unauthenticated = 'UNAUTHENTICATED'
    permission_denied = 'PERMISSION_DENIED'
    not_found = 'NOT_FOUND'
    already_exists = 'ALREADY_EXISTS'
    resource_exhausted = 'RESOURCE_EXHAUSTED'
    internal = 'INTERNAL'


class ErrorEnvelopeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    code: Code = Field(..., description='Modus-specific machine code.')
    status: Status = Field(..., description='AIP-193 canonical status string.')
    message: str = Field(..., examples=['Skill was not found or you lack permission.'])
    request_id: str = Field(..., alias='requestId', examples=['req_01HQ7K8ABCDEFGHIJKLMNOPQRS'])
    info: dict[str, Any] | None = Field(
        None,
        description="Optional domain-specific context. Shape varies per endpoint — see the operation's error response examples.",
        examples=[{'skillId': 'sk_abc123'}],
    )


class ErrorResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    error: ErrorEnvelopeDto


class GroupPermissionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    use: bool = Field(
        ...,
        description='Whether members of this group may use (run / invoke) the skill.',
        examples=[True],
    )
    manage: bool = Field(
        ...,
        description='Whether members of this group may manage (edit / deploy / delete) the skill.',
        examples=[False],
    )


class SharedUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str = Field(
        ...,
        description='Lowercased email of a user explicitly granted access to a private skill.',
        examples=['alice@example.com'],
    )
    added_at: str | None = Field(
        None,
        alias='addedAt',
        description='ISO-8601 timestamp at which this user was added to the share list.',
        examples=['2026-05-01T10:00:00Z'],
    )
    added_by: str | None = Field(
        None,
        alias='addedBy',
        description='Clerk user id of the principal that added this share entry.',
        examples=['user_2abc'],
    )
    user_id: str | None = Field(
        None,
        alias='userId',
        description='Clerk user id of the invited user. Stored for display; access checks use email.',
        examples=['user_2xyz'],
    )


class Visibility(str, Enum):
    shared = 'shared'
    private = 'private'


class AccessConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    visibility: Visibility = Field(
        ...,
        description='Visibility tier. `shared` applies the group-permission map; `private` ignores groups and uses owner + sharedWith for access.',
        examples=['shared'],
    )
    group_permissions: dict[str, GroupPermissionDto] = Field(
        ...,
        alias='groupPermissions',
        description='Map of group UUID -> { use, manage } booleans. Empty object when visibility is `private`.',
        examples=[{'group_eng_uuid': {'use': True, 'manage': False}}],
    )
    guardrails: list[str] = Field(
        ...,
        description='Free-form guardrail labels enforced at run time (e.g. PII redaction profile names).',
        examples=[[]],
    )
    shared_with: list[SharedUserDto] = Field(
        ...,
        alias='sharedWith',
        description='Per-user share entries used for private-visibility skills.',
        examples=[[]],
    )
    owner_user_id: str | None = Field(
        None,
        alias='ownerUserId',
        description='Clerk user id of the skill owner. Set on first write; cannot be changed by clients.',
        examples=['user_2abc'],
    )
    owner_email: str | None = Field(
        None,
        alias='ownerEmail',
        description='Lowercased email of the skill owner. Used by private-skill ACL when owner email matches.',
        examples=['alice@example.com'],
    )


class PendingOwnershipTransferDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    pending_owner_user_id: str = Field(
        ...,
        alias='pendingOwnerUserId',
        description='Clerk user id of the org member who will become owner once they accept.',
        examples=['user_2abc123def456'],
    )
    pending_owner_email: str | None = Field(
        None,
        alias='pendingOwnerEmail',
        description='Email of the pending recipient, resolved from org membership at request time.',
        examples=['newowner@example.com'],
    )
    requested_by_user_id: str = Field(
        ...,
        alias='requestedByUserId',
        description='Clerk user id of the member who requested the transfer (the current owner).',
        examples=['user_2xyz789ghi012'],
    )
    requested_at: str = Field(
        ...,
        alias='requestedAt',
        description='When the transfer was requested.',
        examples=['2026-06-05T12:00:00.000Z'],
    )


class SkillVariationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_output: str = Field(
        ...,
        alias='expectedOutput',
        description='Free-form expected-output prompt that scopes the skill’s reply.',
        examples=['A 3-bullet summary highlighting churn risk drivers.'],
    )
    instructions: list[str] = Field(
        ...,
        description='Ordered list of instruction blocks. Each entry is a free-form string the builder rendered into the system prompt.',
        examples=[['Be concise.', 'Always justify the score.']],
    )
    model: str | None = Field(
        ...,
        description='Provider-prefixed model id. The orchestrator routes by prefix.',
        examples=['anthropic/claude-sonnet-4.6'],
    )
    toolset: dict[str, Any] = Field(
        ...,
        description='Builder-managed toolset descriptor. Map of `{toolName: config}`; opaque to the API surface.',
        examples=[{'web_search': {'enabled': True}, 'calculator': {'enabled': True}}],
    )
    connection_set: list[dict[str, Any]] = Field(
        ...,
        alias='connectionSet',
        description='Connection selections (DBs, integrations) attached to the variation. Each entry is a builder-managed object; opaque here.',
    )
    context_selections: list[dict[str, Any]] = Field(
        ...,
        alias='contextSelections',
        description='Context selections attached to the variation. Free-form builder objects.',
    )
    evaluations: list[dict[str, Any]] = Field(
        ...,
        description='Evaluation entries (task + expected-output pairs) saved for this variation.',
    )
    interfaces: list[dict[str, Any]] = Field(
        ...,
        description='Interface entries attached to the variation (chat, slack, webhook, etc.). Each is a builder-managed object.',
    )
    supervision_subordinate_ids: list[str] = Field(
        ...,
        alias='supervisionSubordinateIds',
        description='IDs of skills supervised by this skill (when it is a manager). Stringified for wire stability.',
        examples=[['12', '17']],
    )
    supervision_subordinate_descriptions: dict[str, str] = Field(
        ...,
        alias='supervisionSubordinateDescriptions',
        description='Map of subordinateId -> manager-provided description blurb.',
        examples=[{'12': 'Reads warehouse facts', '17': 'Drafts the report'}],
    )


class Status1(str, Enum):
    draft = 'draft'
    active = 'active'
    deleted = 'deleted'


class ManageDenial(str, Enum):
    not_owner = 'not_owner'
    needs_group_manage = 'needs_group_manage'


class SkillDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: float = Field(
        ...,
        description='Numeric skill id (stable per-org; not reused after delete).',
        examples=[42],
    )
    slug: str | None = Field(
        ...,
        description='URL-safe slug used in human-readable links. Unique per org.',
        examples=['customer-churn-analyzer-a3f'],
    )
    name: str | None = Field(
        ...,
        description='Display name of the skill. Shown in the builder and in run logs.',
        examples=['Customer Churn Analyzer'],
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description of what this skill does.',
        examples=['Predicts churn risk for a customer given a 90-day usage window.'],
    )
    status: Status1 = Field(
        ...,
        description='Lifecycle status. `draft` = never deployed. `active` = deployed. `deleted` = soft-deleted.',
        examples=['active'],
    )
    org_uuid: str = Field(
        ...,
        alias='orgUuid',
        description='Org UUID this skill belongs to. Matches the caller’s principal.',
        examples=['00000000-0000-0000-0000-000000000001'],
    )
    active_variation_id: str | None = Field(
        None,
        alias='activeVariationId',
        description='Active (deployed) variation id. Null until the skill is first deployed.',
        examples=['00000000-0000-4000-a000-000000000100'],
    )
    draft_variation_id: str | None = Field(
        None,
        alias='draftVariationId',
        description='Most recent draft variation id. Null when there is no draft pending.',
        examples=['00000000-0000-4000-a000-000000000101'],
    )
    has_unpublished_changes: bool = Field(
        ...,
        alias='hasUnpublishedChanges',
        description='True when the draft variation differs from the active variation (deploy would publish changes).',
        examples=[False],
    )
    access_config: AccessConfigDto = Field(
        ...,
        alias='accessConfig',
        description='Access configuration — who in the org can use / manage this skill.',
    )
    pending_ownership_transfer: (
        PendingOwnershipTransferDto | None
    ) = (
        Field(None, alias='pendingOwnershipTransfer', description='Pending ownership transfer awaiting recipient acceptance. Absent when no request is in flight.')
    )
    variation: SkillVariationDto | None = Field(
        None,
        description='Variation-detail payload (`toolset`, `instructions`, `model`, etc.) for the requested view. Present on detail responses; absent on list rows.',
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='Creation timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='Most recent update timestamp.',
        examples=['2026-05-11T10:00:00.000Z'],
    )
    deleted_at: str | None = Field(
        None,
        alias='deletedAt',
        description='Soft-delete timestamp. Null for active skills.',
        examples=[None],
    )
    can_manage: bool = Field(
        ...,
        alias='canManage',
        description='Whether the requesting principal can manage (edit/delete/deploy) this skill. Derived server-side from the principal + accessConfig. Present on every Skill response.',
        examples=[True],
    )
    can_use: bool = Field(
        ...,
        alias='canUse',
        description='Whether the requesting principal can use (run, view history of) this skill. Derived server-side from the principal + accessConfig.',
        examples=[True],
    )
    manage_denial: ManageDenial | None = Field(
        ...,
        alias='manageDenial',
        description='Why `canManage` is false, for client-facing guidance: `needs_group_manage` (shared, but no group you belong to grants Manage) or `not_owner` (private, and you are not the owner). `null` when `canManage` is true.',
        examples=['needs_group_manage'],
    )


class ListSkillsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    skills: list[SkillDto] = Field(
        ...,
        description='Page of skills the caller can at least `use`. Skills the caller cannot see are filtered out (not enumerated).',
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
        examples=['eyJsYXN0SWQiOjQyfQ'],
    )


class ToolsetToolDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Stable id of the tool (matches the registry key on the agent runtime).',
        examples=['web_search'],
    )
    enabled: bool | None = Field(
        None,
        description='Whether this tool is enabled for the skill. Defaults to true when absent.',
        examples=[True],
    )
    config: dict[str, Any] | None = Field(
        None,
        description='Free-form tool-specific configuration (e.g. allowlists). Schema varies per tool.',
        examples=[{'max_results': 5}],
    )


class ToolsetDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    tools: list[ToolsetToolDto] | None = Field(
        None,
        description='List of tools the skill may invoke.',
        examples=[[{'id': 'web_search', 'enabled': True}]],
    )


class CreateSkillDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        ...,
        description='Display name for the skill. Will be slugified into a URL-safe path.',
        examples=['Customer Churn Analyzer'],
        max_length=200,
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description shown in the builder and skill catalog.',
        examples=['Predicts churn risk for a customer given a 90-day usage window.'],
    )
    expected_output: str | None = Field(
        None,
        alias='expectedOutput',
        description='Optional summary of the expected output schema, used when supervising other skills.',
        examples=['JSON: { churn_probability: number, drivers: string[] }'],
    )
    instructions: list[str] | None = Field(
        None,
        description='Ordered list of system-prompt instruction fragments. Joined at run time.',
        examples=[['You are a senior data analyst.', 'Always cite the SQL you used.']],
    )
    toolset: ToolsetDto | None = Field(
        None,
        description='Toolset configuration (tools this skill may invoke). Service sanitizes the shape on write.',
    )
    model: str | None = Field(
        None,
        description='Model identifier to use at run time (e.g. `claude-sonnet-4-5`). Falls back to org default when absent.',
        examples=['claude-sonnet-4-5'],
    )
    connection_set: list[dict[str, Any]] | None = Field(
        None,
        alias='connectionSet',
        description='List of integration connection refs available to this skill. Shape is integration-specific.',
        examples=[[]],
    )
    context_selections: list[dict[str, Any]] | None = Field(
        None,
        alias='contextSelections',
        description='Selected context items (sources / docs) the skill may read.',
        examples=[[]],
    )
    interfaces: list[dict[str, Any]] | None = Field(
        None,
        description='Interface configuration (chat, API, webhook…). Shape is interface-specific.',
        examples=[[]],
    )
    access_config: AccessConfigDto | None = Field(
        None,
        alias='accessConfig',
        description='Access configuration. Omit to use the default (full-org shared with use + manage).',
    )


class SkillMcpInterfaceConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    core_tools: dict[str, Any] | None = Field(
        None,
        alias='coreTools',
        description='Built-in MCP tools (chat, get_context) exposed by this skill.',
    )
    mcp_tool_exposure: dict[str, Any] | None = Field(
        None,
        alias='mcpToolExposure',
        description='Outbound tool exposure for MCP clients (subset or all).',
    )


class PatchSkillMcpConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    config: SkillMcpInterfaceConfigDto = Field(
        ...,
        description='Full MCP interface config to apply live on the published skill (and mirrored to draft when forked).',
    )


class PatchSkillMcpConfigResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    config: SkillMcpInterfaceConfigDto = Field(
        ..., description='Sanitized MCP config now stored on the published variation.'
    )


class UpdateSkillDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        None,
        description='New display name for the skill.',
        examples=['Customer Churn Analyzer v2'],
        max_length=200,
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Updated description.',
        examples=['Predicts churn risk over a 180-day window.'],
    )
    expected_output: str | None = Field(
        None,
        alias='expectedOutput',
        description='Updated expected-output summary, used when this skill is supervised.',
        examples=['JSON: { churn_probability: number }'],
    )
    instructions: list[str] | None = Field(
        None,
        description='Updated instruction fragments. Replaces the prior list when present.',
        examples=[['You are a senior data analyst.']],
    )
    toolset: ToolsetDto | None = Field(None, description='Updated toolset configuration.')
    model: str | None = Field(
        None,
        description='Updated model id. Pass `null` (explicit) to clear and use the org default.',
        examples=['claude-sonnet-4-5'],
    )
    connection_set: list[dict[str, Any]] | None = Field(
        None,
        alias='connectionSet',
        description='Updated connection set. Shape is integration-specific.',
        examples=[[]],
    )
    context_selections: list[dict[str, Any]] | None = Field(
        None,
        alias='contextSelections',
        description='Updated context selections (sources / docs the skill may read).',
        examples=[[]],
    )
    interfaces: list[dict[str, Any]] | None = Field(
        None, description='Updated interface configuration.', examples=[[]]
    )
    evaluations: list[dict[str, Any]] | None = Field(
        None,
        description='Updated evaluation entries (task + expected-output pairs) saved for the draft variation. Replaces the prior list when present.',
        examples=[[]],
    )
    supervision_subordinate_descriptions: dict[str, str] | None = Field(
        None,
        alias='supervisionSubordinateDescriptions',
        description='Map of subordinate skill id (stringified) to the manager-provided description blurb. Replaces the prior map when present.',
        examples=[{'12': 'Reads warehouse facts', '17': 'Drafts the report'}],
    )
    access_config: AccessConfigDto | None = Field(
        None,
        alias='accessConfig',
        description='Updated access configuration. The service rejects changes that would lock the caller out of use + manage.',
    )
    manager_id: float | None = Field(
        None,
        alias='managerId',
        description='Re-parent the skill under a new manager (or remove its current manager when null). When this field is present, all other fields are ignored.',
        examples=[17],
    )


class TransferOwnershipDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    new_owner_user_id: str = Field(
        ...,
        alias='newOwnerUserId',
        description='Clerk user id of the org member who will become the new owner.',
        examples=['user_2abc123def456'],
    )


class DeploySkillDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_main_sha_override: (
        str | None
    ) = (
        Field(None, alias='expectedMainShaOverride', description='SHA the SPA last saw the remote file at; lets the user force-push past a previous drift by acknowledging the version they are overwriting. Empty string is treated as absent.', examples=['a1b2c3d4e5f607890123456789abcdef01234567'], max_length=200)
    )


class DeployResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    skill: SkillDto = Field(
        ...,
        description='The skill after the deploy. `hasUnpublishedChanges` is false and `activeVariationId` matches the newly-published variation.',
    )
    deployed_at: str = Field(
        ...,
        alias='deployedAt',
        description='Server-side timestamp at which the deploy completed.',
        examples=['2026-05-11T10:00:00.000Z'],
    )


class ConversationListItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    thread_id: str = Field(
        ..., alias='threadId', description='Opaque thread id.', examples=['agent_42_abc-xyz']
    )
    skill_id: float = Field(
        ...,
        alias='skillId',
        description='Numeric skill scope returned by the list adapter. This is not conversation ownership.',
        examples=[42],
    )
    first_message: str = Field(
        ...,
        alias='firstMessage',
        description='Preview of the first user turn, used as a list-row caption. Falls back to a stable placeholder when the thread has no human turn yet.',
        examples=['Run the churn analysis for last 30 days.'],
    )
    title: str | None = Field(
        ...,
        description='User-managed display title. Null until the user renames the conversation.',
        examples=['Q3 Revenue Analysis'],
    )
    message_count: float = Field(
        ...,
        alias='messageCount',
        description='Total number of message turns in the (post-collapse) conversation.',
        examples=[12],
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='ISO-8601 timestamp of the first checkpoint.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='ISO-8601 timestamp of the latest checkpoint.',
        examples=['2026-05-01T11:00:00.000Z'],
    )
    tools_used: list[str] | None = Field(
        None,
        alias='toolsUsed',
        description='Distinct tool names invoked across this conversation. Present only when `includeTools=true` is requested.',
        examples=[['sql_runner']],
    )
    user_ids: list[str] = Field(
        ...,
        alias='userIds',
        description='Distinct user ids that participated in this thread.',
        examples=[['user_abc']],
    )


class ListConversationsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    conversations: list[ConversationListItemDto] = Field(
        ..., description='Page of conversation summaries, newest-updated first.'
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page. `null` when there are no further pages.',
        examples=['eyJwYWdlIjoxLCJwYWdlU2l6ZSI6MTB9'],
    )
    total_count: float | None = Field(
        ...,
        alias='totalCount',
        description='Total threads visible in the scanned window after filters. Not a global count.',
        examples=[47],
    )
    page: float | None = Field(
        None,
        description='Legacy echo of the requested 0-indexed page. Retained for SPA backwards-compatibility; new callers should rely on `pageToken` / `nextPageToken`.',
        examples=[0],
    )
    page_size: float | None = Field(
        None,
        alias='pageSize',
        description='Legacy echo of the requested `pageSize`. Retained for SPA backwards-compatibility.',
        examples=[10],
    )


class MatchType(str, Enum):
    title_ = 'title'
    content = 'content'


class ConversationSearchMatchDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    match_type: MatchType = Field(
        ...,
        alias='matchType',
        description='Whether the row matched a user-managed title or deeper message content.',
    )
    item: ConversationListItemDto
    snippet: str | None = Field(
        None,
        description='Short excerpt around the content match. Omitted for title matches.',
        examples=['…LookML syntax for LOD expressions…'],
    )


class Type(str, Enum):
    human = 'human'
    ai = 'ai'
    system = 'system'
    tool = 'tool'
    unknown = 'unknown'


class ConversationMessageDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    type: Type | None = Field(
        ...,
        description='Message role. `human` and `ai` cover the user-visible turns; `system`, `tool`, and `unknown` are surfaced for completeness.',
        examples=['human'],
    )
    content: str = Field(
        ...,
        description='Message content. Usually a string for human turns; AI turns from newer LangChain versions may carry an array of content blocks (e.g. `[{type:"text",text:"…"}]`) instead. Consumers should handle both shapes.',
        examples=['Run the churn analysis for last 30 days.'],
    )
    id: str | None = Field(
        None,
        description='Stable identifier for this message turn, when available.',
        examples=['msg_01HF8X3Z2K8E0'],
    )
    tool_calls: list[Any] | None = Field(
        None,
        alias='toolCalls',
        description='Tool invocations emitted by this message (AI turns). Shape mirrors the LangChain tool-call envelope.',
    )
    tool_call_id: str | None = Field(
        None,
        alias='toolCallId',
        description='Tool call id this message responds to (for `tool` turns).',
    )


class ConversationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    thread_id: str = Field(
        ...,
        alias='threadId',
        description='Opaque thread/checkpoint id. It is not owned by a single skill; a conversation can span multiple agents.',
        examples=['agent_42_abc-xyz'],
    )
    skill_id: float = Field(
        ...,
        alias='skillId',
        description='Numeric skill scope returned by the list/detail adapter. This is not conversation ownership.',
        examples=[42],
    )
    messages: list[ConversationMessageDto] = Field(
        ..., description='Conversation turns, in chronological order.'
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='ISO-8601 timestamp of the first checkpoint for this thread.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='ISO-8601 timestamp of the latest checkpoint for this thread.',
        examples=['2026-05-01T11:00:00.000Z'],
    )


class ConversationFileDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        ..., description='File basename (e.g. `report.csv`).', examples=['report.csv']
    )
    path: str = Field(
        ...,
        description="Full path inside the thread's virtual filesystem.",
        examples=['/output/report.csv'],
    )
    size_bytes: float = Field(
        ..., alias='sizeBytes', description='File size in bytes.', examples=[4096]
    )
    mime_type: str = Field(
        ...,
        alias='mimeType',
        description='Best-guess MIME type based on the file extension.',
        examples=['text/csv'],
    )
    signed_url: str | None = Field(
        None,
        alias='signedUrl',
        description='Short-lived pre-signed download URL for the file bytes. Omitted when conversationFilesBucket is not configured or bytes are fetched via GET .../files/:filePath.',
        examples=['https://modus-files.s3.amazonaws.com/.../report.csv?X-Amz-Signature=...'],
    )
    expires_at: str | None = Field(
        None,
        alias='expiresAt',
        description='ISO-8601 timestamp at which `signedUrl` expires.',
        examples=['2026-05-01T11:00:00.000Z'],
    )
    created_at: str | None = Field(
        None,
        alias='createdAt',
        description='ISO-8601 file creation timestamp, when known.',
        examples=['2026-05-01T10:30:00.000Z'],
    )
    modified_at: str | None = Field(
        None,
        alias='modifiedAt',
        description='ISO-8601 last-modified timestamp, when known.',
        examples=['2026-05-01T10:45:00.000Z'],
    )


class Type1(str, Enum):
    none = 'none'
    bearer = 'bearer'
    headers = 'headers'


class McpAuthConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    type: Type1 | None = Field(
        ..., description='Auth scheme used when connecting to the MCP server.', examples=['bearer']
    )
    bearer_token: str | None = Field(
        None,
        alias='bearerToken',
        description='Bearer token (required when `type=bearer`).',
        examples=['sk_test_abc123'],
    )
    headers: dict[str, Any] | None = Field(
        None,
        description='Header name → value map (required when `type=headers`).',
        examples=[{'X-Api-Key': 'sk_test_abc123'}],
    )


class McpToolDefinitionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        ..., description='Tool name as advertised by the MCP server.', examples=['sql_runner']
    )
    description: str | None = Field(
        None,
        description='Short human-friendly description of the tool.',
        examples=['Run a read-only SQL query against the dataset.'],
    )
    input_schema: dict[str, Any] | None = Field(
        None,
        alias='inputSchema',
        description='JSON Schema descriptor for the tool input arguments, when the MCP server advertises one.',
    )


class McpToolInfoDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        ..., description='Tool name as advertised by the MCP server.', examples=['sql_runner']
    )
    description: str | None = Field(
        None,
        description='Short human-friendly description of the tool.',
        examples=['Run a read-only SQL query against the dataset.'],
    )


class AuthType(str, Enum):
    none = 'none'
    bearer = 'bearer'
    headers = 'headers'


class McpConnectionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Opaque MCP connection id (UUID).',
        examples=['00000000-0000-4000-a000-000000000001'],
    )
    skill_id: float = Field(
        ...,
        alias='skillId',
        description='Numeric skill id this connection is attached to.',
        examples=[42],
    )
    name: str | None = Field(..., description='Human-friendly connection name.', examples=['GitHub MCP'])
    url: str = Field(..., description='MCP server URL.', examples=['https://api.example.com/mcp'])
    auth_type: AuthType = Field(
        ...,
        alias='authType',
        description='Auth scheme used when connecting to the MCP server.',
        examples=['bearer'],
    )
    tool_count: float = Field(
        ...,
        alias='toolCount',
        description='Number of tools discovered during the last discovery run.',
        examples=[7],
    )
    discovered_tools: list[McpToolInfoDto] = Field(
        ...,
        alias='discoveredTools',
        description='Tool summaries discovered during the last discovery run. The full input schemas are surfaced by the get-connection-detail endpoint.',
    )
    discovery_completed_at: str = Field(
        ...,
        alias='discoveryCompletedAt',
        description='ISO-8601 timestamp when discovery last succeeded.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='ISO-8601 creation timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='ISO-8601 last-update timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )


class MemoryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ..., description='Opaque memory id (mem0 surrogate key).', examples=['mem_01HRQX...ABC']
    )
    memory: str = Field(
        ...,
        description='The memory text as stored in mem0.',
        examples=['User prefers concise summaries with bullet points.'],
    )
    hash: str | None = Field(
        None, description='Content hash (mem0-supplied) — useful for de-duplication.'
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description='Opaque metadata bag — caller-supplied tags forwarded verbatim to mem0.',
        examples=[{'source': 'agent_run_42', 'topic': 'preferences'}],
    )
    created_at: str | None = Field(
        None,
        alias='createdAt',
        description='ISO-8601 creation timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str | None = Field(
        None,
        alias='updatedAt',
        description='ISO-8601 last-update timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )


class ListMemoriesResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    memories: list[MemoryDto] = Field(..., description='Memories belonging to the skill.')
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
        examples=['eyJvZmZzZXQiOjI1LCJwYWdlU2l6ZSI6MjV9'],
    )


class UpdateMemoryRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    memory: str | None = Field(
        None,
        description='Replacement memory text. Optional — supply when revising the text.',
        examples=['User prefers concise bullet-point summaries.'],
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description='Replacement metadata bag — forwarded verbatim to mem0. Optional.',
        examples=[{'topic': 'preferences', 'confidence': 'high'}],
    )


class SearchMemoriesRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    query: str = Field(
        ...,
        description="Search query string (semantic search over the skill's memories).",
        examples=['user preferences for response style'],
    )
    user_id: str | None = Field(
        None,
        alias='userId',
        description='Narrow results to memories tagged with this end-user id (mem0 per-user scope).',
        examples=['user_clerk_X'],
    )
    limit: float | None = Field(
        None,
        description='Override the default page size for search results (legacy default is 10).',
        examples=[10],
        ge=1.0,
        le=1000.0,
    )


class ComposeSkillContextRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(
        ...,
        description='User message or intent used to compose relevant context (RAG query).',
        examples=['What tables describe customer churn?'],
        min_length=1,
    )
    limit: float | None = Field(
        None,
        description='Optional cap on context items when the API falls back to structured JSON (no fragment markdown). Ignored when composed markdown is returned.',
        examples=[25],
        ge=1.0,
        le=200.0,
    )


class ComposeSkillContextResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context: str = Field(..., description='Composed context for the skill and intent (markdown from the context composer, or structured JSON fallback).', examples=['## Retrieved Context\n\n### customers\n\n...'])
    context_items: list[dict[str, Any]] = Field(
        ...,
        alias='contextItems',
        deprecated=True,
        description='Deprecated. Always an empty array. Use `context` for composed text (markdown or JSON fallback).',
        examples=[[]],
    )
    original_count: float = Field(
        ...,
        alias='originalCount',
        description='Total context items considered before filtering.',
        examples=[42],
    )
    session_id: str = Field(
        ...,
        alias='sessionId',
        description='Session id used for this composition (for correlation).',
        examples=['api-skill-42-550e8400-e29b-41d4-a716-446655440000'],
    )


class Model(str, Enum):
    claude_sonnet_4_6 = 'claude-sonnet-4.6'
    claude_opus_4_8 = 'claude-opus-4.8'
    gpt_5_2 = 'gpt-5.2'
    gpt_5_5 = 'gpt-5.5'
    gpt_5_mini = 'gpt-5-mini'
    gpt_oss_120b = 'gpt-oss-120b'
    gpt_oss_20b = 'gpt-oss-20b'
    qwen3_235b_a22b_2507 = 'qwen3-235b-a22b-2507'
    qwen3_coder = 'qwen3-coder'
    qwen3_32b = 'qwen3-32b'
    deepseek_chat_v3_1 = 'deepseek-chat-v3.1'
    minimax_m2_7 = 'minimax-m2.7'
    llama_4_maverick = 'llama-4-maverick'
    llama_4_scout = 'llama-4-scout'
    llama_3_3_70b_instruct = 'llama-3.3-70b-instruct'
    gemini_3_1_pro_preview = 'gemini-3.1-pro-preview'
    gemini_3_flash_preview = 'gemini-3-flash-preview'
    grok_4_3_fast = 'grok-4.3-fast'
    grok_4_3 = 'grok-4.3'


class SkillChatRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(
        ...,
        description='User message sent to the published skill supervisor.',
        examples=['Summarize open support tickets from last week.'],
        min_length=1,
    )
    model: Model | None = Field(
        ...,
        description='Canonical model id for this run (required). Allowed values: claude-sonnet-4.6, claude-opus-4.8, gpt-5.2, gpt-5.5, gpt-5-mini, gpt-oss-120b, gpt-oss-20b, qwen3-235b-a22b-2507, qwen3-coder, qwen3-32b, deepseek-chat-v3.1, minimax-m2.7, llama-4-maverick, llama-4-scout, llama-3.3-70b-instruct, gemini-3.1-pro-preview, gemini-3-flash-preview, grok-4.3-fast, grok-4.3.',
        examples=['claude-sonnet-4.6'],
    )


class SkillChatResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    content: str = Field(
        ...,
        description='Final assistant text for the run.',
        examples=['There were 12 open tickets last week…'],
    )
    thread_id: str = Field(
        ...,
        alias='threadId',
        description='Conversation thread id. For follow-up messages use POST …/conversations/{threadId}/chat (same id as GET …/conversations/{threadId}).',
        examples=['api-skill-42-550e8400-e29b-41d4-a716-446655440000'],
    )
    run_id: str = Field(
        ...,
        alias='runId',
        description='Opaque run id for this chat invocation (for logging and correlation).',
        examples=['550e8400-e29b-41d4-a716-446655440001'],
    )


class AgentGroupPermissionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    use: bool = Field(
        ...,
        description='Whether members of this group may use (run / invoke) the agent.',
        examples=[True],
    )
    manage: bool = Field(
        ...,
        description='Whether members of this group may manage (edit / deploy / delete) the agent.',
        examples=[False],
    )


class AgentSharedUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str = Field(
        ...,
        description='Lowercased email of a user explicitly granted access to a private agent.',
        examples=['alice@example.com'],
    )
    added_at: str | None = Field(
        None,
        alias='addedAt',
        description='ISO-8601 timestamp at which this user was added to the share list.',
        examples=['2026-05-01T10:00:00Z'],
    )
    added_by: str | None = Field(
        None,
        alias='addedBy',
        description='Clerk user id of the principal that added this share entry.',
        examples=['user_2abc'],
    )
    user_id: str | None = Field(
        None,
        alias='userId',
        description='Clerk user id of the invited principal (optional — email is the primary key).',
        examples=['user_2xyz'],
    )


class AgentAccessConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    visibility: Visibility = Field(
        ...,
        description='Visibility tier. `shared` applies the group-permission map; `private` ignores groups and uses owner + sharedWith for access.',
        examples=['shared'],
    )
    group_permissions: dict[str, AgentGroupPermissionDto] = Field(
        ...,
        alias='groupPermissions',
        description='Map of group UUID -> { use, manage } booleans. Empty object when visibility is `private`.',
        examples=[{'group_eng_uuid': {'use': True, 'manage': False}}],
    )
    shared_with: list[AgentSharedUserDto] = Field(
        ...,
        alias='sharedWith',
        description='Per-user share entries used for private-visibility agents.',
        examples=[[]],
    )
    owner_user_id: str | None = Field(
        None,
        alias='ownerUserId',
        description='Clerk user id of the agent owner. Set on first write for private agents.',
        examples=['user_2abc'],
    )
    owner_email: str | None = Field(
        None,
        alias='ownerEmail',
        description='Lowercased email of the agent owner. Used by private-agent ACL when owner email matches.',
        examples=['alice@example.com'],
    )


class AgentVariationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    trigger: dict[str, Any] | None = Field(
        None,
        description='`{trigger_type, schedule?}` blob. `trigger_type` is one of `schedule | webhook | api | slack | manual`.',
    )
    workflow_structure: dict[str, Any] | None = Field(
        None,
        alias='workflowStructure',
        description='Workflow graph (`{nodes, edges}`) for type=workflow agents. Null for type=task.',
    )
    agent_selection: dict[str, Any] | None = Field(
        None,
        alias='agentSelection',
        description='Selected skills + per-step config (`{agents, model?}`) for type=task agents. Null for type=workflow.',
    )


class Type2(str, Enum):
    task = 'task'
    workflow = 'workflow'


class AgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: float = Field(
        ...,
        description='Numeric agent id (stable per-org; not reused after delete).',
        examples=[42],
    )
    slug: str | None = Field(
        ...,
        description='URL-safe slug used in human-readable links. Unique per org.',
        examples=['customer-churn-agent-a3f'],
    )
    name: str | None = Field(
        ...,
        description='Display name of the agent. Shown in the builder and in run logs.',
        examples=['Customer Churn Analyzer'],
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description of what this agent does.',
        examples=['Predicts churn risk for a customer given a 90-day usage window.'],
    )
    status: Status1 = Field(
        ...,
        description='Lifecycle status. `draft` = never deployed. `active` = deployed. `deleted` = soft-deleted.',
        examples=['active'],
    )
    type: Type2 | None = Field(
        ...,
        description='Type of automation. `task` = single-step skill orchestration; `workflow` = multi-step graph.',
        examples=['task'],
    )
    org_uuid: str = Field(
        ...,
        alias='orgUuid',
        description='Org UUID this agent belongs to. Matches the caller’s principal.',
        examples=['00000000-0000-0000-0000-000000000001'],
    )
    active_variation_id: str | None = Field(
        None,
        alias='activeVariationId',
        description='Active (deployed) variation id. Null until the agent is first deployed.',
        examples=['00000000-0000-4000-a000-000000000100'],
    )
    draft_variation_id: str | None = Field(
        None,
        alias='draftVariationId',
        description='Most recent draft variation id. Null when there is no draft pending.',
        examples=['00000000-0000-4000-a000-000000000101'],
    )
    has_unpublished_changes: bool = Field(
        ...,
        alias='hasUnpublishedChanges',
        description='True when the draft variation differs from the active variation (deploy would publish changes).',
        examples=[False],
    )
    is_enabled: bool = Field(
        ...,
        alias='isEnabled',
        description='Whether the agent’s schedule is currently active. Toggle via the agent schedule API.',
        examples=[True],
    )
    access_config: AgentAccessConfigDto = Field(
        ...,
        alias='accessConfig',
        description='Access configuration — who in the org can use / manage this agent.',
    )
    pending_ownership_transfer: (
        PendingOwnershipTransferDto | None
    ) = (
        Field(None, alias='pendingOwnershipTransfer', description='Pending ownership transfer awaiting recipient acceptance. Absent when no request is in flight.')
    )
    variation: AgentVariationDto | None = Field(
        None,
        description='Variation-detail payload (`trigger`, `workflowStructure`, `agentSelection`) for the requested view. Present on detail responses; absent on list rows.',
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='Creation timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='Most recent update timestamp.',
        examples=['2026-05-11T10:00:00.000Z'],
    )
    deleted_at: str | None = Field(
        None,
        alias='deletedAt',
        description='Soft-delete timestamp. Null for active agents.',
        examples=[None],
    )
    can_manage: bool = Field(
        ...,
        alias='canManage',
        description='Whether the requesting principal can manage (edit/delete/deploy/toggle) this agent. Derived server-side from the principal + accessConfig. Always present on every Agent response.',
        examples=[True],
    )
    can_use: bool = Field(
        ...,
        alias='canUse',
        description='Whether the requesting principal can use (run, view history of) this agent. Derived server-side from the principal + accessConfig. Always present on every Agent response.',
        examples=[True],
    )
    manage_denial: ManageDenial | None = Field(
        ...,
        alias='manageDenial',
        description='Why `canManage` is false, for client-facing guidance: `needs_group_manage` (shared, but no group you belong to grants Manage) or `not_owner` (private, and you are not the owner). `null` when `canManage` is true. Derived server-side from the principal + accessConfig.',
        examples=['needs_group_manage'],
    )


class ListAgentsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    agents: list[AgentDto] = Field(
        ...,
        description='Page of agents the caller can at least `use`. Agents the caller cannot see are filtered out (not enumerated).',
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
        examples=['eyJsYXN0SWQiOjQyfQ'],
    )


class Frequency(str, Enum):
    hourly = 'hourly'
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    custom = 'custom'


class Weekday(str, Enum):
    monday = 'monday'
    tuesday = 'tuesday'
    wednesday = 'wednesday'
    thursday = 'thursday'
    friday = 'friday'
    saturday = 'saturday'
    sunday = 'sunday'


class TriggerScheduleDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    frequency: Frequency = Field(..., description='Cadence of the schedule.', examples=['daily'])
    time_of_day: str | None = Field(
        None,
        description='Time of day in 24-hour HH:MM format. Required for hourly/daily/weekly/monthly; ignored for custom.',
        examples=['09:00'],
        pattern='^([01]\\d|2[0-3]):[0-5]\\d$',
    )
    timezone: str = Field(..., description='IANA timezone identifier.', examples=['UTC'])
    weekdays: list[Weekday] | None = Field(
        None,
        description='Required for weekly schedules. Lowercase day names.',
        examples=[['monday', 'wednesday', 'friday']],
    )
    day_of_month: float | None = Field(
        None,
        description='Required for monthly schedules. Calendar day 1-31.',
        examples=[15],
        ge=1.0,
        le=31.0,
    )
    cron_expressions: list[str] | None = Field(
        None,
        description='Required for custom schedules. Each entry is a 5-field POSIX cron expression.',
        examples=[['0 9 * * 1-5']],
    )
    cron_description: str | None = Field(
        None,
        description='Human-readable description of the custom schedule. Required when frequency=custom.',
        examples=['Weekdays at 9am'],
    )


class TriggerType(str, Enum):
    schedule = 'schedule'
    webhook = 'webhook'
    api = 'api'
    slack = 'slack'
    manual = 'manual'


class TriggerDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    trigger_type: TriggerType = Field(
        ...,
        description='Trigger kind. Only `schedule` validates its nested payload here; the rest are opaque.',
        examples=['schedule'],
    )
    schedule: TriggerScheduleDto | None = Field(
        None, description='Schedule details. Required when trigger_type=schedule.'
    )


class AgentSelectionEntryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    agent_id: float = Field(
        ..., description='Numeric skill (agent) id to invoke at this step.', examples=[17], ge=1.0
    )
    priority_order: float = Field(
        ..., description='Execution order (1-indexed).', examples=[1], ge=1.0
    )
    role: str | None = Field(None, description='Optional role label.', examples=['researcher'])
    instructions: str | None = Field(
        None,
        description='Per-step instructions added to the prompt.',
        examples=['Focus on the last 30 days of data'],
    )
    tool_restrictions: list[str] | None = Field(
        None, description='Optional allowlist of tools the step may call.'
    )


class AgentSelectionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    model: str | None = Field(None, description='Override model name for the orchestration step.')
    agents: list[AgentSelectionEntryDto] = Field(
        ..., description='Ordered list of skills to invoke. Must contain at least one entry.'
    )


class Type3(str, Enum):
    workflow = 'workflow'
    task = 'task'


class CreateAgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        ...,
        description='Display name for the agent. Will be slugified into a URL-safe path.',
        examples=['Daily Sales Report'],
        max_length=200,
        min_length=1,
    )
    type: Type3 | None = Field(
        ...,
        description='Agent type. Only `workflow` is supported; `task` is accepted as a deprecated alias and silently upgraded to `workflow`.',
        examples=['workflow'],
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description shown in the builder and agent catalog.',
        examples=['Generates a daily sales report from CRM data.'],
    )
    trigger: TriggerDto | None = Field(
        None,
        description='Trigger configuration (schedule / webhook / api / slack / manual). Schedule shape is fully validated; other trigger types are opaque.',
    )
    agent_selection: AgentSelectionDto | None = Field(
        None,
        alias='agentSelection',
        description='Agent selection (for task automations): ordered skills plus per-skill instructions.',
    )
    workflow_structure: dict[str, Any] | None = Field(
        None,
        alias='workflowStructure',
        description='Workflow graph (nodes + edges) for `type=workflow` agents. Free-form JSONB.',
        examples=[{'nodes': [], 'edges': []}],
    )
    access_config: AgentAccessConfigDto | None = Field(
        None,
        alias='accessConfig',
        description='Access configuration. Omit to use the default (full-org shared with use + manage).',
    )


class Type4(str, Enum):
    task = 'task'
    workflow = 'workflow'


class UpdateAgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        None,
        description='New display name for the agent.',
        examples=['Daily Sales Report v2'],
        max_length=200,
        min_length=1,
    )
    type: Type4 | None = Field(
        None, description='Updated agent type. Rarely changed after creation.', examples=['task']
    )
    description: str | None = Field(
        None,
        description='Updated description.',
        examples=['Generates a daily sales report broken down by region.'],
    )
    trigger: TriggerDto | None = Field(
        None,
        description='Updated trigger configuration. Schedule shape is fully validated; other trigger types are opaque.',
    )
    agent_selection: AgentSelectionDto | None = Field(
        None, alias='agentSelection', description='Updated agent selection.'
    )
    workflow_structure: dict[str, Any] | None = Field(
        None,
        alias='workflowStructure',
        description='Updated workflow graph (nodes + edges).',
        examples=[{'nodes': [], 'edges': []}],
    )
    access_config: AgentAccessConfigDto | None = Field(
        None,
        alias='accessConfig',
        description='Updated access configuration. The service rejects changes that would lock the caller out of use + manage.',
    )


class DeployAgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_main_sha_override: (
        str | None
    ) = (
        Field(None, alias='expectedMainShaOverride', description='SHA the SPA last saw the remote file at; lets the user force-push past a previous drift by acknowledging the version they are overwriting. Empty string is treated as absent.', examples=['a1b2c3d4e5f607890123456789abcdef01234567'], max_length=200)
    )


class AgentDeployResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    agent: AgentDto = Field(
        ...,
        description='The agent after the deploy. `hasUnpublishedChanges` is false and `activeVariationId` matches the newly-published variation.',
    )
    deployed_at: str = Field(
        ...,
        alias='deployedAt',
        description='Server-side timestamp at which the deploy completed.',
        examples=['2026-05-11T10:00:00.000Z'],
    )


class AgentType(str, Enum):
    task = 'task'
    workflow = 'workflow'


class AutomationRunListItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Composite run identifier (`workflowId:temporalRunId`).',
        examples=['wf_42_run_1:11111111-2222-3333-4444-555555555555'],
    )
    workflow_id: str = Field(
        ..., alias='workflowId', description='Temporal workflow id.', examples=['wf_42_run_1']
    )
    temporal_run_id: str | None = Field(
        None,
        alias='temporalRunId',
        description='Temporal run id (one workflow may have multiple runs after retry).',
    )
    agent_id: float = Field(..., alias='agentId', description='Parent agent id.', examples=[42])
    agent_name: str = Field(
        ...,
        alias='agentName',
        description='Snapshot of the agent name at the time the run was indexed.',
        examples=['Daily Sales Report'],
    )
    agent_type: AgentType = Field(
        ..., alias='agentType', description='Agent type.', examples=['task']
    )
    status: str = Field(
        ...,
        description='Run status (running / awaiting_human / completed / error / cancelled).',
        examples=['completed'],
    )
    trigger_type: str | None = Field(
        None,
        alias='triggerType',
        description='Trigger type for the run (schedule / webhook / api / slack / manual).',
    )
    started_at: str | None = Field(None, alias='startedAt', description='ISO-8601 start timestamp.')
    ended_at: str | None = Field(
        None, alias='endedAt', description='ISO-8601 end timestamp; absent for in-flight runs.'
    )
    duration_ms: float | None = Field(
        None,
        alias='durationMs',
        description='Duration in milliseconds (when end timestamp is known).',
    )
    summary: str | None = Field(
        None, description='Short human-readable summary of the run outcome.'
    )
    pending_approval: dict[str, Any] | None = Field(
        None,
        alias='pendingApproval',
        description='Pending approval payload (only present when status is awaiting_human).',
    )


class ListAutomationRunsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    runs: list[AutomationRunListItemDto] = Field(
        ..., description='Page of run summaries (Temporal-ordered, descending start time).'
    )
    next_page_token: str | None = Field(
        None,
        alias='nextPageToken',
        description='Opaque token for the next page; null when this was the last page. Pass as `pageToken` on the next request.',
    )
    counts: dict[str, float] = Field(
        ...,
        description='Per-status counts (all_executions / running / awaiting_human / error / completed).',
        examples=[{'all_executions': 100, 'running': 1, 'awaiting_human': 0, 'error': 2, 'completed': 97}],
    )


class StatusReason(str, Enum):
    approval_timeout = 'approval_timeout'


class Source(str, Enum):
    live_query = 'live-query'
    history = 'history'


class GetAutomationRunResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Composite run identifier (`workflowId:temporalRunId`).',
        examples=['wf_42_run_1:11111111-2222-3333-4444-555555555555'],
    )
    workflow_id: str = Field(
        ..., alias='workflowId', description='Temporal workflow id.', examples=['wf_42_run_1']
    )
    temporal_run_id: str | None = Field(
        None,
        alias='temporalRunId',
        description='Temporal run id (one workflow may have multiple runs after retry).',
    )
    agent_id: float = Field(..., alias='agentId', description='Parent agent id.', examples=[42])
    agent_name: str = Field(
        ...,
        alias='agentName',
        description='Snapshot of the agent name at the time the run was indexed.',
        examples=['Daily Sales Report'],
    )
    agent_type: AgentType = Field(
        ..., alias='agentType', description='Agent type.', examples=['task']
    )
    status: str = Field(
        ...,
        description='Run status (running / awaiting_human / completed / error / cancelled).',
        examples=['completed'],
    )
    trigger_type: str | None = Field(
        None,
        alias='triggerType',
        description='Trigger type for the run (schedule / webhook / api / slack / manual).',
    )
    started_at: str | None = Field(None, alias='startedAt', description='ISO-8601 start timestamp.')
    ended_at: str | None = Field(
        None, alias='endedAt', description='ISO-8601 end timestamp; absent for in-flight runs.'
    )
    duration_ms: float | None = Field(
        None,
        alias='durationMs',
        description='Duration in milliseconds (when end timestamp is known).',
    )
    summary: str | None = Field(
        None, description='Short human-readable summary of the run outcome.'
    )
    pending_approval: dict[str, Any] | None = Field(
        None,
        alias='pendingApproval',
        description='Pending approval payload (only present when status is awaiting_human).',
    )
    status_reason: StatusReason | None = Field(
        None,
        alias='statusReason',
        description='Display-only signal that the workflow closed for a non-success reason.',
    )
    source: Source = Field(
        ...,
        description='Where the payload was read from. `live-query` = Temporal workflow is still in progress; `history` = closed run reconstructed from event history.',
    )
    task_result: dict[str, Any] | None = Field(
        None,
        alias='taskResult',
        description='Final result of a `task`-typed agent run. Free-form (depends on the agent).',
    )
    task_error: str | None = Field(
        None, alias='taskError', description='Error message for a failed `task`-typed agent run.'
    )
    workflow_nodes: list[dict[str, Any]] | None = Field(
        None, alias='workflowNodes', description='Per-node state for a `workflow`-typed agent run.'
    )
    history_unavailable_reason: (
        str | None
    ) = (
        Field(None, alias='historyUnavailableReason', description='Set when history was unavailable; `source` will be `live-query` in that case.')
    )


class Type5(str, Enum):
    slack = 'slack'
    mcp = 'mcp'
    teams = 'teams'


class AgentInterfaceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Interface row id (UUID).',
        examples=['00000000-0000-4000-a000-000000000300'],
    )
    agent_id: float = Field(..., alias='agentId', description='Parent agent id.', examples=[42])
    type: Type5 | None = Field(
        ...,
        description='Interface type. `slack` and `teams` deliver chat triggers; `mcp` exposes the agent as an MCP server.',
        examples=['mcp'],
    )
    name: str | None = Field(
        ...,
        description='Display name for the interface (shown in the SPA).',
        examples=['Internal MCP'],
    )
    config: dict[str, Any] = Field(
        ...,
        description='Interface-type-specific configuration (e.g. webhook url, MCP token references). Free-form JSONB.',
        examples=[{}],
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='Creation timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='Most recent update timestamp.',
        examples=['2026-05-11T10:00:00.000Z'],
    )


class UserFeedback(str, Enum):
    negative = 'negative'
    neutral = 'neutral'
    positive = 'positive'


class ContextItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str = Field(
        ...,
        description='Stable UUID for the context item. Use this on PATCH / DELETE / values endpoints.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    org_id: str = Field(
        ...,
        alias='orgId',
        description='Org UUID this item belongs to. Matches the caller’s principal.',
        examples=['00000000-0000-0000-0000-000000000001'],
    )
    context_type: str = Field(
        ...,
        alias='contextType',
        description='Per-row context type identifier — one of `note`, `link`, `saved_query`, plus the dozens of integration-driven types (e.g. `looker_dashboard_metadata`, `salesforce_object_field`).',
        examples=['note'],
    )
    content: dict[str, Any] = Field(
        ...,
        description='Type-specific JSON content. Shape varies by `contextType`; treat as opaque unless you know the kind.',
    )
    description: str | None = Field(
        None,
        description='Human-readable description (separate from the type-specific `content` blob).',
        examples=['Q3 churn analysis notes'],
    )
    user_feedback: UserFeedback = Field(
        ...,
        alias='userFeedback',
        description='User-supplied verification verdict. `positive` ≈ approved/verified; `negative` ≈ rejected/dismissed; `neutral` is the default.',
        examples=['neutral'],
    )
    topics: list[str] = Field(
        ...,
        description='Free-form topic tags. Used for sidebar filtering on the SPA.',
        examples=[['analytics', 'q3']],
    )
    connection_id: str | None = Field(
        None,
        alias='connectionId',
        description='Originating integration connection id for integration-derived items. Null for user-created items.',
        examples=['00000000-0000-4000-a000-000000000111'],
    )
    selection_id: str | None = Field(
        None,
        alias='selectionId',
        description='Originating selection id (datamap-scoped) for integration-derived items.',
        examples=['00000000-0000-4000-a000-000000000222'],
    )
    data_path: list[str] = Field(
        ...,
        alias='dataPath',
        description='Hierarchical Postgres `text[]` path that places the item inside the datamap (used for filtering by data asset).',
        examples=[['salesforce', '00000000-0000-4000-a000-000000000111', 'Account', 'Name']],
    )
    created_at: str | None = Field(
        ...,
        alias='createdAt',
        description='Creation timestamp.',
        examples=['2026-05-01T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='Most recent update timestamp.',
        examples=['2026-05-11T10:00:00.000Z'],
    )
    last_update_metadata: dict[str, Any] | None = Field(
        None,
        alias='lastUpdateMetadata',
        description='Audit blob recording who/what last edited the item (`action`, `user_id`/`editedByName`/`editedByEmail`, `timestamp`). Used by the SPA to render the "Last Update" column.',
        examples=[{'action': 'auto_analysis', 'timestamp': '2026-05-11T10:00:00.000Z'}],
    )


class ListContextItemsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_items: list[ContextItemDto] = Field(
        ...,
        alias='contextItems',
        description='Page of context items. Empty when no items match the filter.',
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request. Required-but-nullable — the field is always present on every response.',
        examples=['eyJjcmVhdGVkQXQiOiIyMDI2LTA1LTAxIiwidWlkIjoiYWJjIn0'],
    )
    total_count: float | None = Field(
        None,
        alias='totalCount',
        description='Approximate total count of matching items (when known). Some filter combinations skip this for cost reasons.',
        examples=[142],
    )


class ListContextItemValuesResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    values: list[Any] = Field(
        ...,
        description='Page of values extracted from the context item at the supplied `contentKeyPath`. Each entry is opaque JSON whose shape depends on the source item.',
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page, or `null` if no more pages. Pass back as `pageToken`.',
    )


class UpdateContextItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_type: str | None = Field(
        None,
        alias='contextType',
        description='Required when `content` is supplied — selects which partition to update against. Free-form string (e.g. `note`, `saved_query`).',
        examples=['note'],
    )
    content: dict[str, Any] | None = Field(
        None, description='Replacement type-specific JSON content. Shape varies by `contextType`.'
    )
    description: str | None = Field(
        None,
        description='Replacement description text.',
        examples=['Updated description after review'],
    )
    user_feedback: UserFeedback | None = Field(
        None,
        alias='userFeedback',
        description='User-supplied verification verdict.',
        examples=['positive'],
    )
    topics: list[str] | None = Field(
        None,
        description='Replacement topic tags. Pass `[]` to clear all tags.',
        examples=[['analytics', 'verified']],
    )


class DeleteContextItemResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str = Field(
        ...,
        description='UUID of the deleted context item.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    context_type: str = Field(
        ...,
        alias='contextType',
        description='Resolved context type at delete time. Always one of `note`, `link`, `saved_query`, `golden_query`, `file_upload`.',
        examples=['note'],
    )


class ContentProjectionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    fields: list[str] | None = Field(
        None, description='Top-level scalar field names to project.', examples=[['isPartial']]
    )
    arrays: dict[str, list[str]] | None = Field(
        None,
        description='Per-array projection: object keys are array field names; the value lists the element fields to keep.',
        examples=[{'channels': ['channelId', 'channelName', 'isPrivate']}],
    )


class LookupContextItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_type: str = Field(
        ...,
        alias='contextType',
        description='Context type of the row to fetch (e.g. `slack_workspace_channel_list`).',
        examples=['slack_workspace_channel_list'],
    )
    data_path: list[str] = Field(
        ...,
        alias='dataPath',
        description="Hierarchical data path identifying the row. Full equality match against the row's `data_path` column.",
        examples=[['00000000-0000-4000-a000-000000000111', 'T0123456']],
    )
    content_projection: ContentProjectionDto | None = Field(
        None,
        alias='contentProjection',
        description='Optional JSONB projection applied at SQL time to shrink the payload. When omitted the full `content` column is returned.',
    )


class LookupContextItemRowDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str = Field(..., description='Stable UUID of the context item.')
    context_type: str = Field(
        ..., alias='contextType', description='Context type (same as the request).'
    )
    data_path: list[str] = Field(
        ...,
        alias='dataPath',
        description='Hierarchical data path of the row (same as the request).',
    )
    content: dict[str, Any] = Field(
        ...,
        description='Item content. When the request supplied a `contentProjection` the JSONB is shaped accordingly; otherwise the full content blob is returned.',
    )
    connection_id: str | None = Field(
        ...,
        alias='connectionId',
        description='Origin connection id if the row was emitted by an integration, otherwise null.',
    )
    selection_id: str | None = Field(
        ...,
        alias='selectionId',
        description='Selection (per-connection subset) id when the row scopes to a selection, otherwise null.',
    )


class LookupContextItemResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    item: LookupContextItemRowDto | None = Field(
        ...,
        description="The matched row, or null when no row in the caller's tenant matches the supplied `(contextType, dataPath)`.",
    )


class DataAssetFilterDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    pass


class TimeBucketDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    pass


class Scope(str, Enum):
    all = 'all'
    groups = 'groups'
    users = 'users'


class AccessPolicyDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    scope: Scope | None = Field(
        Scope.all, description='Visibility mode. Defaults to org-wide ("all") when omitted.'
    )
    group_ids: list[str] | None = Field(
        None,
        alias='groupIds',
        description='Member group uuids granted access. Required when scope is "groups".',
    )
    user_ids: list[str] | None = Field(
        None,
        alias='userIds',
        description='Clerk user ids granted access. Required when scope is "users".',
    )


class CreateNoteDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    title: str | None = Field(
        ...,
        description='Display title for the note. Used in the SPA list and as the s3 object filename.',
        examples=['Q3 churn analysis'],
    )
    content: str = Field(..., description='Note body — markdown text. Stored in tenant S3 + context_items.', examples=['## Findings\n\nChurn rate increased 2.3% MoM.'])
    access: AccessPolicyDto | None = None


class Kind(str, Enum):
    note = 'note'
    saved_query = 'saved_query'
    link = 'link'
    dimension = 'dimension'
    fact = 'fact'
    metric = 'metric'
    filter = 'filter'


class CreatedContextItemResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_item_id: str = Field(
        ...,
        alias='contextItemId',
        description='UUID of the newly-created context item. Use it on subsequent GET / PATCH / DELETE calls.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    kind: Kind = Field(..., description='Kind of context item created.', examples=['note'])
    s3_key: str | None = Field(
        None,
        alias='s3Key',
        description='Tenant S3 key for the raw content blob (notes, saved queries, links). Null for kinds without S3 backing.',
        examples=['context_notes/7a3f9d2c.../Q3_churn_analysis.md'],
    )
    title: str | None = Field(
        None,
        description='Resolved title for the created item. Null for kinds without a title field.',
        examples=['Q3 churn analysis'],
    )


class CreateSavedQueryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        ..., description='Display name for the saved query.', examples=['Top customers Q3']
    )
    query: str | None = Field(
        None,
        description='SQL text. Stored in tenant S3 + context_items. May be omitted or empty when creating a placeholder saved query.',
        examples=['SELECT customer_id, SUM(amount) FROM orders GROUP BY 1 ORDER BY 2 DESC LIMIT 10'],
    )
    connection_id: str | None = Field(
        ...,
        alias='connectionId',
        description='Data connection id this query targets. Must reference an existing integration connection in the org.',
        examples=['00000000-0000-4000-a000-000000000111'],
    )
    description: str | None = Field(
        None,
        description='Optional one-line description shown in the SPA list.',
        examples=['Quarterly cohort by amount.'],
    )
    path: list[str] | None = Field(
        None,
        description='Optional hierarchical path identifying the data scope (e.g. `["database", "schema"]` for Snowflake; `["dataset"]` for BigQuery).',
        examples=[['my_dataset']],
    )
    access: AccessPolicyDto | None = None


class CreateLinkDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    url: str = Field(
        ...,
        description='URL to extract content from. Invoked via Tavily.',
        examples=['https://example.com/blog/post'],
    )
    title: str | None = Field(
        None,
        description='Optional title override. When omitted, Tavily-derived metadata or the URL hostname is used.',
        examples=['Example blog post'],
    )
    is_crawl: bool | None = Field(
        False,
        alias='isCrawl',
        description='When true, crawls multiple pages starting from the supplied URL.',
        examples=[False],
    )
    page_limit: float | None = Field(
        None,
        alias='pageLimit',
        description='Maximum number of pages to crawl when `isCrawl` is true. Ignored otherwise.',
        examples=[10],
        ge=1.0,
        le=200.0,
    )
    access: AccessPolicyDto | None = None


class CreateDimensionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(..., description='Dimension name.', examples=['customer_country'])
    description: str | None = Field(
        ...,
        description='Human description.',
        examples=['ISO 3166 country code derived from billing address.'],
    )
    expr: str = Field(
        ...,
        description='Semantic-layer expression (varies by data warehouse).',
        examples=['${customers.billing_country}'],
    )
    data_type: str | None = Field(
        'TEXT',
        alias='dataType',
        description='Data type tag. Defaults to `TEXT`.',
        examples=['TEXT'],
    )
    synonyms: list[str] | None = Field(
        None,
        description='Optional synonyms used for fuzzy matching.',
        examples=[['country', 'nation']],
    )
    unique: bool | None = Field(
        None, description='True if values are unique per row.', examples=[False]
    )
    sample_values: str | None = Field(
        None,
        alias='sampleValues',
        description='Optional comma- or newline-separated sample values for documentation.',
        examples=['US, CA, GB, DE'],
    )


class CreateFactDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(..., description='Fact name.', examples=['order_amount_usd'])
    description: str | None = Field(
        ...,
        description='Human description.',
        examples=['Total order amount in USD after FX conversion.'],
    )
    expr: str = Field(
        ..., description='Semantic-layer expression.', examples=['${orders.amount_usd}']
    )
    aggregation: str | None = Field(
        'SUM', description='Aggregation strategy. Defaults to `SUM`.', examples=['SUM']
    )
    data_type: str | None = Field(
        'NUMBER',
        alias='dataType',
        description='Data type tag. Defaults to `NUMBER`.',
        examples=['NUMBER'],
    )
    synonyms: list[str] | None = Field(
        None, description='Optional synonyms used for fuzzy matching.'
    )
    access_modifier: str | None = Field(
        'public',
        alias='accessModifier',
        description='Access modifier (`public` / `private`). Defaults to `public`.',
        examples=['public'],
    )


class CreateMetricDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(..., description='Metric name.', examples=['gross_margin_pct'])
    description: str | None = Field(
        ..., description='Human description.', examples=['Gross margin as a percentage of revenue.']
    )
    expr: str = Field(
        ...,
        description='Metric expression in the semantic layer.',
        examples=['(${facts.revenue} - ${facts.cogs}) / ${facts.revenue}'],
    )
    access_modifier: str | None = Field(
        'public',
        alias='accessModifier',
        description='Access modifier (`public` / `private`). Defaults to `public`.',
        examples=['public'],
    )
    format: str | None = Field(
        None,
        description='Display format hint (`percent`, `currency`, `number`, …).',
        examples=['percent'],
    )


class CreateFilterDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(..., description='Filter name.', examples=['active_subscribers'])
    description: str | None = Field(
        ...,
        description='Human description.',
        examples=['Subscribers whose status is `active` and `last_seen_at` < 30d ago.'],
    )
    expr: str = Field(
        ...,
        description='Filter expression.',
        examples=["${subscribers.status} = 'active' AND ${subscribers.last_seen_at} > NOW() - INTERVAL '30 days'"],
    )
    synonyms: list[str] | None = Field(
        None, description='Optional synonyms used for fuzzy matching.'
    )


class ConnectionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Integration connection UUID.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    name: str | None = Field(
        ...,
        description='Human-readable connection name configured in the org.',
        examples=['Production Warehouse'],
    )
    type: str | None = Field(
        ...,
        description='Effective integration category for the connection (e.g. postgresql, bigquery).',
        examples=['postgresql'],
    )


class ListConnectionsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    connections: list[ConnectionDto] = Field(
        ...,
        description='Page of integration connections the caller can `use`. Connections the caller cannot access are filtered out (not enumerated).',
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
        examples=['eyJjcmVhdGVkQXQiOiIyMDI2'],
    )


class BootstrapUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str
    auth_method: str
    created_at: str | None = None
    last_login: str | None = None


class BootstrapOrganizationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    clerk_org_id: str
    name: str
    slug: str
    image_url: str


class OrgMemberDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    user_id: str
    first_name: str
    last_name: str
    email: str
    image_url: str
    role: str


class Status3(str, Enum):
    open = 'open'
    in_progress = 'in_progress'
    resolved = 'resolved'
    closed = 'closed'


class SupportTicketDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str
    title: str
    description: str
    status: Status3
    creator_user_id: str
    creator_email: str
    creator_name: str
    created_at: str
    updated_at: str


class MemberGroupDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str
    name: str
    description: str
    member_ids: list[str]
    created_at: str
    updated_at: str


class UsageBucketDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    bucket: str = Field(..., description='ISO8601 timestamp at the start of the bucket.')
    model: str | None = Field(..., description='LLM model name (canonicalised).')
    group_value: str = Field(
        ..., description='The grouped dimension value (skill/agent id, interface, or model).'
    )
    call_count: float = Field(
        ..., description='Number of LLM_CALL events in this bucket for this model.'
    )
    input_tokens: float = Field(..., description='Sum of input (prompt) tokens.')
    output_tokens: float = Field(..., description='Sum of output (response) tokens.')
    credits: float = Field(..., description='Credits consumed in this bucket.')


class UsageTotalsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    call_count: float
    input_tokens: float
    output_tokens: float
    credits: float = Field(
        ..., description='Total credits consumed across all buckets in the window.'
    )


class Rollup(str, Enum):
    hour = 'hour'
    day = 'day'


class GroupBy(str, Enum):
    all = 'all'
    skill = 'skill'
    agent = 'agent'
    interface = 'interface'
    model = 'model'


class ListUsageResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    org_id: str = Field(
        ...,
        description='Clerk org id (`org_xxx`) the result is scoped to. Matches `metering.usage_events.org_id`. NOT the Postgres tenant UUID.',
    )
    since: str
    until: str
    rollup: Rollup
    group_by: GroupBy = Field(..., description='Dimension that was grouped by in this response.')
    buckets: list[UsageBucketDto]
    totals: UsageTotalsDto


class LevelCountsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    sensitive: float
    flagged: float


class DefaultLevel(str, Enum):
    sensitive = 'sensitive'
    flagged = 'flagged'
    non_sensitive = 'non_sensitive'


class InfoTypeDetailDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    info_type: str
    count: float
    default_level: DefaultLevel = Field(..., alias='defaultLevel')


class Level(str, Enum):
    sensitive = 'sensitive'
    flagged = 'flagged'
    non_sensitive = 'non_sensitive'


class SensitivityOverrideDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    info_type: str
    level: Level
    updated_at: str


class GroupAccessEntryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    group_id: str
    level: Level
    updated_at: str
