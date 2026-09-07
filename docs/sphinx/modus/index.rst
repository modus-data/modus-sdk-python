Modus
=====

Day-to-day client: read scopes, chat, browse context, upload ingested data, and
stream workflow runs.

.. code-block:: python

   import modus

   client = modus.Modus(api_key="modus_xxx")
   for scope in client.scopes.list():
       print(scope.name)

Configuration write operations use ``ModusManagement`` (Management section).
Operational writes such as ``client.ingested_data.upload()`` stay on ``Modus``.

.. toctree::
   :maxdepth: 1
   :hidden:

   scopes
   workflows
   context
   connections
   chat
   suggestions
   ingested-data

.. autoclass:: modus.Modus
   :members:
   :exclude-members: __init__, __enter__, __exit__, __repr__

.. autoclass:: modus.AsyncModus
   :members:
   :exclude-members: __init__, __aenter__, __aexit__, __repr__
