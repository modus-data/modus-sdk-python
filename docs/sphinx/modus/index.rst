Modus
=====

Day-to-day client: read scopes, chat, browse context, stream workflow runs.

.. code-block:: python

   import modus

   client = modus.Modus(api_key="modus_xxx")
   for scope in client.scopes.list():
       print(scope.name)

Write operations use ``ModusManagement`` (Management section).

.. toctree::
   :maxdepth: 1
   :hidden:

   scopes
   workflows
   context
   connections
   chat
   suggestions

.. autoclass:: modus.Modus
   :members:
   :exclude-members: __init__, __enter__, __exit__, __repr__

.. autoclass:: modus.AsyncModus
   :members:
   :exclude-members: __init__, __aenter__, __aexit__, __repr__
