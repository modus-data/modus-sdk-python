# Auto-generated from the Modus API schema. Do not edit by hand.
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel
from pydantic.alias_generators import to_camel


class Visibility(str, Enum):
    shared = 'shared'
    private = 'private'


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


class AgentDashboardAlertDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    dashboard_id: str = Field(
        ...,
        alias='dashboardId',
        description='Id of the dashboard whose KPI alert generated this workflow.',
        examples=['dash_01j9z3k2'],
    )
    tile_id: str = Field(
        ...,
        alias='tileId',
        description='Id of the dashboard tile the alert watches.',
        examples=['tile_revenue'],
    )


class AgentGroupPermissionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    use: bool = Field(
        ...,
        description='Whether members of this group may use (run / invoke) the workflow.',
        examples=[True],
    )
    manage: bool = Field(
        ...,
        description='Whether members of this group may manage (edit / deploy / delete) the workflow.',
        examples=[False],
    )


class AgentInterfaceType(str, Enum):
    slack = 'slack'
    mcp = 'mcp'
    teams = 'teams'


class AgentSelectionEntryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    agent_id: float = Field(
        ...,
        description='Numeric scope (workflow) id to invoke at this step.',
        examples=[17],
        ge=1.0,
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


class AgentSharedUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str = Field(
        ...,
        description='Lowercased email of a user explicitly granted access to a private workflow.',
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


class AgentType(str, Enum):
    task = 'task'
    workflow = 'workflow'


class AgentVariationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    trigger: dict[str, Any] | None = Field(
        None,
        description='`{trigger_type, schedule?}` blob. `trigger_type` is one of `schedule | webhook | api | slack | manual`.',
    )
    workflow_structure: dict[str, Any] | None = Field(
        None,
        alias='workflowStructure',
        description='Workflow graph (`{nodes, edges}`) when `type` is `workflow`. Null when `type` is `task`.',
    )
    agent_selection: dict[str, Any] | None = Field(
        None,
        alias='agentSelection',
        description='Selected scopes + per-step config (`{agents, model?}`) when `type` is `task`. Null when `type` is `workflow`.',
    )


class ApiErrorCode(str, Enum):
    validation = 'VALIDATION'
    bad_request = 'BAD_REQUEST'
    unauthorized = 'UNAUTHORIZED'
    forbidden = 'FORBIDDEN'
    not_found = 'NOT_FOUND'
    conflict = 'CONFLICT'
    rate_limited = 'RATE_LIMITED'
    internal_error = 'INTERNAL_ERROR'
    upstream_error = 'UPSTREAM_ERROR'


class ApiErrorStatus(str, Enum):
    invalid_argument = 'INVALID_ARGUMENT'
    unauthenticated = 'UNAUTHENTICATED'
    permission_denied = 'PERMISSION_DENIED'
    not_found = 'NOT_FOUND'
    already_exists = 'ALREADY_EXISTS'
    resource_exhausted = 'RESOURCE_EXHAUSTED'
    internal = 'INTERNAL'
    unavailable = 'UNAVAILABLE'


class AutomationRunListItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Composite run identifier (`workflowId:temporalRunId`).',
        examples=['wf_42_run_1:11111111-2222-3333-4444-555555555555'],
    )
    workflow_id: str = Field(
        ..., alias='workflowId', description='Workflow run identifier.', examples=['wf_42_run_1']
    )
    temporal_run_id: str | None = Field(
        None,
        alias='temporalRunId',
        description='Run identifier; a workflow may have multiple runs after a retry.',
    )
    agent_id: float = Field(..., alias='agentId', description='Parent workflow id.', examples=[42])
    agent_name: str = Field(
        ...,
        alias='agentName',
        description='Snapshot of the workflow name at the time the run was indexed.',
        examples=['Daily Sales Report'],
    )
    agent_type: AgentType = Field(
        ..., alias='agentType', description='Workflow type.', examples=['task']
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


class AutomationRunSource(str, Enum):
    live_query = 'live-query'
    history = 'history'


class BatchCreateCustomContextItemRelationsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    upserted_count: float = Field(
        ...,
        alias='upsertedCount',
        description='Number of relations created or updated by the batch.',
        examples=[12],
    )


class BulkFinalizeItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    upload_id: str = Field(
        ...,
        alias='uploadId',
        description='Upload id returned by `uploadUrl` / `uploadUrls`.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    file_name: str = Field(
        ...,
        alias='fileName',
        description='File name returned alongside the upload id.',
        examples=['Q3-churn-report.pdf'],
    )
    folder_path: str | None = Field(
        None,
        alias='folderPath',
        description='Root-relative folder path for this upload (for example `reports/2026`). Omit to store at the Files root. To reuse a folder created by an upload, pass its `folderPath`.',
        examples=['reports/2026/Q3'],
    )


class BulkUploadFromUrlItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    url: str | None = Field(
        None,
        description='Source URL to fetch.',
        examples=['https://example.com/reports/Q3-churn-report.pdf'],
    )
    file_name: str | None = Field(
        None,
        alias='fileName',
        description='Override file name. Inferred from the URL path when omitted.',
        examples=['Q3-churn-report.pdf'],
    )
    folder_path: str | None = Field(
        None,
        alias='folderPath',
        description='Root-relative folder path for this upload (for example `reports/2026`). Omit to store at the Files root. To reuse a folder created by an upload, pass its `folderPath`.',
        examples=['reports/2026/Q3'],
    )


class BulkUploadFromUrlsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    urls: list[BulkUploadFromUrlItemDto] = Field(
        ..., description='URLs to fetch and upload. Max 100 per request.'
    )


class BulkUploadUrlItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    file_name: str | None = Field(
        None,
        alias='fileName',
        description='Original file name, used to build the S3 object key.',
        examples=['Q3-churn-report.pdf'],
    )
    content_type: str | None = Field(
        None,
        alias='contentType',
        description='MIME type of the file. `application/octet-stream` falls back to an extension-based guess. Allowed categories: PDF, images, text, Office/OpenDocument documents, audio, and video.',
        examples=['application/pdf'],
    )
    file_size: float | None = Field(
        None,
        alias='fileSize',
        description='File size in bytes. Rejected above 50MB.',
        examples=[1048576],
    )


class BulkUploadUrlsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    files: list[BulkUploadUrlItemDto] = Field(
        ..., description='Files to create presigned upload URLs for. Max 100 per request.'
    )


class ChatInterfaceAccessMode(str, Enum):
    all = 'all'
    allow_list = 'allow-list'
    allow_org = 'allow-org'


class ChatInterfaceConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    access_mode: ChatInterfaceAccessMode | None = Field(
        None,
        alias='accessMode',
        description='Who may use the interface: `all` (anyone in the workspace), `allow-list` (only `allowedEmails`), `allow-org` (members of this organization).',
        examples=['allow-list'],
    )
    allowed_emails: list[str] | None = Field(
        None,
        alias='allowedEmails',
        description='Emails allowed to use the interface when `accessMode` is `allow-list`.',
        examples=[['ana@example.com']],
    )
    available_channel_ids: list[str] | None = Field(
        None,
        alias='availableChannelIds',
        description='Channels where the interface answers. Slack channel ids look like `C0ALH2JTRR9`. Empty or absent means every channel.',
        examples=[['C0ALH2JTRR9']],
    )


class ChatInterfaceType(str, Enum):
    slack = 'slack'
    teams = 'teams'


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
        description='Maximum context items to return. Omit to return all selected items.',
        examples=[25],
        ge=1.0,
        le=200.0,
    )


class ComposeSkillContextResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context: str = Field(
        ...,
        description='Composed context for the scope and intent (markdown from the context composer, or structured JSON fallback).',
        examples=['## Retrieved Context\n\n### customers\n\n...'],
    )
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
        description="Total context items in the scope's configured context selection (before composition strategies).",
        examples=[42],
    )
    selected_count: float = Field(
        ...,
        alias='selectedCount',
        description='Context items the composer kept for this intent.',
        examples=[12],
    )
    context_item_uids: list[str] = Field(
        ...,
        alias='contextItemUids',
        description='UIDs of the context items the composer kept, in selection order. Same length as `selectedCount`.',
        examples=[['ctx_01HZY4M8', 'ctx_01HZY4M9']],
    )
    session_id: str = Field(
        ...,
        alias='sessionId',
        description='Session id used for this composition (for correlation).',
        examples=['api-skill-42-550e8400-e29b-41d4-a716-446655440000'],
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


class ContextItemAncestorDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str = Field(
        ..., description='Stable identifier of the ancestor.', examples=['ancestor-123']
    )
    display_name: str | None = Field(
        ...,
        alias='display_name',
        description='Human-readable label. Generic path-token ancestry copies the same platform segment as uid. Null only when an explicit entry stored no name.',
        examples=['acme'],
    )
    type: str | None = Field(
        ...,
        description='Optional ancestor kind. Null when the source provides only platform path tokens.',
        examples=['container'],
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
        description='Originating integration connection id, or a virtual connection id such as `custom` or `files` for org-owned context.',
        examples=['00000000-0000-4000-a000-000000000111'],
    )
    selection_id: str | None = Field(
        None,
        alias='selectionId',
        description='Datamap selection id. For custom context, this is the customer-defined source id.',
        examples=['00000000-0000-4000-a000-000000000222'],
    )
    data_path: list[str] = Field(
        ...,
        alias='dataPath',
        description='Hierarchical path that places the item inside the data map (used for filtering by data asset).',
        examples=[['salesforce', '00000000-0000-4000-a000-000000000111', 'Account', 'Name']],
    )
    ancestry: list[ContextItemAncestorDto] | None = Field(
        None,
        description='Ordered ancestors. Omitted on older responses that do not yet include the field. Null means stored ancestry is unknown. An empty array means the item has no ancestors. Each entry uses `uid`, `display_name`, and `type`.',
    )
    created_at: str = Field(
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


class ContextItemKind(str, Enum):
    note = 'note'
    saved_query = 'saved_query'
    link = 'link'


class ConversationListItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    thread_id: str = Field(
        ..., alias='threadId', description='Opaque thread id.', examples=['agent_42_abc-xyz']
    )
    scope_id: float = Field(
        ...,
        alias='scopeId',
        description='Numeric scope id returned by the list adapter. This is not conversation ownership.',
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
    source: str | None = Field(
        None,
        description='UI surface the conversation was started from (e.g. `context_chat`, `home`). Not constrained to the `RunSource` enum: historical rows carry legacy values. Null when unknown, absent on responses that predate the field.',
        examples=['context_chat'],
    )
    message_count: float = Field(
        ...,
        alias='messageCount',
        description='Total number of message turns in the (post-collapse) conversation.',
        examples=[12],
    )
    created_at: str = Field(
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


class ConversationMessageType(str, Enum):
    human = 'human'
    ai = 'ai'
    system = 'system'
    tool = 'tool'
    unknown = 'unknown'


class ConversationMessageWindowDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    start_index: float = Field(
        ...,
        alias='startIndex',
        description='Zero-based source-message index of the first returned message. Source-message indexes include non-visible tool and system messages.',
        examples=[90],
    )
    end_index: float = Field(
        ...,
        alias='endIndex',
        description='Exclusive zero-based source-message index after the last returned message.',
        examples=[120],
    )
    total_messages: float = Field(
        ...,
        alias='totalMessages',
        description='Total source-message count used for paging. The returned visible message array can be shorter than endIndex - startIndex.',
        examples=[120],
    )
    has_more_before: bool = Field(
        ...,
        alias='hasMoreBefore',
        description='Whether an older message window exists before startIndex.',
        examples=[True],
    )
    has_more_after: bool = Field(
        ...,
        alias='hasMoreAfter',
        description='Whether a newer message window exists after endIndex.',
        examples=[False],
    )


class CreateCustomContextItemRelationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    from_uid: str = Field(
        ...,
        alias='fromUid',
        description='Uid of the source context item.',
        examples=['00000000-0000-4000-a000-000000000abc'],
    )
    to_uid: str = Field(
        ...,
        alias='toUid',
        description='Uid of the target context item.',
        examples=['00000000-0000-4000-a000-000000000def'],
    )
    relation_type: str = Field(
        ...,
        alias='relationType',
        description='Snake_case relation type describing how the source relates to the target.',
        examples=['depends_on'],
    )
    content: dict[str, Any] | None = Field(
        None, description='Optional structured payload stored on the relation edge.'
    )


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


class CreateNoteDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    title: str = Field(
        ...,
        description='Display title for the note. Used in the SPA list and as the s3 object filename.',
        examples=['Q3 churn analysis'],
    )
    content: str = Field(
        ...,
        description='Note body — markdown text. Stored in tenant S3 + context_items.',
        examples=['## Findings\n\nChurn rate increased 2.3% MoM.'],
    )
    access: AccessPolicyDto | None = None


class CreateSavedQueryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str = Field(
        ..., description='Display name for the saved query.', examples=['Top customers Q3']
    )
    query: str | None = Field(
        None,
        description='SQL text. Stored in tenant S3 + context_items. May be omitted or empty when creating a placeholder saved query.',
        examples=['SELECT customer_id, SUM(amount) FROM orders GROUP BY 1 ORDER BY 2 DESC LIMIT 10'],
    )
    connection_id: str = Field(
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


class CreatedContextItemResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_item_id: str = Field(
        ...,
        alias='contextItemId',
        description='UUID of the newly-created context item. Use it on subsequent GET / PATCH / DELETE calls.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    kind: ContextItemKind = Field(
        ..., description='Kind of context item created.', examples=['note']
    )
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


class CreatedCustomContextItemResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_item_id: str = Field(
        ...,
        alias='contextItemId',
        description='Stable uid of the created or updated custom context item.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    context_type: str = Field(
        ...,
        alias='contextType',
        description='Stored custom context type.',
        examples=['custom_entity_metadata'],
    )
    data_path: list[str] = Field(
        ...,
        alias='dataPath',
        description='Canonical hierarchy path rooted at the virtual `custom` connection and the customer-defined source.',
        examples=[['custom', 'billing-db', 'contracts', 'contract-123']],
    )
    title: str | None = Field(
        ..., description='Display title resolved for the item.', examples=['Acme renewal contract']
    )


class CreatedIngestedDataResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    checksum: str = Field(
        ...,
        description='Lowercase SHA-256 checksum of the canonical JSON envelope.',
        examples=['84f90e54a330d84e157af078f35409b093299941ffc623af900cd05bfc061b3d'],
    )


class CustomAttributeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str = Field(..., description='Attribute name.', examples=['status'])
    data_type: str | None = Field(
        None, alias='dataType', description='Customer-defined attribute type.', examples=['string']
    )
    value: dict[str, Any] | None = Field(
        None, description='Representative value for this attribute.'
    )


class CustomContextItemKind(str, Enum):
    source = 'source'
    collection = 'collection'
    entity = 'entity'
    field = 'field'
    entity_samples = 'entity_samples'


class DashboardChartDatasetDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="allow")
    label: str = Field(..., max_length=500, min_length=1)
    value_column: str = Field(..., alias='valueColumn', max_length=500, min_length=1)


class DashboardDraftSnapshotDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str
    created_by_user_id: str = Field(..., alias='createdByUserId')
    created_at: str = Field(..., alias='createdAt', examples=['2026-09-16T10:00:00.000Z'])


class DashboardElementKind(str, Enum):
    chart = 'chart'
    kpi = 'kpi'
    table = 'table'
    markdown = 'markdown'
    filter = 'filter'


class DashboardElementLayoutDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    x: int = Field(..., description='Left column, 0 through 11.', ge=0, le=11)
    y: int = Field(..., description='Top row, starting at 0.', ge=0)
    w: int = Field(..., description='Width in grid columns.', ge=1, le=12)
    h: int = Field(..., description='Height in grid rows.', ge=1)


class Option(RootModel[str]):
    root: str = Field(..., max_length=500)


class DefaultValue(RootModel[list[str]]):
    root: list[str] = Field(
        ...,
        description='Use { start, end } for date/datetime ranges; null clears the default. The value must match the filterType and allowMultiple setting.',
        max_length=1000,
        min_length=1,
    )


class DefaultValue1(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    start: str | None = None
    end: str | None = None


class DashboardElementSummaryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str
    kind: DashboardElementKind
    title: str
    layout: dict[str, Any] | None = Field(
        ..., description='Grid position (x, y, w, h), or null when the element has none.'
    )
    sql_references: list[str] | None = Field(
        None,
        alias='sqlReferences',
        description='Filters only: the exact {{ ... }} templates tile SQL uses to reference this filter; empty when it cannot be referenced.',
    )


class DashboardElementsListResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    dashboard_id: str = Field(..., alias='dashboardId')
    draft_revision: int = Field(
        ...,
        alias='draftRevision',
        description='Current draft revision; pass it as expectedRevision on the next write.',
    )
    elements: list[DashboardElementSummaryDto]


class DashboardFilterOptionsQueryPatchDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    connection_id: str | None = Field(
        None,
        alias='connectionId',
        description='Connection the options query runs on.',
        max_length=200,
    )
    sql: str | None = Field(
        None, description='SQL that returns the dropdown options.', max_length=100000
    )
    value_column: str | None = Field(
        None,
        alias='valueColumn',
        description='Result column holding each option value.',
        max_length=200,
    )
    label_column: str | None = Field(
        None,
        alias='labelColumn',
        description='Result column holding each option label.',
        max_length=200,
    )


class DashboardFilterType(str, Enum):
    text_pattern = 'text_pattern'
    dropdown = 'dropdown'
    query_dropdown = 'query_dropdown'
    date = 'date'
    datetime = 'datetime'
    datetime_sec = 'datetime_sec'
    date_range = 'date_range'
    datetime_range = 'datetime_range'
    datetime_sec_range = 'datetime_sec_range'
    text = 'text'
    number = 'number'
    boolean = 'boolean'


class DashboardFilterValueType(str, Enum):
    string = 'string'
    number = 'number'
    boolean = 'boolean'
    date = 'date'
    datetime = 'datetime'
    string_list = 'string_list'
    number_list = 'number_list'


class DashboardGroupPermissionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    use: bool = Field(..., description='Group members can view the dashboard.')
    manage: bool = Field(..., description='Group members can edit the dashboard.')


class DashboardLayoutElementDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    element_id: str = Field(
        ...,
        alias='elementId',
        description='Id of the dashboard element to place.',
        max_length=100,
        min_length=1,
    )
    layout: DashboardElementLayoutDto


class DashboardQuotationStyle(str, Enum):
    single = 'single'
    double = 'double'
    none = 'none'


class DashboardSharePermission(str, Enum):
    use = 'use'
    manage = 'manage'


class DashboardSharedUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str
    user_id: str | None = Field(None, alias='userId')
    permission: DashboardSharePermission | None = None


class DashboardTileKind(str, Enum):
    chart = 'chart'
    kpi = 'kpi'
    table = 'table'
    markdown = 'markdown'


class DashboardValueFormat(str, Enum):
    number = 'number'
    currency = 'currency'
    percent = 'percent'


class DashboardVersionKind(str, Enum):
    published = 'published'
    draft_snapshot = 'draft_snapshot'


class DashboardView(str, Enum):
    active = 'active'
    draft = 'draft'


class DashboardVisibility(str, Enum):
    shared = 'shared'
    private = 'private'


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


class DeployAgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_main_sha_override: (
        str | None
    ) = (
        Field(None, alias='expectedMainShaOverride', description='SHA the SPA last saw the remote file at; lets the user force-push past a previous drift by acknowledging the version they are overwriting. Empty string is treated as absent.', examples=['a1b2c3d4e5f607890123456789abcdef01234567'], max_length=200)
    )


class DeploySkillDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_main_sha_override: (
        str | None
    ) = (
        Field(None, alias='expectedMainShaOverride', description='SHA the SPA last saw the remote file at; lets the user force-push past a previous drift by acknowledging the version they are overwriting. Empty string is treated as absent.', examples=['a1b2c3d4e5f607890123456789abcdef01234567'], max_length=200)
    )


class ErrorEnvelopeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    code: ApiErrorCode = Field(..., description='Modus-specific machine code.')
    status: ApiErrorStatus = Field(..., description='Canonical status string for the error.')
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


class EvaluationCadenceFrequency(str, Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    custom = 'custom'


class EvaluationRecipientDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    clerk_user_id: str = Field(..., alias='clerkUserId', description='Clerk user ID')
    email: str = Field(..., description='Email address')
    name: dict[str, Any] | None = Field(None, description='Display name')


class EvaluationResultDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(..., description='Result ID')
    case_id: str = Field(..., alias='caseId', description='Evaluation case ID')
    task: str = Field(..., description='Task that was evaluated')
    expected_output: str = Field(..., alias='expectedOutput', description='Expected output')
    actual_output: dict[str, Any] | None = Field(
        None, alias='actualOutput', description='Actual output from the scope'
    )
    passed: dict[str, Any] | None = Field(None, description='Whether the case passed')
    score: dict[str, Any] | None = Field(None, description='Score (0-100)')
    reasoning: dict[str, Any] | None = Field(None, description='Judge reasoning')
    was_passing_before: dict[str, Any] | None = Field(
        None,
        alias='wasPassingBefore',
        description='Whether this case was passing in the previous run',
    )


class EvaluationRunStatus(str, Enum):
    running = 'running'
    completed = 'completed'
    completed_with_errors = 'completed_with_errors'
    failed = 'failed'


class EvaluationRunTrigger(str, Enum):
    scheduled = 'scheduled'
    manual = 'manual'


class EvaluationRunWithResultsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(..., description='Run ID')
    skill_id: float = Field(..., alias='skillId', description='Scope ID')
    trigger: EvaluationRunTrigger = Field(..., description='How the run was triggered')
    status: EvaluationRunStatus = Field(..., description='Run status')
    started_at: str = Field(..., alias='startedAt', description='When the run started')
    finished_at: dict[str, Any] | None = Field(
        None, alias='finishedAt', description='When the run finished'
    )
    total_cases: float = Field(
        ..., alias='totalCases', description='Total number of evaluation cases'
    )
    passed_cases: float = Field(..., alias='passedCases', description='Number of passed cases')
    failed_cases: float = Field(..., alias='failedCases', description='Number of failed cases')
    avg_score: dict[str, Any] | None = Field(
        None, alias='avgScore', description='Average score (0-100)'
    )
    is_regression: bool = Field(
        ..., alias='isRegression', description='Whether this run detected a regression'
    )
    judge_model: str | None = Field(None, alias='judgeModel', description='Judge model used')
    error_message: str | None = Field(
        None, alias='errorMessage', description='Error message if failed'
    )
    results: list[EvaluationResultDto] = Field(..., description='Per-case results')


class EvaluationSlackChannelDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    nango_connection_id: str = Field(
        ..., alias='nangoConnectionId', description='Nango connection ID for Slack'
    )
    slack_user_id_by_recipient: dict[str, Any] = Field(
        ..., alias='slackUserIdByRecipient', description='Mapping of Clerk user ID to Slack user ID'
    )


class FailedFinalizeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    index: float = Field(
        ..., description='Index of the failing entry in the request `uploads` array.', examples=[2]
    )
    upload_id: str = Field(
        ...,
        alias='uploadId',
        description='Upload id from the failing request entry.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    error: str = Field(
        ...,
        description='Reason this entry could not be finalized.',
        examples=['The upload has not been received.'],
    )


class FailedUploadFromUrlDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    index: float = Field(
        ..., description='Index of the failing entry in the request `urls` array.', examples=[1]
    )
    url: str = Field(
        ...,
        description='URL from the failing request entry.',
        examples=['https://internal.example.com/secret'],
    )
    error: str = Field(
        ...,
        description='Human-readable failure reason (blocked URL, fetch error, oversize, bad MIME, etc).',
        examples=['HTTP 404: Not Found'],
    )


class FailedUploadUrlDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    index: float = Field(
        ..., description='Index of the failing entry in the request `files` array.', examples=[2]
    )
    file_name: str = Field(
        ...,
        alias='fileName',
        description='File name from the failing request entry.',
        examples=['malware.exe'],
    )
    error: str = Field(
        ...,
        description='Human-readable validation failure reason.',
        examples=['File type "application/x-msdownload" is not allowed. Allowed types: PDF, images, text, and common document formats.'],
    )


class FileUploadResourceStatus(str, Enum):
    processing = 'processing'
    ready = 'ready'
    failed = 'failed'


class FinalizeUploadDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    file_name: str = Field(
        ...,
        alias='fileName',
        description='File name returned by `uploadUrl`, used to locate the uploaded object.',
        examples=['Q3-churn-report.pdf'],
    )
    folder_path: str | None = Field(
        None,
        alias='folderPath',
        description='Root-relative folder path for this upload (for example `reports/2026`). Omit to store at the Files root. To reuse a folder created by an upload, pass its `folderPath`.',
        examples=['reports/2026/Q3'],
    )


class StatusReason(str, Enum):
    approval_timeout = 'approval_timeout'


class GetAutomationRunResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Composite run identifier (`workflowId:temporalRunId`).',
        examples=['wf_42_run_1:11111111-2222-3333-4444-555555555555'],
    )
    workflow_id: str = Field(
        ..., alias='workflowId', description='Workflow run identifier.', examples=['wf_42_run_1']
    )
    temporal_run_id: str | None = Field(
        None,
        alias='temporalRunId',
        description='Run identifier; a workflow may have multiple runs after a retry.',
    )
    agent_id: float = Field(..., alias='agentId', description='Parent workflow id.', examples=[42])
    agent_name: str = Field(
        ...,
        alias='agentName',
        description='Snapshot of the workflow name at the time the run was indexed.',
        examples=['Daily Sales Report'],
    )
    agent_type: AgentType = Field(
        ..., alias='agentType', description='Workflow type.', examples=['task']
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
    source: AutomationRunSource = Field(
        ...,
        description='Where the payload was read from. `live-query` = the run is still in progress; `history` = a completed run.',
    )
    task_result: dict[str, Any] | None = Field(
        None,
        alias='taskResult',
        description='Final result of a `task`-typed workflow run. Free-form (depends on the workflow).',
    )
    task_error: str | None = Field(
        None, alias='taskError', description='Error message for a failed `task`-typed workflow run.'
    )
    workflow_nodes: list[dict[str, Any]] | None = Field(
        None,
        alias='workflowNodes',
        description='Per-node state for a `workflow`-typed workflow run.',
    )
    history_unavailable_reason: (
        str | None
    ) = (
        Field(None, alias='historyUnavailableReason', description='Set when history was unavailable; `source` will be `live-query` in that case.')
    )


class GroupPermissionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    use: bool = Field(
        ...,
        description='Whether members of this group may use (run / invoke) the scope.',
        examples=[True],
    )
    manage: bool = Field(
        ...,
        description='Whether members of this group may manage (edit / deploy / delete) the scope.',
        examples=[False],
    )


class HttpIngestedDataRequestType(str, Enum):
    http = 'http'


class IngestedDataResponseFormat(str, Enum):
    csv = 'csv'
    json = 'json'
    xml = 'xml'
    text = 'text'


class ListAutomationRunsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    runs: list[AutomationRunListItemDto] = Field(
        ..., description='Page of run summaries, most recent first.'
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
    total_count: float = Field(
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


class ListCustomContextItemsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_items: list[ContextItemDto] = Field(
        ..., alias='contextItems', description='Page of custom context items.'
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page.',
    )
    total_count: float | None = Field(
        ...,
        alias='totalCount',
        description='Approximate total count of matching custom context items, when known.',
    )


class ListDashboardDraftSnapshotsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    snapshots: list[DashboardDraftSnapshotDto] = Field(
        ..., description='Up to 100 most recent draft snapshots; editors only.'
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
    attribution = 'attribution'


class LookupContextItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_type: str = Field(
        ...,
        alias='contextType',
        description='Context type of the row to fetch (e.g. `slack_channel_metadata`).',
        examples=['slack_channel_metadata'],
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
    ancestry: list[ContextItemAncestorDto] | None = Field(
        None,
        description='Ordered ancestors. Omitted on older responses that do not yet include the field. Null means stored ancestry is unknown. An empty array is stored empty ancestry.',
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


class MemberGroupSource(str, Enum):
    native = 'native'
    directory = 'directory'


class MemoryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(..., description='Opaque memory id.', examples=['mem_01HRQX...ABC'])
    memory: str = Field(
        ...,
        description='The memory text.',
        examples=['User prefers concise summaries with bullet points.'],
    )
    hash: str | None = Field(None, description='Content hash, useful for de-duplication.')
    metadata: dict[str, Any] | None = Field(
        None,
        description='Opaque metadata bag — caller-supplied tags stored with the memory.',
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


class Model(str, Enum):
    claude_sonnet_5 = 'claude-sonnet-5'
    claude_sonnet_5_5 = 'claude-sonnet-5.5'
    claude_sonnet_4_6 = 'claude-sonnet-4.6'
    claude_opus_4_8 = 'claude-opus-4.8'
    claude_opus_5_5 = 'claude-opus-5.5'
    gpt_5_2 = 'gpt-5.2'
    gpt_5_5 = 'gpt-5.5'
    gpt_5_mini = 'gpt-5-mini'
    gpt_5_6_luna = 'gpt-5.6-luna'
    gpt_6_luna = 'gpt-6-luna'
    gpt_oss_120b = 'gpt-oss-120b'
    gpt_oss_20b = 'gpt-oss-20b'
    qwen3_235b_a22b_2507 = 'qwen3-235b-a22b-2507'
    qwen3_coder = 'qwen3-coder'
    qwen3_32b = 'qwen3-32b'
    deepseek_chat_v3_1 = 'deepseek-chat-v3.1'
    deepseek_v4_pro = 'deepseek-v4-pro'
    deepseek_v4_flash_latest = 'deepseek-v4-flash-latest'
    minimax_m2_7 = 'minimax-m2.7'
    llama_4_maverick = 'llama-4-maverick'
    llama_4_scout = 'llama-4-scout'
    llama_3_3_70b_instruct = 'llama-3.3-70b-instruct'
    gemini_3_1_pro_preview = 'gemini-3.1-pro-preview'
    gemini_3_flash_preview = 'gemini-3-flash-preview'
    grok_4_3_fast = 'grok-4.3-fast'
    grok_4_3 = 'grok-4.3'
    grok_4_7 = 'grok-4.7'
    kimi_k3 = 'kimi-k3'


class ApprovalDecision(str, Enum):
    approve = 'approve'
    deny = 'deny'


class ModusChatRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str | None = Field(
        None,
        description='User message sent to Modus. Omit when `approvalContinuation` is true.',
        examples=['What were our top revenue drivers last quarter?'],
        min_length=1,
    )
    model: Model = Field(
        ...,
        description='Canonical model id for this run (required). Allowed values: claude-sonnet-5, claude-sonnet-5.5, claude-sonnet-4.6, claude-opus-4.8, claude-opus-5.5, gpt-5.2, gpt-5.5, gpt-5-mini, gpt-5.6-luna, gpt-6-luna, gpt-oss-120b, gpt-oss-20b, qwen3-235b-a22b-2507, qwen3-coder, qwen3-32b, deepseek-chat-v3.1, deepseek-v4-pro, deepseek-v4-flash-latest, minimax-m2.7, llama-4-maverick, llama-4-scout, llama-3.3-70b-instruct, gemini-3.1-pro-preview, gemini-3-flash-preview, grok-4.3-fast, grok-4.3, grok-4.7, kimi-k3.',
        examples=['claude-sonnet-4.6'],
    )
    approval_continuation: bool | None = Field(
        None,
        alias='approvalContinuation',
        description='Continue a pending write-approval interrupt from a prior turn. When true, `message` is ignored.',
    )
    approval_decision: ApprovalDecision | None = Field(
        None, alias='approvalDecision', description='Required when `approvalContinuation` is true.'
    )


class ModusChatResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    content: str = Field(
        ...,
        description='Final assistant text for the run.',
        examples=['Revenue grew 12% quarter over quarter…'],
    )
    thread_id: str = Field(
        ...,
        alias='threadId',
        description='Conversation thread id. For follow-up use POST …/conversations/{threadId}/chat.',
        examples=['agent_0_550e8400-e29b-41d4-a716-446655440000'],
    )
    run_id: str = Field(
        ...,
        alias='runId',
        description='Opaque run id for this chat invocation.',
        examples=['550e8400-e29b-41d4-a716-446655440001'],
    )


class ModusContextRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(
        ...,
        description='User message or intent used to compose relevant context.',
        examples=['What tables describe customer churn?'],
        min_length=1,
    )
    limit: float | None = Field(
        None,
        description='Maximum context items to return. Omit to return all selected items.',
        examples=[25],
        ge=1.0,
        le=200.0,
    )


class ModusContextResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context: str = Field(
        ..., description='Composed context for the intent (markdown or JSON fallback).'
    )
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
        description='Total context items in the configured scope (before composition strategies).',
    )
    selected_count: float = Field(
        ..., alias='selectedCount', description='Context items the composer kept for this intent.'
    )
    context_item_uids: list[str] = Field(
        ...,
        alias='contextItemUids',
        description='UIDs of the context items the composer kept, in selection order. Same length as `selectedCount`.',
    )
    session_id: str = Field(
        ..., alias='sessionId', description='Session id used for this composition.'
    )


class MoveContextItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    destination_folder_uid: str | None = Field(
        ...,
        alias='destinationFolderUid',
        description='Stored context-item uid of an existing Files folder, or null to move to the Files root. The destination must already exist. Move does not rename or merge folders.',
        examples=[None],
    )


class MoveContextItemResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    moved_items: int = Field(
        ...,
        alias='movedItems',
        description='Number of context items whose parent changed. Zero is a successful same-parent no-op.',
        examples=[3],
        ge=0,
    )


class OrgMemberDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    user_id: str
    first_name: str
    last_name: str
    email: str
    image_url: str
    role: str


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


class PublishDashboardDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_revision: int = Field(
        ...,
        alias='expectedRevision',
        description='Draft revision to publish; a stale value is rejected with 409.',
        ge=1,
    )


class ReasoningEffort(str, Enum):
    none = 'none'
    minimal = 'minimal'
    low = 'low'
    medium = 'medium'
    high = 'high'
    xhigh = 'xhigh'
    max = 'max'


class ResourceLifecycleStatus(str, Enum):
    draft = 'draft'
    active = 'active'
    deleted = 'deleted'


class ManageDenial(str, Enum):
    not_owner = 'not_owner'
    needs_group_manage = 'needs_group_manage'


class ScopeInterfaceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ..., description='Interface id (UUID).', examples=['00000000-0000-4000-a000-000000000500']
    )
    scope_id: float = Field(..., alias='scopeId', description='Scope id.', examples=[42])
    type: ChatInterfaceType = Field(..., examples=['slack'])
    name: str = Field(..., description='Display name.', examples=['Slack'])
    config: ChatInterfaceConfigDto
    created_at: str = Field(
        ...,
        alias='createdAt',
        description='Creation timestamp.',
        examples=['2026-09-30T10:00:00.000Z'],
    )
    updated_at: str = Field(
        ...,
        alias='updatedAt',
        description='Most recent update timestamp.',
        examples=['2026-09-30T10:00:00.000Z'],
    )


class SearchMemoriesRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    query: str = Field(
        ...,
        description="Search query string (semantic search over the scope's memories).",
        examples=['user preferences for response style'],
    )
    user_id: str | None = Field(
        None,
        alias='userId',
        description='Narrow results to memories tagged with this end-user id.',
        examples=['user_clerk_X'],
    )
    limit: float | None = Field(
        None,
        description='Override the default page size for search results (legacy default is 10).',
        examples=[10],
        ge=1.0,
        le=1000.0,
    )


class SetSupervisionRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    subordinate_agent_ids: list[float] = Field(
        ...,
        alias='subordinateAgentIds',
        description='Replacement list of subordinate scope ids. The previous list is fully replaced; pass `[]` to clear.',
        examples=[[17, 23, 91]],
    )


class SharedUserPermission(str, Enum):
    use = 'use'
    manage = 'manage'


class SkillChatRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(
        ...,
        description='User message sent to the published scope supervisor.',
        examples=['Summarize open support tickets from last week.'],
        min_length=1,
    )
    model: Model = Field(
        ...,
        description='Canonical model id for this run (required). Allowed values: claude-sonnet-5, claude-sonnet-5.5, claude-sonnet-4.6, claude-opus-4.8, claude-opus-5.5, gpt-5.2, gpt-5.5, gpt-5-mini, gpt-5.6-luna, gpt-6-luna, gpt-oss-120b, gpt-oss-20b, qwen3-235b-a22b-2507, qwen3-coder, qwen3-32b, deepseek-chat-v3.1, deepseek-v4-pro, deepseek-v4-flash-latest, minimax-m2.7, llama-4-maverick, llama-4-scout, llama-3.3-70b-instruct, gemini-3.1-pro-preview, gemini-3-flash-preview, grok-4.3-fast, grok-4.3, grok-4.7, kimi-k3.',
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


class SkillMcpInterfaceConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    core_tools: dict[str, Any] | None = Field(
        None,
        alias='coreTools',
        description='Core MCP tools: chat (get_answer), getContext, teachModus. Omitted keys default to chat false, getContext true, teachModus false. chat cannot be true together with another tool.',
    )
    mcp_tool_exposure: dict[str, Any] | None = Field(
        None,
        alias='mcpToolExposure',
        description='Integration tools exposed to MCP clients: mode discovery (all) or subset with allowedIntegrationKeys. Must be an empty subset when chat is true.',
    )


class SqlIngestedDataRequestType(str, Enum):
    sql = 'sql'


class SuggestionEventSource(str, Enum):
    home = 'home'


class SuggestionEventType(str, Enum):
    shown = 'shown'
    clicked = 'clicked'
    dismissed = 'dismissed'
    submitted = 'submitted'


class SuggestionQuestionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(..., description='Stable suggestion id.')
    skill_id: float | None = Field(
        None, alias='skillId', description='Numeric scope id this suggestion is scoped to.'
    )
    label: str = Field(..., description='Short Home button label.')
    prompt: str = Field(..., description='Prompt sent when the suggestion is selected.')
    rationale: str | None = Field(None, description='Reason this suggestion was generated.')
    metadata: dict[str, Any] | None = Field(
        None, description='Suggestion metadata for diagnostics and ranking.'
    )


class SupervisionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    supervisor_agent_id: float = Field(
        ...,
        alias='supervisorAgentId',
        description='Numeric id of the scope that supervises the listed subordinates. Echoes the `:id` from the URL path.',
        examples=[42],
    )
    subordinate_agent_ids: list[float] = Field(
        ...,
        alias='subordinateAgentIds',
        description='Numeric ids of the scopes supervised by `supervisorAgentId`. The order is preserved across writes and reads.',
        examples=[[17, 23, 91]],
    )


class ToggleAgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    active: bool = Field(
        ...,
        description='Target enabled state. `true` enables the workflow schedule; `false` disables it.',
        examples=[True],
    )


class ToolCatalogActionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str = Field(
        ...,
        description='Stable action id: the exact string to list in `toolset.<id>.byConnection.<connectionId>.actions` (or `toolset.<id>.actions`, which binds to the newest workspace connection).',
        examples=['list_dags'],
    )
    display_name: str = Field(
        ...,
        alias='displayName',
        description='Human-readable label for display.',
        examples=['List DAGs'],
    )
    description: str = Field(
        ...,
        description='What this action does.',
        examples=['List the selected DAGs with their schedule, owners, tags, and paused state.'],
    )


class ToolCatalogEntryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Stable id — use as the key in a toolset object, e.g. `{ [id]: { enabled: true } }`.',
        examples=['sql_runner'],
    )
    display_name: str = Field(
        ...,
        alias='displayName',
        description='Human-readable name for display.',
        examples=['SQL Runner'],
    )
    category: str | None = Field(
        None,
        description='Grouping category, e.g. "data", "messaging", "general".',
        examples=['data'],
    )
    requires_connection: bool = Field(
        ...,
        alias='requiresConnection',
        description='True if this tool requires a connected integration/account before it can be used.',
        examples=[False],
    )
    actions: list[ToolCatalogActionDto] | None = Field(
        None,
        description='Fixed set of actions this tool exposes. Present only when the action list does not depend on a live connection (built-in tools). Connected integrations expose connection-specific actions not listed here.',
    )


class ToolsetToolDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Stable id of the tool (matches the registry key on the workflow runtime).',
        examples=['web_search'],
    )
    enabled: bool | None = Field(
        None,
        description='Whether this tool is enabled for the scope. Defaults to true when absent.',
        examples=[True],
    )
    config: dict[str, Any] | None = Field(
        None,
        description='Free-form tool-specific configuration (e.g. allowlists). Schema varies per tool.',
        examples=[{'max_results': 5}],
    )


class TransferDashboardOwnershipDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    new_owner_user_id: str = Field(
        ...,
        alias='newOwnerUserId',
        description='User id of the new owner; must be a member of the organization.',
        max_length=200,
        min_length=1,
    )


class TransferOwnershipDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    new_owner_user_id: str = Field(
        ...,
        alias='newOwnerUserId',
        description='Clerk user id of the org member who will become the new owner.',
        examples=['user_2abc123def456'],
    )


class TriggerType(str, Enum):
    schedule = 'schedule'
    webhook = 'webhook'
    api = 'api'
    slack = 'slack'
    manual = 'manual'


class TriggerEvaluationRunResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    run_id: str = Field(..., alias='runId', description='The created run ID')
    workflow_id: str | None = Field(
        None, alias='workflowId', description='Workflow identifier for the run'
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


class UpdateAgentInterfaceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        None,
        description='New display name.',
        examples=['Internal MCP v2'],
        max_length=200,
        min_length=1,
    )
    config: dict[str, Any] | None = Field(
        None,
        description='New config payload (interface-type-specific). Free-form JSONB. Replaces the prior config.',
        examples=[{}],
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


class UpdateCustomContextItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        None, description='Replacement display name.', examples=['Acme renewal contract']
    )
    entity_type: str | None = Field(
        None,
        alias='entityType',
        description='Replacement customer-defined entity or field type.',
        examples=['contract'],
    )
    description: str | None = Field(
        None,
        description='Replacement description.',
        examples=['Updated internal billing metadata.'],
    )
    content: dict[str, Any] | None = Field(
        None, description='Replacement main textual or structured content.'
    )
    url: str | None = Field(
        None,
        description='Replacement customer-facing URL.',
        examples=['https://internal.example.com/contracts/contract-123'],
    )
    attributes: list[CustomAttributeDto] | None = Field(
        None, description='Replacement structured attributes.'
    )
    data_type: str | None = Field(
        None, alias='dataType', description='Replacement field data type.', examples=['timestamp']
    )
    value: dict[str, Any] | None = Field(
        None, description='Replacement representative field value.'
    )
    samples: list[dict[str, Any]] | None = Field(
        None, description='Replacement representative samples.'
    )
    raw: dict[str, Any] | None = Field(
        None, description='Replacement customer-specific raw fields.'
    )
    topics: list[str] | None = Field(
        None,
        description='Replacement topic tags. Pass `[]` to clear all tags.',
        examples=[['billing', 'verified']],
    )


class UpdateDashboardAccessDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    visibility: DashboardVisibility = Field(
        ...,
        description='shared: the owner and the groups granted in groupPermissions; private: the owner and the users in sharedWith.',
    )
    group_permissions: dict[str, DashboardGroupPermissionDto] = Field(
        ...,
        alias='groupPermissions',
        description='Group id to permissions. Used only when visibility is shared; ignored when private.',
    )
    shared_with: list[DashboardSharedUserDto] = Field(
        ...,
        alias='sharedWith',
        description='Users granted access. Used only when visibility is private; ignored when shared.',
    )


class UpdateDashboardLayoutDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_revision: int = Field(
        ...,
        alias='expectedRevision',
        description='Draft revision the change is based on; a stale value is rejected with 409.',
        ge=1,
    )
    elements: list[DashboardLayoutElementDto] = Field(
        ...,
        description='Every affected item with its final x, y, width, and height.',
        max_length=300,
        min_length=1,
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
        description='Replacement metadata bag. Optional.',
        examples=[{'topic': 'preferences', 'confidence': 'high'}],
    )


class UpdateScopeInterfaceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        None, description='New display name.', examples=['Support'], max_length=200, min_length=1
    )
    config: ChatInterfaceConfigDto | None = Field(None, description='Replaces the whole config.')


class UploadFromUrlDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    url: str = Field(
        ...,
        description='Source URL to fetch. SSRF-guarded; every redirect hop is re-validated.',
        examples=['https://example.com/reports/Q3-churn-report.pdf'],
    )
    file_name: str | None = Field(
        None,
        alias='fileName',
        description='Override file name. Inferred from the URL path when omitted.',
        examples=['Q3-churn-report.pdf'],
    )
    folder_path: str | None = Field(
        None,
        alias='folderPath',
        description='Root-relative folder path for this upload (for example `reports/2026`). Omit to store at the Files root. To reuse a folder created by an upload, pass its `folderPath`.',
        examples=['reports/2026/Q3'],
    )


class UploadUrlDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    file_name: str = Field(
        ...,
        alias='fileName',
        description='Original file name, used to build the S3 object key.',
        examples=['Q3-churn-report.pdf'],
    )
    content_type: str = Field(
        ...,
        alias='contentType',
        description='MIME type of the file. `application/octet-stream` falls back to an extension-based guess. Allowed categories: PDF, images, text, Office/OpenDocument documents, audio, and video.',
        examples=['application/pdf'],
    )
    file_size: float = Field(
        ...,
        alias='fileSize',
        description='File size in bytes. Rejected above 50MB.',
        examples=[1048576],
    )


class UploadUrlResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    upload_id: str = Field(
        ...,
        alias='uploadId',
        description='Server-generated id for this upload. Use it on `GET /context/files/{uploadId}`.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    upload_url: str = Field(
        ...,
        alias='uploadUrl',
        description='Presigned S3 URL. PUT the raw file bytes here within 15 minutes.',
        examples=['https://tenant-bucket.s3.amazonaws.com/context_uploads/...'],
    )
    s3_key: str = Field(
        ...,
        alias='s3Key',
        description='Tenant S3 key the file will land at once uploaded.',
        examples=['context_uploads/7a3f9d2c.../Q3-churn-report.pdf'],
    )
    file_name: str = Field(
        ...,
        alias='fileName',
        description='Sanitized file name (non-alphanumeric characters replaced with `_`).',
        examples=['Q3-churn-report.pdf'],
    )
    content_type: str = Field(
        ...,
        alias='contentType',
        description='Resolved content type (extension-inferred when the request sent `application/octet-stream`).',
        examples=['application/pdf'],
    )
    expires_at: str = Field(
        ...,
        alias='expiresAt',
        description='ISO timestamp when the presigned URL expires (15 minutes from creation).',
        examples=['2026-08-12T14:15:00.000Z'],
    )
    headers: dict[str, str] = Field(
        ...,
        description='Headers to send unchanged with the upload PUT request.',
        examples=[{'Content-Type': 'application/pdf'}],
    )


class UsageBucketDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    bucket: str = Field(..., description='ISO8601 timestamp at the start of the bucket.')
    model: str | None = Field(
        None,
        description='Canonicalised LLM model name. Present only when grouping by model (where it equals `group_value`); omitted on scope/workflow/interface breakdowns, where the grouped value lives in `group_value`.',
    )
    group_value: str = Field(
        ..., description='The grouped dimension value (scope/workflow id, interface, or model).'
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


class UsageUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str = Field(
        ...,
        description='Acting-user email present in usage over the window.',
        examples=['jane@acme.com'],
    )


class WorkflowEdgeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(..., description='Stable edge id, unique within the graph.', examples=['e1'])
    source: str = Field(..., description='Source node id.', examples=['1'])
    target: str = Field(..., description='Target node id.', examples=['2'])
    source_handle: str | None = Field(
        None,
        alias='sourceHandle',
        description='Source port handle (e.g. a condition branch). Omit for a single-output node.',
        examples=['branch_0'],
    )


class WorkflowNodePositionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    x: float = Field(..., examples=[0])
    y: float = Field(..., examples=[50])


class WorkflowNodeType(str, Enum):
    start = 'start'
    action = 'action'
    condition = 'condition'
    agent = 'agent'
    human_approval = 'humanApproval'


class ActiveConversationRunStatus(str, Enum):
    queued = 'queued'
    pending = 'pending'
    running = 'running'


class ActiveRunsBySessionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    session_ids: list[str] = Field(
        ...,
        alias='sessionIds',
        description='Conversation thread ids to check for non-terminal runs.',
        max_length=100,
    )


class Version(str, Enum):
    published = 'published'
    draft = 'draft'


class StreamProtocolVersion(float, Enum):
    number_2 = 2


class CancelRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization the run belongs to. Omit for PAT/SDK callers — falls back to the authenticated principal's org.",
    )
    reason: str | None = Field(
        None, description='Human-readable reason for the cancel, logged server-side only.'
    )
    last_seen_event_id: str | None = Field(
        None,
        alias='lastSeenEventId',
        description='Redis Stream id of the last SSE frame the client rendered, so the persisted partial message matches what the client saw. Falls back to the server-side accumulator when absent.',
    )


class DocumentAttachmentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    file_name: str = Field(..., alias='fileName', description='Original file name.')
    parsed_content: str | None = Field(None, alias='parsedContent')
    upload_id: str | None = Field(None, alias='uploadId')
    mime_type: str | None = Field(None, alias='mimeType')
    original_size: float | None = Field(None, alias='originalSize')
    storage_file_name: str | None = Field(None, alias='storageFileName')
    raw_content_s3_key: str | None = Field(None, alias='rawContentS3Key')
    size_bytes: float | None = Field(None, alias='sizeBytes')
    summary: str | None = None


class ErrorEnvelopeDto1(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    code: ApiErrorCode = Field(..., description='Modus-specific machine code.')
    status: ApiErrorStatus = Field(..., description='Canonical status string for the error.')
    message: str = Field(..., examples=['Run was not found or you lack permission.'])
    request_id: str = Field(..., alias='requestId', examples=['req_01HQ7K8ABCDEFGHIJKLMNOPQRS'])
    info: dict[str, Any] | None = Field(
        None,
        description='Optional domain-specific context. Shape varies per endpoint.',
        examples=[{'runId': 'run_abc123'}],
    )


class ErrorResponseDto1(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    error: ErrorEnvelopeDto1


class ImageAttachmentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    data: str | None = None
    mime_type: str | None = Field(None, alias='mimeType')
    name: str | None = None
    s3_key: str | None = Field(None, alias='s3Key')
    upload_id: str | None = Field(None, alias='uploadId')


class Decision(str, Enum):
    approve = 'approve'
    deny = 'deny'
    connected = 'connected'
    cancelled = 'cancelled'


class RunReasoningEffort(str, Enum):
    none = 'none'
    minimal = 'minimal'
    low = 'low'
    medium = 'medium'
    high = 'high'
    xhigh = 'xhigh'
    max = 'max'


class RunSource(str, Enum):
    home = 'home'
    agent_settings = 'agent_settings'
    agent = 'agent'
    api = 'api'
    modus_api = 'modus_api'
    mcp = 'mcp'
    slack = 'slack'
    slack_dm = 'slack_dm'
    teams = 'teams'
    context_chat = 'context_chat'
    dashboard_copilot = 'dashboard_copilot'
    dashboard_assistant = 'dashboard_assistant'
    other = 'other'


class SupplementalContextSource(str, Enum):
    slack = 'slack'
    teams = 'teams'


class UserContextDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str | None = Field(
        None, description='End-user email for personalization; also used for usage attribution.'
    )
    name: str | None = Field(None, description='End-user display name.')
    timezone: str | None = Field(None, description='IANA timezone, e.g. America/New_York.')
    user_id: str | None = Field(
        None, alias='userId', description='User id for system/PAT runs (usage attribution).'
    )


class WorkflowActionSource(str, Enum):
    agent = 'agent'
    api = 'api'
    other = 'other'


class AddAgentInterfaceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    type: AgentInterfaceType = Field(
        ...,
        description='Interface type. Only `slack`, `mcp`, and `teams` are accepted.',
        examples=['mcp'],
    )
    name: str = Field(
        ...,
        description='Display name for the interface.',
        examples=['Internal MCP'],
        max_length=200,
        min_length=1,
    )
    config: dict[str, Any] | None = Field(
        None,
        description='Initial config payload (interface-type-specific). Free-form JSONB.',
        examples=[{}],
    )


class AddScopeInterfaceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    type: ChatInterfaceType = Field(
        ..., description='Chat platform. One interface per type per scope.', examples=['slack']
    )
    name: str | None = Field(
        None,
        description='Display name. Defaults to the chat platform name.',
        examples=['Support'],
        max_length=200,
        min_length=1,
    )
    config: ChatInterfaceConfigDto | None = None


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
        description='Per-user share entries used for private-visibility workflows.',
        examples=[[]],
    )
    owner_user_id: str | None = Field(
        None,
        alias='ownerUserId',
        description='Clerk user id of the workflow owner. Set on first write for private workflows.',
        examples=['user_2abc'],
    )
    owner_email: str | None = Field(
        None,
        alias='ownerEmail',
        description='Lowercased email of the workflow owner. Used by private-workflow ACL when owner email matches.',
        examples=['alice@example.com'],
    )


class AgentInterfaceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(
        ...,
        description='Interface row id (UUID).',
        examples=['00000000-0000-4000-a000-000000000300'],
    )
    agent_id: float = Field(..., alias='agentId', description='Parent workflow id.', examples=[42])
    type: AgentInterfaceType = Field(
        ...,
        description='Interface type. `slack` and `teams` deliver chat triggers; `mcp` exposes the workflow as an MCP server.',
        examples=['mcp'],
    )
    name: str = Field(
        ...,
        description='Display name for the interface (shown in the SPA).',
        examples=['Internal MCP'],
    )
    config: dict[str, Any] = Field(
        ...,
        description='Interface-type-specific configuration (e.g. webhook url, MCP token references). Free-form JSONB.',
        examples=[{}],
    )
    created_at: str = Field(
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


class BatchCreateCustomContextItemRelationsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    relations: list[CreateCustomContextItemRelationDto] = Field(
        ...,
        description='Relations to upsert. Idempotent by (fromUid, toUid, relationType); re-sending updates content.',
    )


class BatchCreateCustomContextItemsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    context_items: list[CreatedCustomContextItemResponseDto] = Field(
        ...,
        alias='contextItems',
        description='Custom context items created or updated by the batch.',
    )


class BulkFinalizeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uploads: list[BulkFinalizeItemDto] = Field(
        ..., description='Uploads to finalize. Max 100 per request.'
    )


class BulkUploadUrlsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uploaded: list[UploadUrlResponseDto] = Field(
        ..., description='Presigned upload slots for every file that passed validation.'
    )
    failed: list[FailedUploadUrlDto] = Field(
        ...,
        description='Per-item failures (bad MIME type, oversize, etc). Empty when every file succeeded.',
    )


class ConversationMessageDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    type: ConversationMessageType = Field(
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


class CreateCustomContextItemDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    kind: CustomContextItemKind = Field(
        ..., description='Shape of custom context item to create.', examples=['entity']
    )
    source_id: str = Field(
        ...,
        alias='sourceId',
        description='Stable identifier for the customer-defined source.',
        examples=['billing-db'],
    )
    source_name: str | None = Field(
        None,
        alias='sourceName',
        description='Display name for the customer-defined source.',
        examples=['Billing database'],
    )
    collection_id: str | None = Field(
        None,
        alias='collectionId',
        description='Stable identifier for the collection inside the source.',
        examples=['contracts'],
    )
    collection_name: str | None = Field(
        None,
        alias='collectionName',
        description='Display name for the collection.',
        examples=['Contracts'],
    )
    external_id: str | None = Field(
        None,
        alias='externalId',
        description='Stable identifier for the entity inside the collection.',
        examples=['contract-123'],
    )
    field_name: str | None = Field(
        None,
        alias='fieldName',
        description='Field name for field-level custom context.',
        examples=['renewalDate'],
    )
    name: str | None = Field(
        None, description='Display name for the item.', examples=['Acme renewal contract']
    )
    entity_type: str | None = Field(
        None,
        alias='entityType',
        description='Customer-defined entity or field type.',
        examples=['contract'],
    )
    description: str | None = Field(
        None,
        description='Human-readable description.',
        examples=['Enterprise contract renewal metadata from the internal billing system.'],
    )
    content: dict[str, Any] | None = Field(
        None, description='Main textual or structured content for the custom item.'
    )
    url: str | None = Field(
        None,
        description='Customer-facing URL for the source object, when available.',
        examples=['https://internal.example.com/contracts/contract-123'],
    )
    attributes: list[CustomAttributeDto] | None = Field(
        None, description='Structured attributes for entity-level custom context.'
    )
    data_type: str | None = Field(
        None,
        alias='dataType',
        description='Field data type for field-level custom context.',
        examples=['timestamp'],
    )
    value: dict[str, Any] | None = Field(
        None, description='Representative value for field-level custom context.'
    )
    samples: list[dict[str, Any]] | None = Field(
        None, description='Representative samples for entity sample context.'
    )
    raw: dict[str, Any] | None = Field(
        None,
        description='Customer-specific fields that should be retained but are not part of the normalized contract.',
    )
    topics: list[str] | None = Field(
        None, description='Topic tags for filtering.', examples=[['billing', 'renewals']]
    )
    idempotency_key: str | None = Field(
        None,
        alias='idempotencyKey',
        description='Optional stable key used to make single-item creates idempotent.',
        examples=['billing-db/contracts/contract-123'],
    )
    access: AccessPolicyDto | None = None


class CreateDashboardElementDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_revision: int = Field(
        ...,
        alias='expectedRevision',
        description='Draft revision the change is based on; a stale value is rejected with 409.',
        ge=1,
    )
    kind: DashboardElementKind = Field(
        ..., description='Element to create: a chart, KPI, table or markdown tile, or a filter.'
    )
    title: str = Field(..., description='Title shown on the element.', max_length=500, min_length=1)
    layout: DashboardElementLayoutDto = Field(..., description='Grid position of the new element.')


class DashboardAccessDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    visibility: DashboardVisibility = Field(
        ...,
        description='shared: the owner and the groups granted in groupPermissions; private: the owner and the users in sharedWith.',
    )
    group_permissions: dict[str, DashboardGroupPermissionDto] = Field(
        ...,
        alias='groupPermissions',
        description='Group id to permissions. Used only when visibility is shared; ignored when private.',
    )
    shared_with: list[DashboardSharedUserDto] = Field(
        ...,
        alias='sharedWith',
        description='Users granted access. Used only when visibility is private; ignored when shared.',
    )


class DashboardAccessResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    visibility: DashboardVisibility
    group_permissions: dict[str, DashboardGroupPermissionDto] = Field(
        ..., alias='groupPermissions', description='Permissions by group id.'
    )
    shared_with: list[DashboardSharedUserDto] = Field(..., alias='sharedWith')
    owner_user_id: str = Field(..., alias='ownerUserId')
    owner_email: str | None = Field(..., alias='ownerEmail')


class DashboardChartConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="allow")
    type: str = Field(
        ..., description='Any Chart.js chart type registered by the renderer.', min_length=1
    )
    label_column: str = Field(..., alias='labelColumn', max_length=500, min_length=1)
    datasets: list[DashboardChartDatasetDto] = Field(
        ...,
        description='Chart.js datasets. valueColumn maps SQL results to data; all other Chart.js dataset settings pass through.',
        min_length=1,
    )
    options: dict[str, Any] | None = Field(
        None, description='Full JSON-serializable Chart.js options object.'
    )


class DashboardElementDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str
    kind: DashboardElementKind
    title: str | None = None
    layout: dict[str, Any] | None = Field(
        ..., description='Grid position (x, y, w, h), or null when the element has none.'
    )
    connection_id: str | None = Field(
        None, alias='connectionId', description='Chart, KPI and table tiles.'
    )
    sql: str | None = Field(None, description='Chart, KPI and table tiles.')
    chart_config: dict[str, Any] | None = Field(
        None,
        alias='chartConfig',
        description='Chart tiles: the chart settings, or null when none are set.',
    )
    format: str | None = Field(None, description='KPI tiles: display format of the value.')
    markdown: str | None = Field(None, description='Markdown tiles.')
    filter_type: str | None = Field(
        None,
        alias='filterType',
        description='Filters: the filter type as stored, which can also be a storage type such as string_list.',
    )
    required: bool | None = None
    options: list[str] | None = None
    allow_multiple: bool | None = Field(None, alias='allowMultiple')
    quotation: str | None = Field(None, description='Filters: how the value is quoted in SQL.')
    regex: str | None = None
    options_query: dict[str, Any] | None = Field(
        None,
        alias='optionsQuery',
        description='Query dropdown filters: connectionId, sql, valueColumn and labelColumn.',
    )
    default_value: str | float | bool | list[str | float] | dict[str, Any] | None = Field(
        None,
        alias='defaultValue',
        description='Default filter value; a { start, end } object for date and datetime ranges.',
    )
    sql_references: list[str] | None = Field(
        None,
        alias='sqlReferences',
        description='Filters: the exact {{ ... }} templates tile SQL uses to reference this filter.',
    )


class DashboardElementPatchDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    title: str | None = Field(None, description='Element title.', max_length=500)
    connection_id: str | None = Field(
        None, alias='connectionId', description='Connection the tile query runs on.', max_length=200
    )
    sql: str | None = Field(
        None, description='SQL query of a chart, KPI or table tile.', max_length=100000
    )
    chart_config: DashboardChartConfigDto | None = Field(
        None, alias='chartConfig', description='Chart settings of a chart tile; null clears them.'
    )
    format: DashboardValueFormat | None = Field(None, description='Display format of a KPI value.')
    markdown: str | None = Field(
        None, description='Content of a markdown tile.', max_length=1000000
    )
    filter_type: DashboardFilterType | None = Field(
        None,
        alias='filterType',
        description='Use only the listed editor filter types. Configure a compatible defaultValue in the same patch.',
    )
    required: bool | None = Field(
        None, description='Whether the filter needs a value before tiles run.'
    )
    options: list[Option] | None = Field(None, description='Fixed choices of a dropdown filter.')
    allow_multiple: bool | None = Field(
        None, alias='allowMultiple', description='Whether a dropdown filter accepts several values.'
    )
    quotation: DashboardQuotationStyle | None = Field(
        None, description='How the filter value is quoted when inserted into SQL.'
    )
    regex: str | None = Field(
        None, description='Pattern a text filter value must match.', max_length=500
    )
    options_query: DashboardFilterOptionsQueryPatchDto | None = Field(
        None,
        alias='optionsQuery',
        description='Query that supplies the choices of a query dropdown filter.',
    )
    default_value: str | float | bool | DefaultValue | DefaultValue1 | None = Field(
        None,
        alias='defaultValue',
        description='Use { start, end } for date/datetime ranges; null clears the default. The value must match the filterType and allowMultiple setting.',
    )
    layout: DashboardElementLayoutDto | None = Field(
        None, description='New grid position of the element.'
    )


class DashboardElementResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    dashboard_id: str = Field(..., alias='dashboardId')
    draft_revision: int = Field(
        ...,
        alias='draftRevision',
        description='Current draft revision; pass it as expectedRevision on the next write.',
    )
    element: DashboardElementDto


class DashboardFilterDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str
    label: str
    type: DashboardFilterValueType
    required: bool
    quotation: DashboardQuotationStyle | None = None
    regex: str | None = None
    default_value: str | float | bool | list[str | float] | dict[str, Any] | None = Field(
        None,
        alias='defaultValue',
        description='Default filter value; a { start, end } object for date and datetime ranges.',
    )


class DashboardSelectedVersionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str | None = Field(..., description='Null for the draft.')
    version_number: int | None = Field(..., alias='versionNumber', description='Null for the draft.')
    created_by_user_id: str = Field(..., alias='createdByUserId')
    created_at: str = Field(..., alias='createdAt', examples=['2026-09-16T10:00:00.000Z'])
    access: DashboardAccessResponseDto


class DashboardTileDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str
    title: str
    kind: DashboardTileKind
    connection_id: str | None = Field(None, alias='connectionId')
    sql: str | None = None
    config: dict[str, Any]


class DashboardVersionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str
    dashboard_uid: str = Field(..., alias='dashboardUid')
    version_number: int | None = Field(
        ...,
        alias='versionNumber',
        description='Sequential number for published versions; null for draft snapshots.',
    )
    kind: DashboardVersionKind
    title: str
    description: str
    access: DashboardAccessResponseDto
    definition: dict[str, Any] = Field(
        ..., description='The definition as stored for this version.'
    )
    created_by_user_id: str = Field(..., alias='createdByUserId')
    created_at: str = Field(..., alias='createdAt', examples=['2026-09-16T10:00:00.000Z'])


class EvaluationCadenceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    frequency: EvaluationCadenceFrequency | None = Field(None, description='Schedule frequency')
    time_of_day: str | None = Field(
        None, alias='timeOfDay', description='Time of day in HH:MM format', examples=['09:00']
    )
    timezone: str | None = Field(None, description='IANA timezone', examples=['America/New_York'])
    weekdays: list[str] | None = Field(
        None, description='Days of week for weekly frequency', examples=[['MONDAY', 'WEDNESDAY']]
    )
    day_of_month: float | None = Field(
        None, alias='dayOfMonth', description='Day of month for monthly frequency', ge=1.0, le=31.0
    )
    cron_expression: str | None = Field(
        None,
        alias='cronExpression',
        description='Cron expression for custom frequency',
        examples=['0 9 * * 1-5'],
    )


class EvaluationChannelsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: bool = Field(..., description='Enable email notifications')
    slack: EvaluationSlackChannelDto | None = Field(
        None, description='Slack notification configuration'
    )


class EvaluationNotificationsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    recipients: list[EvaluationRecipientDto] = Field(..., description='Notification recipients')
    channels: EvaluationChannelsDto = Field(..., description='Notification channels')


class EvaluationRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(..., description='Run ID')
    skill_id: float = Field(..., alias='skillId', description='Scope ID')
    trigger: EvaluationRunTrigger = Field(..., description='How the run was triggered')
    status: EvaluationRunStatus = Field(..., description='Run status')
    started_at: str = Field(..., alias='startedAt', description='When the run started')
    finished_at: dict[str, Any] | None = Field(
        None, alias='finishedAt', description='When the run finished'
    )
    total_cases: float = Field(
        ..., alias='totalCases', description='Total number of evaluation cases'
    )
    passed_cases: float = Field(..., alias='passedCases', description='Number of passed cases')
    failed_cases: float = Field(..., alias='failedCases', description='Number of failed cases')
    avg_score: dict[str, Any] | None = Field(
        None, alias='avgScore', description='Average score (0-100)'
    )
    is_regression: bool = Field(
        ..., alias='isRegression', description='Whether this run detected a regression'
    )
    judge_model: str | None = Field(None, alias='judgeModel', description='Judge model used')
    error_message: str | None = Field(
        None, alias='errorMessage', description='Error message if failed'
    )


class FileUploadResourceDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    upload_id: str = Field(
        ...,
        alias='uploadId',
        description='Upload id — same value returned by `uploadUrl`/`uploadUrls`.',
        examples=['7a3f9d2c-1111-4000-a000-000000000abc'],
    )
    status: FileUploadResourceStatus = Field(
        ..., description='Current processing status.', examples=['ready']
    )
    file_name: str | None = Field(None, alias='fileName', examples=['Q3-churn-report.pdf'])
    folder_path: str | None = Field(
        None,
        alias='folderPath',
        description='Relative folder path within Files. Null at the Files root.',
        examples=['reports/2026/Q3'],
    )
    content_type: str | None = Field(None, alias='contentType', examples=['application/pdf'])
    file_size: float | None = Field(None, alias='fileSize', examples=[1048576])
    s3_key: str | None = Field(
        None, alias='s3Key', examples=['context_uploads/7a3f9d2c.../Q3-churn-report.pdf']
    )
    created_at: str | None = Field(None, alias='createdAt', examples=['2026-08-12T14:00:00.000Z'])
    summary: str | None = Field(
        None, description='Generated summary once parsing completes. Null until then.'
    )
    parsed: bool | None = Field(
        None, description='Whether the file was successfully parsed. Null while pending/processing.'
    )
    document_count: float | None = Field(None, alias='documentCount', examples=[1])
    error_message: str | None = Field(
        None, alias='errorMessage', description='Populated when `status` is `failed`.'
    )


class HttpIngestedDataRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    type: Literal['http'] = Field(..., examples=['http'])
    uri: str = Field(
        ...,
        description='Request URI exactly as sent.',
        examples=['https://api.example.com/v1/orders?status=open'],
    )
    method: str = Field(..., description='HTTP method exactly as sent.', examples=['GET'])
    body: str | None = Field(
        None,
        description='Request body exactly as sent. An omitted body is stored as an empty string, so both spellings of a bodiless request share one checksum.',
        examples=['{"status":"open"}'],
    )


class IngestedDataResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    status: int | None = Field(
        None,
        description='HTTP status returned by the source endpoint.',
        examples=[200],
        ge=100,
        le=599,
    )
    format: IngestedDataResponseFormat = Field(..., examples=['json'])
    content: str = Field(
        ...,
        description='Response content exactly as received, including an empty response.',
        examples=['{"orders":[]}'],
    )


class ListAgentInterfacesResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    interfaces: list[AgentInterfaceDto] = Field(
        ..., description='All interfaces attached to the workflow (in creation order).'
    )


class ListDashboardVersionsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    versions: list[DashboardVersionDto] = Field(
        ...,
        description='Published versions only, newest first, each with its full definition; not paginated.',
    )


class ListEvaluationRunsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    runs: list[EvaluationRunDto]
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
    )


class ListFilesResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    files: list[FileUploadResourceDto] = Field(
        ..., description='Page of durable file uploads. Empty when none match.'
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page.',
        examples=['eyJjcmVhdGVkQXQiOiIyMDI2LTA1LTAxIiwidWlkIjoiYWJjIn0'],
    )


class ListMemoriesResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    memories: list[MemoryDto] = Field(..., description='Memories belonging to the scope.')
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
        examples=['eyJvZmZzZXQiOjI1LCJwYWdlU2l6ZSI6MjV9'],
    )


class ListOrgMembersResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    members: list[OrgMemberDto]


class ListScopeInterfacesResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    interfaces: list[ScopeInterfaceDto] = Field(
        ..., description='Every chat interface on the scope (at most one per type).'
    )


class ListSuggestionQuestionsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    suggestions: list[SuggestionQuestionDto]
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
        examples=['eyJvZmZzZXQiOjUsInBhZ2VTaXplIjo1fQ'],
    )


class ListToolsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    tools: list[ToolCatalogEntryDto] = Field(
        ..., description='Known tool/integration surfaces a scope can select in its toolset.'
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; null when this was the last page. Pass as `pageToken` on the next request.',
        examples=[None],
    )


class ListUsageResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    org_id: str = Field(..., description='Organization id (`org_xxx`) the result is scoped to.')
    since: str
    until: str
    rollup: Rollup
    group_by: GroupBy = Field(..., description='Dimension that was grouped by in this response.')
    buckets: list[UsageBucketDto]
    totals: UsageTotalsDto


class ListUsageUsersResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    users: list[UsageUserDto] = Field(..., description='Distinct acting-user emails in the window.')


class LookupContextItemResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    item: LookupContextItemRowDto | None = Field(
        ...,
        description="The matched row, or null when no row in the caller's tenant matches the supplied `(contextType, dataPath)`.",
    )


class MemberGroupDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uid: str
    name: str
    description: str
    member_ids: list[str] | None = Field(
        None,
        description='Clerk user ids in this group. Present for native groups (the synthesized Everyone group included). Absent for directory-sourced groups — use `member_count`; membership is directory-managed.',
    )
    created_at: str
    updated_at: str
    source: MemberGroupSource | None = Field(
        None,
        description='Provenance of the group: org-managed ("native") or backed by an identity-provider directory group ("directory").',
        examples=['native'],
    )
    member_count: float | None = Field(
        None,
        description='Member count for directory-sourced groups. Present (and non-null) only when `source` is "directory".',
        examples=[42],
    )


class ModelSettingsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    reasoning_effort: ReasoningEffort | None = Field(
        None,
        alias='reasoningEffort',
        description='Optional reasoning effort for models that support it.',
    )
    context_window: float | None = Field(
        None, alias='contextWindow', description='Selected model context window in tokens.', ge=1.0
    )


class PatchSkillMcpConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    config: SkillMcpInterfaceConfigDto = Field(
        ...,
        description='Full MCP interface config written to the scope draft; takes effect on the next deploy.',
    )


class PatchSkillMcpConfigResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    config: SkillMcpInterfaceConfigDto = Field(
        ..., description='Sanitized MCP config now stored on the scope draft.'
    )


class RecordSuggestionEventDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    event_type: SuggestionEventType = Field(
        ...,
        alias='eventType',
        description='First-party Home suggestion interaction.',
        examples=['clicked'],
    )
    source: SuggestionEventSource | None = Field(
        None, description='Product surface that emitted the event.', examples=['home']
    )
    skill_id: float | None = Field(
        None, alias='skillId', description='Selected Home scope id when known.'
    )
    thread_id: str | None = Field(
        None,
        alias='threadId',
        description='Conversation thread id when the event is tied to a chat.',
    )
    metadata: dict[str, Any] | None = Field(None, description='Event metadata.')


class SharedUserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    email: str = Field(
        ...,
        description='Lowercased email of a user explicitly granted access to a private scope.',
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
    permission: SharedUserPermission | None = Field(
        None,
        description='Per-invitee access level for private scopes. `manage` grants edit / deploy / delete (implies use); `use` (default) grants run-only.',
        examples=['use'],
    )


class SkillVariationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_output: str = Field(
        ...,
        alias='expectedOutput',
        description='Free-form expected-output prompt that constrains the scope’s reply.',
        examples=['A 3-bullet summary highlighting churn risk drivers.'],
    )
    instructions: list[str] = Field(
        ...,
        description='Ordered list of instruction blocks. Each entry is a free-form string the builder rendered into the system prompt.',
        examples=[['Be concise.', 'Always justify the score.']],
    )
    model: str = Field(
        ...,
        description='Provider-prefixed model id. The orchestrator routes by prefix.',
        examples=['anthropic/claude-sonnet-4.6'],
    )
    model_settings: ModelSettingsDto | None = Field(
        None,
        alias='modelSettings',
        description='Model-specific runtime controls such as reasoning effort and context window.',
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
        description='IDs of scopes supervised by this scope (when it is a manager). Stringified for wire stability.',
        examples=[['12', '17']],
    )
    supervision_subordinate_descriptions: dict[str, str] = Field(
        ...,
        alias='supervisionSubordinateDescriptions',
        description='Map of subordinateId -> manager-provided description blurb.',
        examples=[{'12': 'Reads warehouse facts', '17': 'Drafts the report'}],
    )


class SqlIngestedDataRequestDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    type: Literal['sql'] = Field(..., examples=['sql'])
    query: str = Field(
        ...,
        description='SQL query exactly as executed.',
        examples=["SELECT * FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"],
    )


class ToolsetDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    tools: list[ToolsetToolDto] | None = Field(
        None,
        description='List of tools the scope may invoke.',
        examples=[[{'id': 'web_search', 'enabled': True}]],
    )


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


class UpdateDashboardElementDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_revision: int = Field(
        ...,
        alias='expectedRevision',
        description='Draft revision the change is based on; a stale value is rejected with 409.',
        ge=1,
    )
    patch: DashboardElementPatchDto = Field(
        ..., description='Fields to change; include at least one.'
    )


class UpdateEvaluationConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    enabled: bool | None = Field(None, description='Whether scheduled evaluations are enabled')
    cadence: EvaluationCadenceDto | None = Field(None, description='Schedule cadence configuration')
    judge_model: str | None = Field(
        None, alias='judgeModel', description='Model ID for the judge LLM'
    )
    judge_guidance: str | None = Field(
        None, alias='judgeGuidance', description='Custom guidance for the judge LLM'
    )
    notifications: EvaluationNotificationsDto | None = Field(
        None, description='Regression notification settings'
    )


class WorkflowDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: float = Field(
        ...,
        description='Numeric workflow id (stable per-org; not reused after delete).',
        examples=[42],
    )
    slug: str = Field(
        ...,
        description='URL-safe slug used in human-readable links. Unique per org.',
        examples=['customer-churn-agent-a3f'],
    )
    name: str = Field(
        ...,
        description='Display name of the workflow. Shown in the builder and in run logs.',
        examples=['Customer Churn Analyzer'],
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description of what this workflow does.',
        examples=['Predicts churn risk for a customer given a 90-day usage window.'],
    )
    status: ResourceLifecycleStatus = Field(
        ...,
        description='Lifecycle status. `draft` = never deployed. `active` = deployed. `deleted` = soft-deleted.',
        examples=['active'],
    )
    type: AgentType = Field(
        ...,
        description='Type of workflow. `task` = single-step scope orchestration; `workflow` = multi-step graph.',
        examples=['task'],
    )
    org_uuid: str = Field(
        ...,
        alias='orgUuid',
        description='Org UUID this workflow belongs to. Matches the caller’s principal.',
        examples=['00000000-0000-0000-0000-000000000001'],
    )
    active_variation_id: str | None = Field(
        None,
        alias='activeVariationId',
        description='Active (deployed) variation id. Null until the workflow is first deployed.',
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
        description='Whether the workflow’s schedule is currently active. Toggle via the workflow schedule API.',
        examples=[True],
    )
    access_config: AgentAccessConfigDto = Field(
        ...,
        alias='accessConfig',
        description='Access configuration — who in the org can use / manage this workflow.',
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
    created_at: str = Field(
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
        description='Soft-delete timestamp. Null for active workflows.',
        examples=[None],
    )
    can_manage: bool = Field(
        ...,
        alias='canManage',
        description='Whether the requesting principal can manage (edit/delete/deploy/toggle) this workflow. Derived server-side from the principal + accessConfig. Always present on every Workflow response.',
        examples=[True],
    )
    can_use: bool = Field(
        ...,
        alias='canUse',
        description='Whether the requesting principal can use (run, view history of) this workflow. Derived server-side from the principal + accessConfig. Always present on every Workflow response.',
        examples=[True],
    )
    manage_denial: ManageDenial | None = Field(
        ...,
        alias='manageDenial',
        description='Why `canManage` is false, for client-facing guidance: `needs_group_manage` (shared, but no group you belong to grants Manage) or `not_owner` (private, and you are not the owner). `null` when `canManage` is true. Derived server-side from the principal + accessConfig.',
        examples=['needs_group_manage'],
    )
    dashboard_alert: AgentDashboardAlertDto | None = Field(
        None,
        alias='dashboardAlert',
        description='Set when a dashboard KPI alert generated this workflow. Changing its definition requires disconnectDashboardAlert.',
    )


class WorkflowNodeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str = Field(..., description='Stable node id, unique within the graph.', examples=['1'])
    type: WorkflowNodeType = Field(
        ...,
        description='Node kind. Determines how the runtime interprets `data`.',
        examples=['start'],
    )
    position: WorkflowNodePositionDto | None = Field(
        None, description='Canvas position. Optional — preserved for builder layout when present.'
    )
    data: dict[str, Any] | None = Field(
        None,
        description='Node-type-specific payload (intentionally open — shape varies by `type`). Defaults to `{}`.',
        examples=[{}],
    )


class WorkflowStructureDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    nodes: list[WorkflowNodeDto] | None = Field(
        None, description='Workflow nodes. Defaults to `[]`.'
    )
    edges: list[WorkflowEdgeDto] | None = Field(
        None, description='Directed edges connecting the nodes. Defaults to `[]`.'
    )


class ActiveConversationRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    run_id: str = Field(..., alias='runId', description='Run identifier.')
    session_id: str = Field(..., alias='sessionId', description='Conversation thread id.')
    status: ActiveConversationRunStatus = Field(..., description='Current non-terminal run status.')
    message: str | None = Field(None, description='User message that started the run.')
    source: str | None = Field(None, description='Client interaction source for the run.')
    created_at: AwareDatetime = Field(..., alias='createdAt', description='Creation timestamp.')
    updated_at: AwareDatetime = Field(
        ..., alias='updatedAt', description='Most recent update timestamp.'
    )


class ActiveRunsBySessionResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    runs: list[ActiveConversationRunDto]


class ActiveRunsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    runs: list[ActiveConversationRunDto]
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page, or `null` if there are no more active runs.',
    )


class AttachmentsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    images: list[ImageAttachmentDto] | None = None
    documents: list[DocumentAttachmentDto] | None = None


class RunModelSettingsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    reasoning_effort: RunReasoningEffort | None = Field(None, alias='reasoningEffort')
    context_window: float | None = Field(
        None, alias='contextWindow', description='Selected model context window in tokens.', ge=1.0
    )


class SupplementalContextDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    text: str = Field(
        ...,
        description='Background context (e.g. Slack/Teams thread + channel history) to prepend to the system prompt.',
    )
    source: SupplementalContextSource = Field(
        ..., description='Producer that supplied the supplemental context.'
    )


class WorkflowActionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization the run belongs to. Omit for PAT/SDK callers — falls back to the authenticated principal's org.",
    )
    session_id: str = Field(
        ..., alias='sessionId', description='Client-generated session identifier.'
    )
    file_thread_id: str | None = Field(
        None, alias='fileThreadId', description='File thread ID for document-scoped execution.'
    )
    workflow_action: dict[str, Any] = Field(
        ...,
        alias='workflowAction',
        description='Workflow action descriptor: toolId, toolName, aiDescription, runtimeScope, and any action-specific parameters.',
    )
    previous_outputs: list[dict[str, Any]] | None = Field(
        None,
        alias='previousOutputs',
        description='Outputs from earlier steps in a multi-step workflow, forwarded to the action runtime.',
    )
    user_timezone: str | None = Field(
        None,
        alias='userTimezone',
        description='IANA time zone name for the executing user (e.g. "America/New_York").',
    )
    run_id: str | None = Field(
        None,
        alias='runId',
        description='Optional client-supplied run ID. Idempotency-Key header takes precedence.',
    )
    automation_id: str | None = Field(
        None, alias='automationId', description='Workflow id for usage attribution.'
    )
    source: WorkflowActionSource | None = Field(
        None, description='UI surface that triggered this action.'
    )


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
        description='Per-user share entries used for private-visibility scopes.',
        examples=[[]],
    )
    owner_user_id: str | None = Field(
        None,
        alias='ownerUserId',
        description='Clerk user id of the scope owner. Set on first write; cannot be changed by clients.',
        examples=['user_2abc'],
    )
    owner_email: str | None = Field(
        None,
        alias='ownerEmail',
        description='Lowercased email of the scope owner. Used by private-scope ACL when owner email matches.',
        examples=['alice@example.com'],
    )


class AgentDeployResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    workflow: WorkflowDto = Field(
        ...,
        description='The workflow after the deploy. `hasUnpublishedChanges` is false and `activeVariationId` matches the newly-published variation.',
    )
    deployed_at: str = Field(
        ...,
        alias='deployedAt',
        description='Server-side timestamp at which the deploy completed.',
        examples=['2026-05-11T10:00:00.000Z'],
    )


class AgentSelectionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    model: str | None = Field(None, description='Override model name for the orchestration step.')
    model_settings: ModelSettingsDto | None = Field(
        None,
        alias='modelSettings',
        description='Model-specific runtime controls such as reasoning effort and context window.',
    )
    agents: list[AgentSelectionEntryDto] = Field(
        ..., description='Ordered list of scopes to invoke. Must contain at least one entry.'
    )


class BatchCreateCustomContextItemsDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    items: list[CreateCustomContextItemDto] = Field(
        ...,
        description='Custom context items to upsert. Batch imports are idempotent by item hierarchy.',
    )


class BulkFinalizeResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    finalized: list[FileUploadResourceDto] = Field(
        ..., description='Resources for every upload that was finalized.'
    )
    failed: list[FailedFinalizeDto] = Field(
        ..., description='Per-item failures. Empty when every upload was finalized.'
    )


class BulkUploadFromUrlsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    uploaded: list[FileUploadResourceDto] = Field(
        ...,
        description='File upload resources for every URL that was fetched and landed successfully.',
    )
    failed: list[FailedUploadFromUrlDto] = Field(
        ..., description='Per-item failures. Empty when every URL succeeded.'
    )


class ConversationDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    thread_id: str = Field(
        ...,
        alias='threadId',
        description='Opaque thread/checkpoint id. It is not owned by a single scope; a conversation can span multiple workflows.',
        examples=['agent_42_abc-xyz'],
    )
    scope_id: float = Field(
        ...,
        alias='scopeId',
        description='Numeric scope id returned by the list/detail adapter. This is not conversation ownership.',
        examples=[42],
    )
    messages: list[ConversationMessageDto] = Field(
        ..., description='Conversation turns, in chronological order.'
    )
    message_window: ConversationMessageWindowDto | None = Field(
        None,
        alias='messageWindow',
        description='Present only when a bounded message window was requested and honored.',
    )
    created_at: str = Field(
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


class CreateAgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str = Field(
        ...,
        description='Display name for the workflow. Will be slugified into a URL-safe path.',
        examples=['Daily Sales Report'],
        max_length=200,
        min_length=1,
    )
    type: AgentType = Field(
        ...,
        description='Workflow type. Only `workflow` is supported; `task` is accepted as a deprecated alias and silently upgraded to `workflow`.',
        examples=['workflow'],
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description shown in the builder and workflow catalog.',
        examples=['Generates a daily sales report from CRM data.'],
    )
    trigger: TriggerDto | None = Field(
        None,
        description='Trigger configuration (schedule / webhook / api / slack / manual). Schedule shape is fully validated; other trigger types are opaque.',
    )
    agent_selection: AgentSelectionDto | None = Field(
        None,
        alias='agentSelection',
        description='Workflow selection (for task workflows): ordered scopes plus per-scope instructions.',
    )
    workflow_structure: WorkflowStructureDto | None = Field(
        None,
        alias='workflowStructure',
        description='Workflow graph (nodes + edges) when `type` is `workflow`. Unknown node/edge keys and out-of-enum node types are rejected with a 422.',
    )
    access_config: AgentAccessConfigDto | None = Field(
        None,
        alias='accessConfig',
        description='Access configuration. Omit to use the default (full-org shared with use + manage).',
    )


class CreateIngestedDataDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    integration_type: str = Field(
        ..., description='Canonical Modus integration identifier.', examples=['generic']
    )
    request: SqlIngestedDataRequestDto | HttpIngestedDataRequestDto = Field(
        ..., discriminator='type'
    )
    response: IngestedDataResponseDto


class CreateSkillDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str = Field(
        ...,
        description='Display name for the scope. Will be slugified into a URL-safe path.',
        examples=['Customer Churn Analyzer'],
        max_length=200,
        min_length=1,
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description shown in the builder and scope catalog.',
        examples=['Predicts churn risk for a customer given a 90-day usage window.'],
    )
    expected_output: str | None = Field(
        None,
        alias='expectedOutput',
        description='Optional summary of the expected output schema, used when supervising other scopes.',
        examples=['JSON: { churn_probability: number, drivers: string[] }'],
    )
    instructions: list[str] | None = Field(
        None,
        description='Ordered list of system-prompt instruction fragments. Joined at run time.',
        examples=[['You are a senior data analyst.', 'Always cite the SQL you used.']],
    )
    toolset: ToolsetDto | None = Field(
        None,
        description="Toolset configuration (tools this scope may invoke). Service sanitizes the shape on write. A connected integration given as `{actions, rules?}` is bound to the organization's newest workspace connection of that integration and returned as `{byConnection: {<connectionId>: {actions, rules?}}}`.",
    )
    model: str | None = Field(
        None,
        description='Model identifier to use at run time (e.g. `claude-sonnet-4-5`). Falls back to org default when absent.',
        examples=['claude-sonnet-4-5'],
    )
    model_settings: ModelSettingsDto | None = Field(
        None,
        alias='modelSettings',
        description='Model-specific runtime controls such as reasoning effort and context window.',
    )
    connection_set: list[dict[str, Any]] | None = Field(
        None,
        alias='connectionSet',
        description='List of integration connection refs available to this scope. Shape is integration-specific.',
        examples=[[]],
    )
    context_selections: list[dict[str, Any]] | None = Field(
        None,
        alias='contextSelections',
        description='Selected context items (sources / docs) the scope may read.',
        examples=[[]],
    )
    interfaces: list[dict[str, Any]] | None = Field(
        None,
        description='The scope\'s MCP interface configuration. Only entries with `type: "mcp"` are accepted; any other type is rejected with 400.',
        examples=[[]],
    )
    access_config: AccessConfigDto | None = Field(
        None,
        alias='accessConfig',
        description='Access configuration. Omit to use the default (full-org shared with use + manage).',
    )


class DashboardDefinitionDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    tiles: list[DashboardTileDto]
    filters: list[DashboardFilterDto]
    layout: dict[str, Any] | None = Field(
        None, description='Element positions and filter settings.'
    )


class DashboardDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: str
    context_item_id: str = Field(..., alias='contextItemId')
    title: str
    description: str
    access: DashboardAccessResponseDto
    definition: DashboardDefinitionDto
    view: DashboardView
    selected_version: DashboardSelectedVersionDto = Field(..., alias='selectedVersion')
    draft_revision: int = Field(
        ...,
        alias='draftRevision',
        description='Current draft revision; pass it as expectedRevision on the next write.',
    )
    active_version_id: str | None = Field(..., alias='activeVersionId')
    updated_by_user_id: str = Field(..., alias='updatedByUserId')
    created_at: str = Field(..., alias='createdAt', examples=['2026-09-16T10:00:00.000Z'])
    updated_at: str = Field(..., alias='updatedAt', examples=['2026-09-16T10:00:00.000Z'])
    pending_ownership_transfer: PendingOwnershipTransferDto | None = Field(
        ..., alias='pendingOwnershipTransfer'
    )
    can_use: bool = Field(..., alias='canUse')
    can_manage: bool = Field(..., alias='canManage')


class EvaluationConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    enabled: bool = Field(..., description='Whether scheduled evaluations are enabled')
    cadence: EvaluationCadenceDto | None = Field(None, description='Schedule cadence configuration')
    judge_model: str | None = Field(
        None,
        alias='judgeModel',
        description='Model ID for the judge LLM',
        examples=['openai/gpt-4o'],
    )
    judge_guidance: str | None = Field(
        None, alias='judgeGuidance', description='Custom guidance for the judge LLM'
    )
    notifications: EvaluationNotificationsDto = Field(
        ..., description='Regression notification settings'
    )


class ListAgentsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    workflows: list[WorkflowDto] = Field(
        ...,
        description='Page of workflows the caller can at least `use`. Workflows the caller cannot see are filtered out (not enumerated).',
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
    )


class ListDashboardsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    dashboards: list[DashboardDto] = Field(
        ...,
        description='Active view: published dashboards the caller can use. Draft view: dashboards the caller can manage. Each has its full definition; not paginated.',
    )


class ListMemberGroupsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    groups: list[MemberGroupDto]


class PublishDashboardResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    dashboard: DashboardDto = Field(
        ..., description='The dashboard in its active view after publishing.'
    )
    version: DashboardVersionDto = Field(..., description='The version that was just published.')


class ScopeDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    id: float = Field(
        ...,
        description='Numeric scope id (stable per-org; not reused after delete).',
        examples=[42],
    )
    slug: str = Field(
        ...,
        description='URL-safe slug used in human-readable links. Unique per org.',
        examples=['customer-churn-analyzer-a3f'],
    )
    name: str = Field(
        ...,
        description='Display name of the scope. Shown in the builder and in run logs.',
        examples=['Customer Churn Analyzer'],
    )
    description: str | None = Field(
        None,
        description='Optional one-paragraph description of what this scope does.',
        examples=['Predicts churn risk for a customer given a 90-day usage window.'],
    )
    status: ResourceLifecycleStatus = Field(
        ...,
        description='Lifecycle status. `draft` = never deployed. `active` = deployed. `deleted` = soft-deleted.',
        examples=['active'],
    )
    org_uuid: str = Field(
        ...,
        alias='orgUuid',
        description='Org UUID this scope belongs to. Matches the caller’s principal.',
        examples=['00000000-0000-0000-0000-000000000001'],
    )
    active_variation_id: str | None = Field(
        None,
        alias='activeVariationId',
        description='Active (deployed) variation id. Null until the scope is first deployed.',
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
        description='Access configuration — who in the org can use / manage this scope.',
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
    created_at: str = Field(
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
        description='Soft-delete timestamp. Null for active scopes.',
        examples=[None],
    )
    can_manage: bool = Field(
        ...,
        alias='canManage',
        description='Whether the requesting principal can manage (edit/delete/deploy) this scope. Derived server-side from the principal + accessConfig. Present on every Scope response.',
        examples=[True],
    )
    can_use: bool = Field(
        ...,
        alias='canUse',
        description='Whether the requesting principal can use (run, view history of) this scope. Derived server-side from the principal + accessConfig.',
        examples=[True],
    )
    manage_denial: ManageDenial | None = Field(
        ...,
        alias='manageDenial',
        description='Why `canManage` is false, for client-facing guidance: `needs_group_manage` (shared, but no group you belong to grants Manage) or `not_owner` (private, and you are not the owner). `null` when `canManage` is true.',
        examples=['needs_group_manage'],
    )


class UpdateAgentDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        None,
        description='New display name for the workflow.',
        examples=['Daily Sales Report v2'],
        max_length=200,
        min_length=1,
    )
    type: AgentType | None = Field(
        None, description='Updated workflow type. Rarely changed after creation.', examples=['task']
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
        None, alias='agentSelection', description='Updated workflow selection.'
    )
    workflow_structure: WorkflowStructureDto | None = Field(
        None,
        alias='workflowStructure',
        description='Updated workflow graph (nodes + edges). Unknown node/edge keys and out-of-enum node types are rejected with a 422.',
    )
    access_config: AgentAccessConfigDto | None = Field(
        None,
        alias='accessConfig',
        description='Updated access configuration. The service rejects changes that would lock the caller out of use + manage.',
    )
    disconnect_dashboard_alert: (
        bool | None
    ) = (
        Field(None, alias='disconnectDashboardAlert', description='Acknowledge that this change disconnects the workflow from its dashboard alert. Required when name, trigger or workflowStructure change on a workflow whose dashboardAlert is set.', examples=[True])
    )


class UpdateDashboardDraftDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    expected_revision: int = Field(
        ...,
        alias='expectedRevision',
        description='Draft revision the change is based on; a stale value is rejected with 409.',
        ge=1,
    )
    title: str | None = Field(None, description='New dashboard title.', max_length=500)
    description: str | None = Field(
        None, description='New dashboard description.', max_length=10000
    )
    definition: DashboardDefinitionDto = Field(
        ..., description='Replaces the whole draft definition.'
    )


class UpdateSkillDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    name: str | None = Field(
        None,
        description='New display name for the scope.',
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
        description='Updated expected-output summary, used when this scope is supervised.',
        examples=['JSON: { churn_probability: number }'],
    )
    instructions: list[str] | None = Field(
        None,
        description='Updated instruction fragments. Replaces the prior list when present.',
        examples=[['You are a senior data analyst.']],
    )
    toolset: ToolsetDto | None = Field(
        None,
        description="Updated toolset configuration. A connected integration given as `{actions, rules?}` is bound to the organization's newest workspace connection of that integration and returned as `{byConnection: {<connectionId>: {actions, rules?}}}`.",
    )
    model: str | None = Field(
        None,
        description='Updated model id. Pass `null` (explicit) to clear and use the org default.',
        examples=['claude-sonnet-4-5'],
    )
    model_settings: ModelSettingsDto | None = Field(
        None,
        alias='modelSettings',
        description='Updated model-specific runtime controls. Pass `null` to clear.',
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
        description='Updated context selections (sources / docs the scope may read).',
        examples=[[]],
    )
    interfaces: list[dict[str, Any]] | None = Field(
        None,
        description='Updated MCP interface configuration. Only entries with `type: "mcp"` are accepted; any other type is rejected with 400.',
        examples=[[]],
    )
    evaluations: list[dict[str, Any]] | None = Field(
        None,
        description='Updated evaluation entries (task + expected-output pairs) saved for the draft variation. Replaces the prior list when present.',
        examples=[[]],
    )
    supervision_subordinate_descriptions: dict[str, str] | None = Field(
        None,
        alias='supervisionSubordinateDescriptions',
        description='Map of subordinate scope id (stringified) to the manager-provided description blurb. Replaces the prior map when present.',
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
        description='Re-parent the scope under a new manager (or remove its current manager when null). When this field is present, all other fields are ignored.',
        examples=[17],
    )


class RunConfigDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    model: str | None = Field(None, description='Model id, e.g. anthropic/claude-sonnet-4.6.')
    model_settings: RunModelSettingsDto | None = Field(
        None, alias='modelSettings', description='Model-specific runtime controls.'
    )
    context_selections: list[dict[str, Any]] | None = Field(
        None, alias='contextSelections', description='Context selections (runtime-owned shape).'
    )
    connection_selections: list[dict[str, Any]] | None = Field(
        None,
        alias='connectionSelections',
        description='Database connection selections (runtime-owned shape).',
    )
    connection_set: list[dict[str, Any]] | None = Field(
        None, alias='connectionSet', description='Schema scopes (runtime-owned shape).'
    )
    connection_all_mode_ids: list[str] | None = Field(None, alias='connectionAllModeIds')
    guardrails: list[str] | None = Field(None, description='Guardrail ids applied to the run.')
    toolset: dict[str, Any] | None = Field(None, description='Map of tool name to tool config.')
    experimental_features: bool | None = Field(None, alias='experimentalFeatures')
    debug: bool | None = None
    composer_file_offload: bool | None = Field(
        None, alias='composerFileOffload', description='Set false to keep composer output inline.'
    )


class SkillRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(..., description='The user message to send.')
    session_id: str = Field(
        ...,
        alias='sessionId',
        description='Opaque client-generated conversation token for continuity. The server NEVER derives the run target identity (scope/workflow/modus) from this string — target identity comes only from the request path and DTO (see RunTarget). It is used solely to thread successive turns of the same conversation together.',
    )
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization id. Ignored for authenticated callers — the server uses the principal's org.",
    )
    version: Version | None = Field(
        None, description='Saved version to run (scope/workflow; ignored for Modus).'
    )
    file_thread_id: str | None = Field(
        None, alias='fileThreadId', description='Document-scoped conversation thread id.'
    )
    config: RunConfigDto | None = None
    attachments: AttachmentsDto | None = None
    user_context: UserContextDto | None = Field(None, alias='userContext')
    supplemental_context: SupplementalContextDto | None = Field(None, alias='supplementalContext')
    source: RunSource | None = Field(None, description='Origin of the run.')
    run_id: str | None = Field(
        None, alias='runId', description='Client-supplied run id (Idempotency-Key header wins).'
    )
    stream_protocol_version: StreamProtocolVersion | None = Field(
        None,
        alias='streamProtocolVersion',
        description='Streaming protocol version. Version 2 supports assistant-content replacement events.',
    )
    experimental_features: bool | None = Field(None, alias='experimentalFeatures')
    debug: bool | None = None
    subordinate_skill_ids: list[float] | None = Field(
        None,
        alias='subordinateSkillIds',
        description='Subordinate scope ids for an unsaved supervisor-scope draft test.',
    )


class CreateDashboardDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    title: str = Field(..., description='Dashboard title.', max_length=500, min_length=1)
    description: str | None = Field(None, description='Dashboard description.', max_length=10000)
    definition: DashboardDefinitionDto = Field(
        ..., description='Tiles, filters and layout of the draft. Element ids must be unique.'
    )
    access: DashboardAccessDto | None = Field(
        None, description='Who can use and manage the dashboard.'
    )


class DeployResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    scope: ScopeDto = Field(
        ...,
        description='The scope after the deploy. `hasUnpublishedChanges` is false and `activeVariationId` matches the newly-published variation.',
    )
    deployed_at: str = Field(
        ...,
        alias='deployedAt',
        description='Server-side timestamp at which the deploy completed.',
        examples=['2026-05-11T10:00:00.000Z'],
    )


class ListSkillsResponseDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    scopes: list[ScopeDto] = Field(
        ...,
        description='Page of scopes the caller can at least `use`. Scopes the caller cannot see are filtered out (not enumerated).',
    )
    next_page_token: str | None = Field(
        ...,
        alias='nextPageToken',
        description='Opaque token for the next page; `null` when this was the last page. Pass as `pageToken` on the next request.',
    )


class AgentRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(..., description='The user message to send.')
    session_id: str = Field(
        ...,
        alias='sessionId',
        description='Opaque client-generated conversation token for continuity. The server NEVER derives the run target identity (scope/workflow/modus) from this string — target identity comes only from the request path and DTO (see RunTarget). It is used solely to thread successive turns of the same conversation together.',
    )
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization id. Ignored for authenticated callers — the server uses the principal's org.",
    )
    version: Version | None = Field(
        None, description='Saved version to run (scope/workflow; ignored for Modus).'
    )
    file_thread_id: str | None = Field(
        None, alias='fileThreadId', description='Document-scoped conversation thread id.'
    )
    config: RunConfigDto | None = None
    attachments: AttachmentsDto | None = None
    user_context: UserContextDto | None = Field(None, alias='userContext')
    supplemental_context: SupplementalContextDto | None = Field(None, alias='supplementalContext')
    source: RunSource | None = Field(None, description='Origin of the run.')
    run_id: str | None = Field(
        None, alias='runId', description='Client-supplied run id (Idempotency-Key header wins).'
    )
    stream_protocol_version: StreamProtocolVersion | None = Field(
        None,
        alias='streamProtocolVersion',
        description='Streaming protocol version. Version 2 supports assistant-content replacement events.',
    )
    experimental_features: bool | None = Field(None, alias='experimentalFeatures')
    debug: bool | None = None


class FollowUpRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(..., description='The user message to send.')
    session_id: str = Field(
        ...,
        alias='sessionId',
        description='Opaque client-generated conversation token for continuity. The server NEVER derives the run target identity (scope/workflow/modus) from this string — target identity comes only from the request path and DTO (see RunTarget). It is used solely to thread successive turns of the same conversation together.',
    )
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization id. Ignored for authenticated callers — the server uses the principal's org.",
    )
    version: Version | None = Field(
        None, description='Saved version to run (scope/workflow; ignored for Modus).'
    )
    file_thread_id: str | None = Field(
        None, alias='fileThreadId', description='Document-scoped conversation thread id.'
    )
    config: RunConfigDto | None = None
    attachments: AttachmentsDto | None = None
    user_context: UserContextDto | None = Field(None, alias='userContext')
    supplemental_context: SupplementalContextDto | None = Field(None, alias='supplementalContext')
    source: RunSource | None = Field(None, description='Origin of the run.')
    run_id: str | None = Field(
        None, alias='runId', description='Client-supplied run id (Idempotency-Key header wins).'
    )
    stream_protocol_version: StreamProtocolVersion | None = Field(
        None,
        alias='streamProtocolVersion',
        description='Streaming protocol version. Version 2 supports assistant-content replacement events.',
    )
    experimental_features: bool | None = Field(None, alias='experimentalFeatures')
    debug: bool | None = None
    subordinate_skill_ids: list[float] | None = Field(
        None,
        alias='subordinateSkillIds',
        description='Saved scope ids to subordinate under this Modus run.',
    )


class InterruptRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization the run belongs to. Omit for PAT/SDK callers — falls back to the authenticated principal's org.",
    )
    last_seen_event_id: str | None = Field(
        None,
        alias='lastSeenEventId',
        description='Redis Stream id of the last SSE frame the client rendered (see CancelRunDto).',
    )
    next_run: FollowUpRunDto = Field(
        ..., alias='nextRun', description='Follow-up message that supersedes the current turn.'
    )


class ModusRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(..., description='The user message to send.')
    session_id: str = Field(
        ...,
        alias='sessionId',
        description='Opaque client-generated conversation token for continuity. The server NEVER derives the run target identity (scope/workflow/modus) from this string — target identity comes only from the request path and DTO (see RunTarget). It is used solely to thread successive turns of the same conversation together.',
    )
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization id. Ignored for authenticated callers — the server uses the principal's org.",
    )
    version: Version | None = Field(
        None, description='Saved version to run (scope/workflow; ignored for Modus).'
    )
    file_thread_id: str | None = Field(
        None, alias='fileThreadId', description='Document-scoped conversation thread id.'
    )
    config: RunConfigDto | None = None
    attachments: AttachmentsDto | None = None
    user_context: UserContextDto | None = Field(None, alias='userContext')
    supplemental_context: SupplementalContextDto | None = Field(None, alias='supplementalContext')
    source: RunSource | None = Field(None, description='Origin of the run.')
    run_id: str | None = Field(
        None, alias='runId', description='Client-supplied run id (Idempotency-Key header wins).'
    )
    stream_protocol_version: StreamProtocolVersion | None = Field(
        None,
        alias='streamProtocolVersion',
        description='Streaming protocol version. Version 2 supports assistant-content replacement events.',
    )
    experimental_features: bool | None = Field(None, alias='experimentalFeatures')
    debug: bool | None = None
    subordinate_skill_ids: list[float] | None = Field(
        None, alias='subordinateSkillIds', description='Saved scope ids to scope the Modus run to.'
    )


class ResumeRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    message: str = Field(..., description='The user message to send.')
    session_id: str = Field(
        ...,
        alias='sessionId',
        description='Opaque client-generated conversation token for continuity. The server NEVER derives the run target identity (scope/workflow/modus) from this string — target identity comes only from the request path and DTO (see RunTarget). It is used solely to thread successive turns of the same conversation together.',
    )
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization id. Ignored for authenticated callers — the server uses the principal's org.",
    )
    version: Version | None = Field(
        None, description='Saved version to run (scope/workflow; ignored for Modus).'
    )
    file_thread_id: str | None = Field(
        None, alias='fileThreadId', description='Document-scoped conversation thread id.'
    )
    config: RunConfigDto | None = None
    attachments: AttachmentsDto | None = None
    user_context: UserContextDto | None = Field(None, alias='userContext')
    supplemental_context: SupplementalContextDto | None = Field(None, alias='supplementalContext')
    source: RunSource | None = Field(None, description='Origin of the run.')
    run_id: str | None = Field(
        None, alias='runId', description='Client-supplied run id (Idempotency-Key header wins).'
    )
    stream_protocol_version: StreamProtocolVersion | None = Field(
        None,
        alias='streamProtocolVersion',
        description='Streaming protocol version. Version 2 supports assistant-content replacement events.',
    )
    experimental_features: bool | None = Field(None, alias='experimentalFeatures')
    debug: bool | None = None
    decision: Decision = Field(..., description='Decision that resumes the interrupted run.')


class EditQueuedRunDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")
    organization_id: str | None = Field(
        None,
        alias='organizationId',
        description="Organization the run belongs to. Omit for PAT/SDK callers — falls back to the authenticated principal's org.",
    )
    next_run: FollowUpRunDto = Field(
        ..., alias='nextRun', description='New payload replacing the queued run.'
    )
