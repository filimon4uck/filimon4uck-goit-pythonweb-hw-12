.. Contacts API documentation master file, created by
   sphinx-quickstart on Tue Apr 15 22:11:35 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Contacts API documentation
==========================

Add your content using ``reStructuredText`` syntax. See the
`reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
documentation for details.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

REST API main
===================
.. automodule:: main
  :members:
  :undoc-members:
  :show-inheritance:

REST API routes
========================================
.. automodule:: src.routes.v1.auth
  :members:
  :undoc-members:
  :show-inheritance:
  
.. automodule:: src.routes.v1.contacts
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.routes.v1.users
  :members:
  :undoc-members:
  :show-inheritance:

REST API config
========================================
.. automodule:: src.conf.config
  :members:
  :undoc-members:
  :show-inheritance:

REST API utils
========================================
.. automodule:: src.utils.email_token
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.utils.get_services
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.utils.healthchecker
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.utils.reset_password_token
  :members:
  :undoc-members:
  :show-inheritance:

REST API services
========================================
.. automodule:: src.services.auth
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.services.contacts
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.services.email
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.services.upload_file
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.services.user
  :members:
  :undoc-members:
  :show-inheritance:

REST API repositories
==========================================================
.. automodule:: src.repositories.contacts_repository
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.repositories.user_repository
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.repositories.refresh_token_repository
  :members:
  :undoc-members:
  :show-inheritance:

REST API schemas
=====================================
.. automodule:: src.schemas.contact
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.schemas.email
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.schemas.password
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.schemas.token
  :members:
  :undoc-members:
  :show-inheritance:

.. automodule:: src.schemas.user
  :members:
  :undoc-members:
  :show-inheritance:


Indices and tables
=====================================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`