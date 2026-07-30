ModusManagement
===============

Create, update, and deploy scopes, workflows, and context.

.. code-block:: python

   from modus.management import ModusManagement

   mgmt = ModusManagement(api_key="modus_xxx")
   scope = mgmt.scopes.create(name="Analyst", model="gpt-4o")
   mgmt.scopes.deploy(scope.id)

.. toctree::
   :maxdepth: 1
   :hidden:

   scopes
   workflows
   context
   tools
   usage
   users

.. autoclass:: modus.management.ModusManagement
   :members:
   :exclude-members: __init__, __enter__, __exit__, __repr__

.. autoclass:: modus.management.AsyncModusManagement
   :members:
   :exclude-members: __init__, __aenter__, __aexit__, __repr__
