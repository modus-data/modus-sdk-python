# Changelog

Published versions come from the `sdk-python/v*` tags; the current release is
whatever [PyPI](https://pypi.org/project/modus-sdk/) is serving. This file records
what changed, not which version is live.

Record concise, customer-visible release notes under `[Unreleased]` for every SDK
release, including pre-1.0 (`0.x`) releases.

## [Unreleased]

### Added

- **`context_suggestions` conversation source.** Filter conversation lists to discussions started from context suggestions.
- **`status_reason` on workflow run lists.** Each run in a workflow run list now carries the optional `status_reason` that run reads already had, so you no longer have to fetch each run to see it. It gains a value: `"agent_reported_issue"` marks a completed run in which a workflow step said it could not finish part of its task; `"approval_timeout"` is unchanged. The run is still `completed`.
- **`generated_description` on a scope.** Scope reads include `generated_description` (`str | None`), the summary written for the scope so a caller can choose it, sync and async. Null when none has been written.
- **Breaking (pre-1.0): `SupervisionView`.** `mgmt.scopes.supervision(id).get(view=...)` takes `SupervisionView` (`"active"` or `"draft"`), sync and async. `"published"` is not a supervision view. `VariationView` now also allows `"published"`, so a value typed as `VariationView` no longer type-checks there. Migration: type it as `SupervisionView`. Runtime values are unchanged.
- **`view="published"` on scope and workflow list and get.** Returns the published version you can use, sync and async. A scope or workflow that is only a draft, deleted, or that you can manage but not use is left out. For workflows it is also type workflow only; a task is left out. `active` and `draft` are unchanged.
- **`mgmt.scopes.apply_selection_ops()`.** Apply selection changes to a scope (sync and async). Pass `validate_only=True` to run the same checks and return the scope that would be saved, without writing. A preview result carries `validate_only=True`; a committed one does not, and every other field keeps its stored value, so a preview still needs a second call to save. Set a connection with `setConnectionPreferences` and remove it with `removeConnection`.
- **`claude-haiku-5.5` model.** Anthropic's Claude Haiku 5.5 is an accepted chat model id.
- **`gemini-3.8-flash` model.** Google's generally available Gemini 3.8 Flash is an accepted chat
  model id.
- **`mgmt.scopes.mcp_exposure_catalog(scope_id, request)`.** Lists the tools a scope can expose to MCP clients, sync and async. A field you send replaces the current draft for this call; a field you omit stays as stored. Nothing is saved. Rows you cannot access are left out, and stored selections on them are counted.
- **Run methods take the request models.** `runs.create` (`AgentRunCreateRequest`), `create_scope` (`SkillRunCreateRequest`), `create_modus` (`ModusRunCreateRequest`), `resume` (`ResumeRunRequest`), `cancel` (`CancelRunRequest`), `interrupt` and `edit_queued` (`FollowUpRunRequest`), and `workflow_actions.execute` (`WorkflowActionRequest`) and `cancel`, sync and async, send a model by its camelCase field names. A model used to be sent with its snake_case field names and `None` values, so a field such as `session_id` never reached the server as `sessionId`. A mapping still works as before.
- **Custom context item writes take the request models and return typed dicts.** `custom_items.create(CreateCustomContextItemDto(...))` and `update(uid, UpdateCustomContextItemDto(...))` take a model as well as keyword arguments (the keywords win), and `batch_create` and `create_relations` take models as well as dicts. The results are still dicts, now typed: `CreatedCustomContextItem` (`contextItemId`, `uid`, `contextType`, `dataPath`, `title`) and `UpdatedCustomContextItem` (`uid`). The models import from `modus.types.context`.
- **The `Typing :: Typed` classifier.** The package already shipped `py.typed`; its PyPI metadata now says so.
- **A trace id for every call.** Each request sends a W3C `traceparent` (a new trace per call, kept across its retries, each re-send also carrying `X-Modus-Retry-Attempt`), and every `ModusError` from an HTTP call carries it as `trace_id`, sync and async alike. Quote `trace_id` with `request_id` to support: it also names a call that never reached Modus. A `traceparent` you set in `default_headers` is sent as is.
- **`access` on file finalize and URL uploads.** `FinalizeUploadDto`, each `BulkFinalizeItemDto`, `UploadFromUrlDto` and each `BulkUploadFromUrlItemDto` take an optional `access` (visibility, group permissions, shared-with) that applies only when the file is first created; omitted, the file is shared with everyone with you as owner. A service-account token cannot set it.
- **Access on notes, saved queries, links and uploaded files.** `mgmt.context.items.update_access(uid, visibility=..., group_permissions=..., shared_with=...)` replaces who can view and manage one of these items; an item with no owner becomes yours. `ContextItem` reads of these types carry `access` and `can_manage`.
- **`client.workflows.chat()`.** Send a published workflow a message and stream its node output; `result()` returns the workflow's final output.
- **`AssistantContentResetEvent.sub_agent`** marks a correction to a sub-agent's output; a reset without it corrects the assistant's own reply.
- **Approvals on chat.** A run that stops for a write approval returns `result().approval`; `chat.resume(decision="approve" | "deny")` continues the same conversation.
- **Connection selection preferences on scopes.** A `connection_set` entry on create and update takes
  `preferences` (`mode` `all` or `manual`, `include` / `exclude` rules of id steps); reads return
  `preferences` on the connection's first row.
- **`deepseek-v4.1-flash-1017` model.** The October 17, 2026 snapshot of DeepSeek V4.1 Flash is an
  accepted chat model id.
- **Resume a dropped run stream.** Every run event carries `id`, its SSE event id, when the server sends one, and `runs.stream(run_id, last_event_id=...)` (sync and async) resumes after that event instead of replaying the run from the start.
- **`ErrorEvent.request_id`.** A run that fails after it started ends with an `ErrorEvent` that carries the id to quote to support; a chat stream raises `ModusError` with it as `request_id`.
- **Async scope evaluations.** `AsyncModusManagement().scopes.evaluations(id)` has the same methods as the sync client: `get_config`, `update_config`, `trigger_run`, `list_runs`, `get_run`, `add_case`, `update_case`, and `delete_case`.
- **`BadRequestError`** for HTTP 400 (a schema or parse failure), a `ModusError` subclass, so
  existing `except modus.ModusError` code is unaffected.
- **`ModusError.info`** carries the error envelope's structured detail, for example
  `info["missing"]` (the token scopes a 403 lacks) or `info["violations"]` on a 422.
- **`ModusError.retryable`** says whether the SDK's retry rule allowed re-sending the failed call.
- **`Retry-After` as an HTTP date, and `retry-after-ms`,** fill `RateLimitError.retry_after`.
- **An organization owner can give an ownerless scope an owner.** A scope created with a service-account token has no owner. `mgmt.scopes.request_ownership_transfer(id, new_owner_user_id=...)` by an organization owner now assigns one: naming yourself takes effect at once, naming another member waits for them to accept. `mgmt.scopes.cancel_ownership_transfer(id)` lets the organization owner withdraw that request.

### Removed

- **Breaking (pre-1.0): scope writes send a connection's selection only as `preferences`.** Each `connectionSet` entry `mgmt.scopes.create()` and `mgmt.scopes.update()` (sync and async) send is `{ connection_id, preferences, context_enabled? }`: `path` is removed from the request and `preferences` is required. An entry with `path` or without `preferences` is rejected with 400 and `info.reason` `legacy_entry`. `apply_selection_ops()` no longer takes `selectRoot`, `deselectRoot` or `setRootDeepRules`, nor their `path`, `includes` and `excludes` fields: set a connection with `setConnectionPreferences` and remove it with the new `removeConnection`. Reads still return one row per included path, with `path`, so turn a read into one entry per connection before you write it back.
- **Breaking MAJOR (CU-z93r0b8wwz): `Toolset.sql_runner` and SQL selectors.** Use
  `Toolset.sql("postgresql", connection_id="<Modus connection UUID>")` (or your SQL platform)
  to grant `query`; scope selections still control data access. Flat integration entries,
  action-string arrays, `sql_runner`, `looker_bi`, `langfuse_observability`, and `*_analytics`
  keys are no longer accepted by the API. No compatibility aliases are provided.

### Changed

- **Breaking (pre-1.0): MCP tool exposure keys name a connection (CU-z93r0b9hub).** In `mcpToolExposure.allowedIntegrationKeys`, `toolset:<connectionId>` exposes every tool granted on that connection, now and later, and never another connection's; `toolset_action:<platform>:<connectionId>:<action>` exposes one tool, a SQL connection's query tool included (`toolset_action:postgresql:<connectionId>:query`). `toolset:<platform>`, `data_connection:<connectionId>` and `data_connection_tool:` keys are retired: a stored `toolset:<platform>` key became the `toolset:<connectionId>` key of each connection the scope grants on that platform, a stored `data_connection:` key on a SQL connection became that connection's `toolset:<connectionId>`, and a retired key naming no such connection was removed, and a write adding one returns 422. `mcp_exposure_catalog` lists one row per connection, and `McpExposureFamily` no longer has `data_connection`.
- **Breaking MAJOR (CU-z93r0b8wwz): explicit integration connections.** `Toolset.integration`
  and every integration shortcut require `connection_id=` and produce
  `{platform: {byConnection: {connection_id: {actions, rules?}}}}`. Choose the Modus connection
  UUID yourself; the API no longer selects the newest workspace connection. Actions are operation
  names without connection/path suffixes, and rules apply only to that connection.
  `INTEGRATIONS` now includes every catalog platform key, including `looker`, `langfuse`,
  `amplitude`, `mixpanel` and `fireflies`, without aliases or suffixes.
- **Breaking (pre-1.0): the `access` body on note, saved-query and link creates is dashboard-shaped.** The generated `CreateNoteDto`, `CreateSavedQueryDto` and `CreateLinkDto` models now take `access` as `UpdateContextItemAccessDto` (`visibility`, `group_permissions`, `shared_with`, the body `mgmt.context.items.update_access` takes) instead of `AccessPolicyDto` (`scope`, `group_ids`, `user_ids`); the old shape is rejected with 400. Omitting `access` shares the item with everyone in the organization, with you as owner. `create_note`, `create_saved_query` and `create_link` send no `access` and are unchanged.
- **Context compose no longer fails at 30 seconds.** `scopes.get_context()` and `modus.get_context()` (sync and async) now call `POST /agent/v1/scopes/{id}/context` and `POST /agent/v1/modus/context` on the agent host, the host `chat()` uses. The old routes sat behind a 30-second gateway limit, so a slower compose came back as a bare 503 and was retried up to twice more while the first one was still running. Same arguments and result; a compose may now run for up to 90 seconds, and one still running then raises with `UPSTREAM_TIMEOUT` (504). Keep the read timeout above 90 seconds (the default is 300). The agent host is derived the same way as for chat: `agent_host` (or `MODUS_AGENT_HOST`), else from `base_url`; with a custom `base_url` and neither set, compose raises `ModusError` before sending anything, as chat does. If your network allows only the API host, allow the agent host too.
- **A resume with nothing to answer raises `ConflictError`.** `runs.resume` on a conversation with no write approval or connection request pending now fails with HTTP 409 (`code` `CONFLICT`) before any event, and the conversation stays usable. It used to yield one error event and leave every later turn on that conversation failing.
- **Breaking (pre-1.0): `workflows.runs.events(run_id)` returns the poll response.** The endpoint is the JSON long-poll transport, but the method expected a `text/event-stream` and always raised "expected text/event-stream, got application/json". It now returns a `RunEventsPoll` model (`events`, `cursor`, `status`, `done`), like the TypeScript SDK; each event has its stream `id` and `type`, and its other fields in `model_extra`. The async method is awaited, not iterated. Use `runs.stream(run_id)` for streamed events.
- **A refused run raises before any event.** When the agent host refuses a run (an empty turn, a scope you cannot see, a conflicting `Idempotency-Key`, a full conversation queue), `runs.create*` and `runs.resume` streams now raise the exception for the HTTP status (`NotFoundError`, `PermissionDeniedError`, `ConflictError`, `RateLimitError`, or `ModusError` with `status_code` 400) instead of yielding one `ErrorEvent`. No SDK code changed: the host now answers with the real status. An `ErrorEvent` still ends a run that fails after it started.
- **Breaking (pre-1.0): evaluation run timestamps are `datetime`.** `EvaluationRun.started_at` was a `str` and is now a timezone-aware `datetime`. `finished_at` is `datetime | None`. Replace string parsing with the value itself. Use this release with a Modus API that sends ISO 8601 evaluation timestamps; an older server's JavaScript date string fails validation.
- **Run request models carry the API-token message limit.** `message` on the run request models (`SkillRunDto`, `ModusRunDto`, `AgentRunDto`, `FollowUpRunDto`) has `max_length=32000`, the limit the server holds API tokens to, so a longer message fails validation before any request. `config.model` lists the models an API token may send.
- **Breaking (pre-1.0): scope `connectionSet` rows have one shape.** `scopes.create` and `scopes.update` accept each entry only as `{ connection_id, path, preferences?, context_enabled? }`, where `path` is an array of strings, `preferences` an object and `context_enabled` a boolean. An empty path selects the whole connection. Any other field, a non-string path segment or an empty or null `connection_id` is rejected with 400; a null `connectionSet` clears the list. `variation.connection_set` entries are now `ConnectionSetItemDto` models (`.connection_id`, `.path`, `.preferences`, `.context_enabled`); `row["connection_id"]` no longer works.
- **Breaking (pre-1.0): workflow `guardrails` removed.** `workflows.create` and `workflows.update` (sync and async) no longer take `guardrails=`. The workflow access configuration has no guardrails, so every call that set it failed with 400 and changed nothing. Scope `guardrails` are unchanged.
- **Breaking (pre-1.0): `scopes.memories(id).update()` returns `None`.** The server answers 204 with no body; the method raised a `ValidationError` after the update had been applied.
- **Breaking (pre-1.0): `manager_id` is an `int`.** `scopes.update(manager_id=...)` takes the numeric id of the manager scope. It was typed `str`, which the server rejects with 400. To detach, pass `update_mask="managerId"`.
- **Breaking (pre-1.0): evaluation runs `page_size` is checked.** `mgmt.scopes.evaluations(id).list_runs()` rejects a `page_size` outside 1..100 with 400, like every other list (it was clamped above 100).
- **Breaking (pre-1.0): a POST that fails after being sent now raises instead of being
  re-sent.** Retries depend on the method: GET, PUT, PATCH and DELETE retry 408, 429, 500, 502,
  503, 504, dropped connections and timeouts. A POST retries only on 429 or a connection that
  never opened (`ConnectError`, `ConnectTimeout`, `PoolTimeout`), except the POSTs that only
  read or set a state (context compose, item lookup, memory search, active-run lookup, run cancel, run interrupt, workflow-action cancel, workflow toggle, ingested-data upload), which retry like a GET. Before, a `scopes.create` that hit
  a gateway 504 or a read timeout was sent again and could create a second scope; now it raises
  and you decide whether to re-create.
- **A `Retry-After` over 60 s raises `RateLimitError` at once** (with `retry_after` set)
  instead of sleeping that long. Up to 60 s is still waited out.
- **Reading a workflow needs use or manage permission, not manage alone.** `mgmt.workflows.get(id)` returns a workflow you can run or change; `can_use` and `can_manage` say which. A workflow you cannot access is a 404 `NotFoundError` instead of a 403. `mgmt.workflows.interfaces(id).list()` still needs manage permission (403), and is a 404 when you cannot access the workflow.
- **Deploying a scheduled workflow with no owner is a 409.** `mgmt.workflows.deploy(id)` no longer reports an ownerless scheduled workflow as enabled when no schedule could be created.
- **A non-UUID interface id is a 400.** `mgmt.workflows.interfaces(id).update()` and `.delete()` with an id that is not a UUID return 400 instead of a retried 500.
- **Dashboard and element titles must contain a non-whitespace character.** A blank title on `mgmt.context.dashboards.create`, `.update_draft`, and `.elements(id).create` / `.update` returns 400.
- **Delete docs match the server.** Deleting a workflow or scope that is already deleted returns 404; deleting a memory that no longer exists returns 404 (it returned 422). Neither is a no-op.
- **Custom context item writes are documented as opt-in.** `custom_items` writes
  raise `PermissionDeniedError` ("Custom context item writes are not enabled")
  until Modus enables them for the organization.
- **Breaking (pre-1.0): `runs.interrupt` and `runs.edit_queued` take the turn to send.** `runs.interrupt(run_id, next_run, *, last_seen_event_id=None)` and `runs.edit_queued(run_id, next_run)` send `next_run` (`message` and `sessionId`, the run's conversation id) as `nextRun` and return the admitted run as `RunAdmission` (`run_id`, `status`), sync and async. For `interrupt`, that is the new run that carries the follow-up turn; stream it with `runs.stream(run_id)`. The old optional `body` defaulted to `{}`, which the server always rejected, and the methods returned `None`. `interrupt` sets `nextRun.runId` when you omit it, so a retried request returns the same run instead of starting a second turn. On a run that has already finished, `interrupt` starts a follow-up turn.
- **`runs.resume` requires `sessionId` and sends no message.** A missing or blank `sessionId` raises `ValidationError` before any request, as it does for `interrupt` and `edit_queued`; it was replaced by a random id, so the server answered "no longer pending". The documented example sends only `decision` and `sessionId`; a non-empty `message` is rejected by the server.
- **Breaking (pre-1.0): `chat()` streams from the agent host.** `client.scopes.chat()`, `client.modus.chat()` and `client.workflows.chat()` return a `ChatSession`. Iterate `text_stream` / `event_stream` for the reply as it arrives, or call `result()` for `ChatResult` (`content`, `thread_id`, `run_id`). On `AsyncModus`, `await client.scopes.chat(...)` returns the result as before; `chat()` itself is no longer a coroutine, so wrap it with `asyncio.ensure_future(...)` (not `create_task`) to run it as a task. The request is sent when you first iterate, call `result()` or `await` the session, not when `chat()` is called. Runs are no longer cut off after 30 seconds, and `content` is the server's final answer: interim narration and sub-agent output are left out. A session sends one request; iterating it again replays what arrived. A session that reaches `done` releases its connection; use the session as a context manager, or call `close()`, if you stop reading before then. Iterating `text_stream` after the run applies the server's mid-run corrections (`assistant_content_reset`), so the text matches what `content` was built from. **Migrate:** `client.scopes.chat(...).content` becomes `client.scopes.chat(...).result().content` (likewise `thread_id`, `run_id`, `approval`, and on `client.modus` / `client.workflows`); the old spelling raises an `AttributeError` that names the new one. Async code that awaits `chat()` keeps working unchanged.
- **Breaking (pre-1.0): numeric ids, counts and sizes are `int`.** Scope and workflow ids (`ScopeDto.id`, `WorkflowDto.id`, `agent_id`, `scope_id`, `manager_id`, supervision ids), counts (`total_count`, `message_count`, `original_count`, eval case counts, usage `call_count` / `input_tokens` / `output_tokens`), file sizes, indexes and page sizes were typed `float`, so ids printed as `34.0` and `mypy` rejected `client.scopes.get(scope.id)`. They are now `int`. The values on the wire are unchanged. Scores, averages, credits and canvas positions stay `float`. **Migrate:** code that relied on `isinstance(x, float)` or formatted ids as floats now gets `int`.
- **Workflow streams show their output.** Node tokens are unwrapped, `workflow_done` carries the workflow's final output, and a workflow that fails or is cancelled raises instead of ending the stream silently.
- **Breaking (pre-1.0): a custom `base_url` needs `agent_host` to chat.** When the agent host cannot be derived from `base_url` (anything other than `api.<env>.getmodus.com`), chat and runs raise instead of sending your key to the production agent host. Pass `agent_host` or set `MODUS_AGENT_HOST`; a blank value counts as unset.

### Removed

- **Breaking (pre-1.0): `chat_stream()`, `ChatStream`, `AsyncChatStream` and `get_final_result()`.** Use `chat()`, which streams; call `result()` instead of `get_final_result()`.
- **Breaking (pre-1.0): `version="draft"` on scope and workflow chat, and the `SkillChatRequestDto` / `SkillChatResponseDto` exports.** API tokens run published scopes only; `ChatResult` is the chat result type.

### Deprecated

- **`api-skill-<scopeId>-…` thread ids.** Continuing a conversation with the id an earlier `scopes.chat()` returned still works: the server reads it as the `agent_<scopeId>_…` thread it named. Store the `agent_<scopeId>_…` id the response now returns; the old form is accepted only by the chat continuation call and goes away with it.

### Fixed

- **A chat you stop reading at `done` closes its connection.** On some Python versions (3.12.3, for example) breaking out of `chat.event_stream` left the HTTP stream open until garbage collection; it now closes when the run finishes.
- **String enums print their value.** `print(scope.status)` and `str(scope.status)` give `active`, as the TypeScript SDK does, not `ResourceLifecycleStatus.active`. Comparison with `"active"` and `.value` are unchanged.
- **Python-version classifiers.** The package declares Python 3.10 to 3.14, matching `requires-python`, so PyPI lists the supported versions.
- **README.** The async example awaits the page before paging (`(await client.scopes.list()).auto_paging_iter()`); getting started follows every page; the `move` example moves the uploaded file into a folder; custom context item writes are documented as off until Modus enables them for your organization; it shows how to reach staging or a self-hosted API (`base_url` / `MODUS_BASE_URL`, `agent_host` / `MODUS_AGENT_HOST`); the error example handles a client-side `ValidationError`; tokens are shown as `modus_pat_…`; and the example scripts are said to live in the GitHub repository, not the wheel.
- **`mgmt.users.list_member_groups()` and `list_org_members()` no longer raise on a null.** `MemberGroupDto.description` and `OrgMemberDto.image_url` are `str | None`, as the API documents; a group with no description or a member with no image raised `ValidationError`.
- **Stream loops type-check.** Each run event's `type` is a `Literal` (`"token"`, `"done"`, …), so `if event.type == "token": event.content` narrows under mypy and pyright instead of reporting `"ErrorEvent" has no attribute "content"`.
- **`import modus` then `modus.management.ModusManagement()` type-checks**, as the docstrings write it.
- **`mgmt.workflows.create(name, "workflow")` type-checks.** `type` accepts `"workflow"` or `"task"` as well as `AgentType`; `update` accepts `"workflow"`.
- **`modus.context_item_label()` takes a `lookup()` row**, as the `lookup` docstring shows. An untitled row returns the fallback instead of raising `AttributeError`.
- **Server: `conversations.list(kind=...)` filters.** `kind="modus"` returns only Modus threads and `kind="scopes"` only scope threads; before, both returned every conversation.
- **Server: resuming a finished run ends at once.** `runs.stream(run_id, last_event_id=...)` with the id of the run's final `done`/`error`/`cancelled` event now ends with no events, instead of waiting forever.
- **Server: errors use Scope and Workflow.** A missing scope is `Scope not found` with `info["scopeId"]` (was `Skill not found`, `info["skillId"]`); a missing workflow is `Workflow not found` with `info["workflowId"]` (was `Agent not found`, `info["agentId"]`). Code that read the old key must read the new one.
- **`scopes.evaluations(id).update_config()` sends the API's field names.** It sent `judge_model`, `judge_guidance`, `time_of_day` and `clerk_user_id` in snake_case, which the API rejects with 400 ("property judge_model should not exist"); only `enabled` and `cadence.frequency` worked. Sync and async.
- **Completed evaluation runs could not be listed or read.** `mgmt.scopes.evaluations(id).list_runs()` and `.get_run(run_id)` raised `ValidationError` for any finished run, because `avg_score`, `finished_at` and the result fields `actual_output`, `passed`, `score`, `reasoning` and `was_passing_before` were typed as dicts. They are now `float`, `datetime`, `str` and `bool`, each optional. The server now sends evaluation timestamps as ISO 8601 (see Changed). An evaluation recipient's `name` is `str | None`.
- **A path id of `'..'` could target the parent resource, e.g. delete the scope.** `scopes.memories(7).delete('..')` sent `DELETE /scopes/7`. Every path id that is blank, `'.'` or `'..'` now raises `ValueError` before any request; a blank id no longer returns the list page as one item.
- **Paging no longer skips items.** `scopes.list()`, `workflows.list()`, `connections.list()` and their auto-paging iterators return every item: a page boundary no longer drops items created in the same millisecond, and `connections.list()` no longer drops a connection or ends early when other members' connections are hidden from you.
- **Numeric ids above 2147483647 return 404.** Such a scope or workflow id now raises `NotFoundError` instead of a 500 that was retried three times.
- **Evaluation runs page in a stable order.** Runs that started at the same time are no longer repeated or skipped across pages.
- **A run started while you page evaluation runs is not repeated.** The `list_runs` page token is now an opaque position in the list, not a row offset, so a run that starts between two pages no longer shows up again on the next page (and a deleted one no longer makes the next page skip a run). A numeric page token from before this release is rejected with 400 (`BadRequestError`); restart from the first page.
- **`update_config` returns what it stored.** The first `scopes.evaluations(id).update_config(UpdateEvaluationConfig(judge_model=...))` on a scope returned `judge_model=None` (and the defaults for every other field), although the value was saved; a later partial update could also turn `enabled` back off. The server now reads the configuration it just wrote.
- **`scopes.chat()` returns the conversation's thread id.** `thread_id` is now `agent_<scopeId>_…`, the id `scopes.conversations(id).list()` shows, so `get(thread_id)` accepts it. It was `api-skill-<scopeId>-…`, which those calls answered with 404.
- **`context.create_link()` on a page that cannot be read raises `UnprocessableError` (422), not a 500.** An unreachable or empty page names the URL in the message.
- **`update_mask` sends only what you set.** `scopes.update`, `workflows.update`, `context.items.update`, and `workflows.interfaces(id).update` sent `null` for every unset field whenever `update_mask` was given, and the server rejected the call with 400. The body now holds the fields you set, plus `null` for each field the mask names and you left unset, which the server clears.
- **`Toolset.empty()` clears a scope's tools.** `scopes.update(toolset=Toolset.empty())` sends `{}`; it was dropped, so the tools stayed.
- **`suggestions.list(scope_ids=[])` raises `modus.ValidationError`** before any request. It sent `scopeIds=`, which the server rejects with 400.
- **Clearing a masked field no longer fails with 500.** `scopes.update` with `update_mask` naming `description` or `expectedOutput` (or `workflows.update` naming `description`) and the field left unset raised `InternalServerError` after three tries. A cleared field now takes its empty value: text `''`; a list `[]`; a map `{}`; a context item's `userFeedback` `neutral`; and a memory's `metadata` `{}`. A field with no empty value raises `BadRequestError` saying it cannot be cleared. These are `name`, `accessConfig`, a workflow's `type` and `workflowStructure`, a context item's `content` and `contextType`, a memory's `memory`, and an interface's `name` and `config`.
- **Updating or deleting a memory that does not exist raises `NotFoundError`.** `scopes.memories(id).update()` and `.delete()` returned `None` as if they had succeeded when memory is off for the organization.
- **Docs: ids are numeric.** The getting-started example took a slug (`scopes.get("revenue-analysis")`), which the server rejects with 400; it now takes an id from `list()`. Docstrings no longer say "id or slug". `type="task"` is documented as a deprecated alias on create; `workflows.update` accepts only `"workflow"`.
- **Client-side argument errors are `ModusError`s.** An invalid id, path segment or other
  argument the SDK rejects before sending raises `modus.ValidationError`, which subclasses both
  `ModusError` and `ValueError`, so `except modus.ModusError` now catches it and existing
  `except ValueError` code keeps working.
- **Error messages are the API's message.** `ModusError.message` was the whole error envelope
  as a dict repr (`"{'code': 'NOT_FOUND', ...}"`); it is now the envelope's `message`.
  `code` and `request_id` were always `None`; they now come from the envelope (`request_id`
  falls back to the `x-request-id` header).
- **Every httpx transport error is an `APIConnectionError`.** `ReadError`, `WriteError`,
  `CloseError` (a reset keep-alive connection) and other `httpx.TransportError`s escaped as raw
  httpx exceptions and were never retried; they are now wrapped and retried for safe methods.
- **A 2xx response that is not JSON** raises a `ModusError` naming the status, content type and
  the first 200 characters, instead of a raw `JSONDecodeError`. An empty 200 on a GET returns
  `None` instead of raising.
- **`UnprocessableError` documentation:** 422 is a business-rule failure; schema failures are
  400 (`BadRequestError`).
- **Breaking (pre-1.0): `context.items.list_values` pages one item's array.** The
  server used to ignore the uid and return one row per item of the context type,
  with each item's whole `content`. It now reads only the item named by `uid`
  (`NotFoundError` when it is missing, unreadable, or of another context type) and
  pages the elements of the array at `content_key_path`. `ContextValueRow` has
  `index` (the element's 0-based position) and `value` (the element itself).
- **Conversation messages carry text.** `conversations.get` returns `content` as a
  string for every message, so a message stored as content blocks no longer fails
  validation; tool calls stay in `tool_calls`.
- **Oversized request bodies say so.** A request body over an operation's size
  limit fails with HTTP 413 and error code `PAYLOAD_TOO_LARGE` instead of
  `BAD_REQUEST`. Dashboards, a custom context item and a note now accept up to
  1 MiB, and `custom_items.batch_create` up to 8 MiB.

### Deprecated

- **`connection_set[].path`.** Send `preferences` instead; `path` is derived from it on reads.
- **`connection_set[].context_enabled`.** A scope always reads context from its connections; omit the field.
  `false` is accepted only when the connection is already stored with `false`.

## [0.9.0] — 2026-10-24

### Added

- **List selectable units.** `client.connections.list_selections(connection_id)` and
  `iter_selections(connection_id)` page the units a scope can select on a connection
  (`GET /connections/{id}/selections`). `client.connections.list()` items may include
  `selection_model`.
- **Evaluation case methods.** `mgmt.scopes.evaluations(id).add_case()`, `.update_case(case_id)`, and `.delete_case(case_id)` add, change, or remove one evaluation case. Omit `id` on add and the client assigns one, so a retry sends the same id. A retry whose id is already stored returns a conflict; an identical body is not treated as success. An empty `task` is allowed. An update with neither field is rejected.

### Changed

- **MCP config is checked on write.** Scope create, scope update, and `PATCH /scopes/{id}/mcp-config` return the effective core tools and tool exposure. A changed value must use true or false for each core tool, and version 1 with mode subset or discovery for tool exposure. A newly added exposure key must be one the scope can expose. A key already stored can be sent again or removed.
- **Breaking (pre-1.0): typed evaluation cases.** `PATCH /scopes/{id}` replaces `evaluations` with objects of `id` (optional), `task`, and `expectedOutput`. `task` and `expectedOutput` are required, and any other key, such as `createdAt` or `updatedAt`, is rejected with 400. Omit `id` on a new case and one is assigned. A repeated `id` is rejected. An empty `task` is allowed.
- **Breaking (pre-1.0): scope `interfaces` have one shape.** `scopes.create` and `scopes.update` (`POST /api/v1/scopes` and `PATCH /api/v1/scopes/{id}`) accept only MCP interface rows. `type` must be `mcp`. Each row has an optional id and name and a config of core tools and exposed integrations. A row without an id or name is assigned one. Responses return only id, type, name, and config; extra stored keys such as `enabled` are no longer returned.
- **Breaking (pre-1.0): workflow responses declare their shapes.** `Workflow.variation.trigger`, `workflow_structure`, and `agent_selection` are `WorkflowTriggerResponseDto`, `WorkflowStructureResponseDto`, and `AgentSelectionResponseDto` instead of dicts. Replace dict indexing with attribute access: `agent_selection["model"]` becomes `agent_selection.model`, and `trigger["schedule"]` becomes `trigger.schedule`. A non-schedule trigger has `schedule: null`, and a schedule leaves unused cadence fields null. A workflow interface `config` describes Slack and Teams (`accessMode`, `allowedEmails`, `availableChannelIds`) and an empty object for MCP.
- **Scope `connectionSet` rows must be a selectable unit.** `scopes.create` and `scopes.update` reject a new row whose path is neither the whole connection nor one selectable unit of it, with 422 `root.not_a_root`. A row already stored can stay, and removing it still succeeds.
- **Workflow interface config.** Slack and Teams `config` on a workflow interface is `accessMode` (`all`, `allow-list`, or `allow-org`), `allowedEmails`, and `availableChannelIds`. An MCP interface accepts no config keys. An unknown key or invalid value in a changed config returns 422 with violations; `config: null` returns 400. Unchanged stored values are accepted.
- **`search_query` documents word search.** `mgmt.context.custom_items.list(search_query=...)` (`GET /context/custom-items`) describes
  word search: it returns rows that contain every word of the query, case-insensitive.
- **Known toolset values are validated.** A new or edited scope `toolset` value must match that tool's shape.
  Most tools take an array of strings. `file_publish` takes `{ actions: string[], rules?: { nameMode: "any" | "restricted", allowedNames: string[] } }`.
  Coding tools take an array of `{ connectionUid, repoOwner, repoName, branch }`.
  `sql_runner` entries are `VERB:connectionId:`, optionally followed by `database:schema`, where `VERB` is `SELECT`, `INSERT`, `UPDATE`, `DELETE`, or `CREATE`.
  A value that does not match is `422`
  with rule `toolset.bad_value`; an unknown key stays `toolset.unknown_key`. Sending the same stored value again succeeds,
  including a historical value the new check would reject, and removing that value succeeds. The handwritten `Toolset` helpers are unchanged.

### Fixed

- **Workflow GET triggers and permission reasons.** `parse_trigger` accepts the trigger on a workflow response and still sends snake_case keys (`trigger_type`, `time_of_day`) on update. `Workflow.manage_denial` is again the string `not_owner`, `needs_group_manage`, or `null`.
- **Model settings survive a workflow update.** `AgentSelection` carries `model_settings`, and `parse_agent_selection` keeps it, so a selection read from a workflow and passed to `workflows.update(agent_selection=...)` no longer clears the stored `modelSettings`.

### Removed

- **`ToolsetDto` and `ToolsetToolDto`.** Scope create and update `toolset` is a map of tool key to its configuration. The generated `{ tools: [{ id, enabled, config }] }` models are gone. Unknown keys are rejected. The handwritten `Toolset` helpers are unchanged.
- **Breaking (pre-1.0): evaluation case timestamps.** Scope evaluation cases no longer include `createdAt` or `updatedAt`.

## [0.8.0] — 2026-10-18

### Removed

- **Breaking: evaluation Slack `nangoConnectionId`.** Send `connectionId`, the
  Slack connection's Modus UUID, in notification settings instead. Generated
  models expose `connection_id` (UUID) instead of `nango_connection_id`; JSON
  requests use `connectionId`. No deprecation window; requires a major release.

### Added

- **Service account tokens.** `api_key` accepts an organization-owned service account
  token (`modus_sat_<orgUuid>_<prefix>_<secret>`) as well as a personal access token.
- **`include_own_learnings` on `scopes.create`.** A new scope reads what is taught while
  using it by default; pass `False` to create it without its own learnings.
- **`default_headers` client option.** `Modus`, `AsyncModus`, `ModusManagement` and
  `AsyncModusManagement` accept headers to send on every request. They override the
  SDK's own defaults, except `Authorization`, which always comes from `api_key`.
- **`X-Modus-Client: sdk` request header.** Every request names the SDK as the client.
- **`gpt-6-luna` model.** The chat request `model` enum
  (`Model.gpt_6_luna`) accepts the new OpenAI model.
- **`gpt-5.6-luna` model.** The chat request `model` union accepts the new
  OpenAI model.
- **Move Files items.** `mgmt.context.items.move(uid, destination_folder_uid=...)`
  relocates a live file or folder. Pass `None` for the Files root.
- **Generic context item browse.** `client.context.items.list` and
  `mgmt.context.items.list` accept optional `connection_ids`, `parent_uids`,
  and `ancestor_uids` arrays. Omit a filter to leave it unrestricted; pass
  `[]` for the known-empty / match-none forms. Async twins match.
- **Upload destinations.** Sync and async upload helpers accept an optional
  `folder_path` prefix for single files, batches, and directories.

### Changed

- **Scope context file handling.** `scopes.get_context` returns bounded inline
  previews for large bodies; full file content is not available through this REST method.
- **Connected-integration toolset entries bind to a connection.** A scope toolset entry
  given as `{"actions": [...], "rules": ...}` (what `Toolset.integration` and its
  shortcuts build) is bound on create/update to the organization's newest workspace
  connection of that integration and returned as `{"byConnection": {<connection id>:
  {...}}}`. A create or update whose entry has no workspace connection to bind to
  returns `422`; re-sending an entry already stored unchanged is accepted.
- Deleting a Files folder through context items also deletes its contained files,
  subfolders, and parsed file items.

## [0.7.0] — 2026-09-30

### Added

- **Scope Slack/Teams interfaces.** `scopes.interfaces(scope_id)` lists, adds, updates and
  removes the Slack and Microsoft Teams interfaces of a scope (sync and async).
- **`claude-sonnet-5.5` model.** The chat request `model` enum
  (`Model.claude_sonnet_5_5`) accepts the new Anthropic model.
- **`deepseek-v4-pro`, `deepseek-v4-flash-latest`, and `kimi-k3` models.** The
  chat request `model` enum accepts these models.
- **Optional `ancestry` on context items.** List, get, lookup, and custom-item
  responses may include ordered ancestors (`uid`, `display_name`, `type`). The
  field is omitted on older responses, `null` when stored ancestry is unknown,
  and `[]` when the item has no ancestors.
- **`context_item_uids` on composed context.** `POST /modus/context` and
  `POST /scopes/{id}/context` now return the UIDs of the context items the composer
  kept, in selection order. Previously the response reported `selectedCount` with no
  way to learn which items it counted — `context_items` has been an empty array for
  some time and remains deprecated.
- **`claude-opus-5.5` and `grok-4.7` models.** The chat request `model` enum
  (`Model.claude_opus_5_5`, `Model.grok_4_7`) accepts the two new models.

### Removed

- **`RunConfigDto.strategies`.** The run API no longer publishes context-composer
  strategy IDs, so the generated `RunConfigDto` model no longer carries
  `strategies`. These IDs are the composer's internal vocabulary and get renamed,
  so a pinned value could silently stop doing anything. Strategy selection is
  chosen by the service.

### Added

- **Dashboard documents.** `mgmt.context.dashboards` document operations: list, get, create,
  update_draft, publish, delete, versions, draft snapshots, access, ownership transfer
  (`list()`, `get()`, `create()`, `update_draft()`, `publish()`, `delete()`,
  `list_versions()`, `get_version()`, `restore_version()`, `list_draft_snapshots()`,
  `update_access()`, `request_ownership_transfer()`, `accept_ownership_transfer()`,
  `cancel_ownership_transfer()`). New types `DashboardVersion`, `DashboardDraftSnapshot` and
  `DashboardPublishResult`; version definitions are returned as stored, so older versions
  may lack newer fields. Async twins are on `AsyncModusManagement`.

- **Dashboard draft elements and layout.** `mgmt.context.dashboards.elements(dashboard_id)`
  lists, reads, creates and updates the tiles and filters of a dashboard draft
  (`list()`, `get()`, `create()`, `update()`), and `mgmt.context.dashboards.update_layout()`
  moves or resizes several of them in one change. Every write takes the `expected_revision`
  it is based on and raises `ConflictError` when the draft changed. Async twins are on
  `AsyncModusManagement`.

- **Workflows linked to a dashboard alert.** Workflow responses carry `dashboard_alert`
  (`dashboard_id`, `tile_id`) when a dashboard KPI alert generated the workflow. Updating the
  name, trigger or workflow structure of such a workflow raises `ConflictError` unless the update
  sets `disconnect_dashboard_alert=True`, which disconnects it from the alert.

- Ingested-data uploads accept an optional source HTTP `response.status` from 100 through 599.

- **Ingested data uploads.** `Modus.ingested_data.upload` and
  `AsyncModus.ingested_data.upload` store raw SQL or HTTP request-response exchanges.
  Uploading identical content again raises `ConflictError`.

- **Conversation lists: optional `source` and `source_ref` filters.** `client.modus.conversations.list`
  and `client.scopes.conversations(scope_id).list` (both sync and async) now accept `source`
  to restrict results to one UI surface (e.g. `"context_chat"`, `"dashboard_copilot"`,
  `"dashboard_assistant"`, `"slack"`) and `source_ref` to narrow `source` to one instance of
  that surface — for `dashboard_copilot` and `dashboard_assistant`, a single dashboard id.
  `source_ref` requires `source`; sent on its own it is rejected with a 422. On the org-level
  list, `source` may only be combined with an omitted `kind` or `kind="all"` (not
  `kind="modus"` / `kind="scopes"`). Conversations recorded before the filter shipped carry
  no instance key and do not match it.

- **File uploads: optional `folder_path`.** `upload_from_url`, `finalize`, and directory
  uploads now accept an optional relative folder label that is stored with the file and
  returned on the file resource. `upload_dir` sets it automatically from each file's path
  relative to the upload root, so directory structure is preserved.

### Changed

- **Scope interfaces are MCP-only.** `management.scopes.create` and
  `management.scopes.update` accept only `interfaces` entries with `type: "mcp"`;
  any other type (for example `slack` or `teams`) is rejected with HTTP 400.
  Manage a scope's Slack and Teams interfaces with `scopes.interfaces(scope_id)`.

- **Scope MCP: Get Answer works alone.** `management.scopes.patch_mcp_config` now
  rejects a config that turns `core_tools.chat` (`get_answer`) on together with
  `getContext`, `teachModus` or any tool exposure, with HTTP 422. The call replaces the
  whole config and omitted keys take their defaults: `chat` off, `getContext` on,
  `teachModus` off, every tool exposed. To turn Get Answer on, send `chat: true`,
  `getContext: false` and an empty `subset` exposure in one call.

- `modus.get_context` and `scopes.get_context` now apply `limit` to composed
  context items, including normal Markdown responses. Omitting it remains unlimited.

- **Breaking (pre-1.0):** Ingested-data upload results now contain only `checksum`;
  object keys are internal storage details.

- **Breaking (pre-1.0):** Directory-managed member groups no longer include member IDs.
  Use the member count to determine their size. Native member groups are unchanged.

## [0.6.0] — 2026-08-15

### Changed

- Public OpenAPI updates from production release.

## [0.5.0] — 2026-08-08

### Changed

- Public OpenAPI updates from production release.

## [0.4.0] — 2026-08-01

### Changed

- Public OpenAPI updates from production release.

## [0.3.0] — 2026-07-26
