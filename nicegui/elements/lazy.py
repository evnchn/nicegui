from ..element import Element


class Lazy(Element, component='lazy.js'):
    """Lazy element that defers rendering of its children past the first browser paint.

    The surrounding UI can lay out and paint before the heavy child subtree is built,
    which is useful for tab panels and pages with many non-critical widgets.
    """
