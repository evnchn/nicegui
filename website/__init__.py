"""NiceGUI documentation website package.

This ``__init__`` intentionally does not eagerly import submodules.
``main.py`` imports the submodules it needs explicitly, and eagerly
importing them here pulls in documentation modules that instantiate
``Client`` objects at module load time (to pre-render UI snippets).
Those ``Client`` objects schedule an ``Outbox.loop`` coroutine via
``background_tasks.create_or_defer``; when there is no running event
loop (e.g. during pytest collection of ``tests/test_seo.py``), the
coroutines are deferred to ``app.on_startup``, never awaited, and
eventually garbage-collected, producing ``RuntimeWarning`` entries
that break the ``unraisableexception`` plugin's setup hook for the
first test.
"""
