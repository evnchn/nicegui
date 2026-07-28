from __future__ import annotations

import functools
import hashlib
import importlib
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from . import core
from .helpers import hash_file_path
from .vbuild import VBuild
from .version import __version__

if TYPE_CHECKING:
    from .element import Element


@dataclass(kw_only=True, slots=True)
class Component:
    key: str
    name: str
    path: Path
    _keys: ClassVar[set[str]] = set()
    _names: ClassVar[set[str]] = set()

    def __post_init__(self) -> None:
        assert self.key not in self._keys, f'Duplicate key "{self.key}" for {self.__class__.__name__} {self.path}'
        assert self.name not in self._names, f'Duplicate name "{self.name}" for {self.__class__.__name__} {self.path}'
        self._keys.add(self.key)
        self._names.add(self.name)

    @property
    def tag(self) -> str:
        """The tag of the component."""
        return f'nicegui-{self.name}'


@dataclass(kw_only=True, slots=True)
class VueComponent(Component):
    html: str
    script: str
    style: str


@dataclass(kw_only=True, slots=True)
class JsComponent(Component):
    pass


@dataclass(kw_only=True, slots=True)
class Resource:
    key: str
    path: Path
    _keys: ClassVar[set[str]] = set()

    def __post_init__(self) -> None:
        assert self.key not in self._keys, f'Duplicate key "{self.key}" for {self.__class__.__name__} {self.path}'
        self._keys.add(self.key)


@dataclass(kw_only=True, slots=True)
class DynamicResource:
    name: str
    function: Callable


@dataclass(kw_only=True, slots=True)
class Import:
    name: str
    path: Path
    _names: ClassVar[set[str]] = set()

    def __post_init__(self) -> None:
        assert self.name not in self._names, f'Duplicate name "{self.name}" for {self.__class__.__name__} {self.path}'
        self._names.add(self.name)


@dataclass(kw_only=True, slots=True)
class Library(Import):
    key: str
    _keys: ClassVar[set[str]] = set()

    def __post_init__(self) -> None:
        assert self.key not in self._keys, f'Duplicate key "{self.key}" for {self.__class__.__name__} {self.path}'
        self._keys.add(self.key)


@dataclass(kw_only=True, slots=True)
class EsmModule(Import):
    pass


vue_components: dict[str, VueComponent] = {}
js_components: dict[str, JsComponent] = {}
libraries: dict[str, Library] = {}
resources: dict[str, Resource] = {}
dynamic_resources: dict[str, DynamicResource] = {}
esm_modules: dict[str, EsmModule] = {}
importmap_overrides: dict[str, str] = {}


def register_vue_component(path: Path, *, max_time: float | None) -> Component:
    """Register a .vue or .js Vue component.

    Single-file components (.vue) are built right away
    to delegate this "long" process to the bootstrap phase
    and to avoid building the component on every single request.
    """
    key = compute_key(path, max_time=max_time)
    name = _get_name(path)
    if path.suffix == '.vue':
        if key in vue_components and vue_components[key].path == path:
            return vue_components[key]
        v = VBuild(path)
        vue_components[key] = VueComponent(key=key, name=name, path=path, html=v.html, script=v.script, style=v.style)
        return vue_components[key]
    if path.suffix == '.js':
        if key in js_components and js_components[key].path == path:
            return js_components[key]
        js_components[key] = JsComponent(key=key, name=name, path=path)
        return js_components[key]
    raise ValueError(f'Unsupported component type "{path.suffix}"')


def register_library(path: Path, *, max_time: float | None) -> Library:
    """Register a *.js library."""
    key = compute_key(path, max_time=max_time)
    name = _get_name(path)
    if path.suffix in {'.js', '.mjs'}:
        if key in libraries and libraries[key].path == path:
            return libraries[key]
        libraries[key] = Library(key=key, name=name, path=path)
        return libraries[key]
    raise ValueError(f'Unsupported library type "{path.suffix}"')


def register_resource(path: Path, *, max_time: float | None) -> Resource:
    """Register a resource."""
    key = compute_key(path, max_time=max_time)
    if key in resources and resources[key].path == path:
        return resources[key]
    resources[key] = Resource(key=key, path=path)
    return resources[key]


def register_dynamic_resource(name: str, function: Callable) -> DynamicResource:
    """Register a dynamic resource which returns the result of a function."""
    dynamic_resources[name] = DynamicResource(name=name, function=function)
    return dynamic_resources[name]


def register_esm(name: str, path: Path, *, max_time: float | None) -> None:
    """Register an ESM module."""
    key = compute_key(path, max_time=max_time)
    if key in esm_modules:
        if esm_modules[key].name == name:
            return
        raise ValueError(f'Conflicting ESM registration for key "{key}": "{esm_modules[key].name}" vs "{name}"')
    esm_modules[key] = EsmModule(name=name, path=path)


def setup_esm_package(package_file: str, package_name: str, esm_name: str, exports: dict[str, str]) \
        -> tuple[Callable[[str], object], Callable[[], list[str]]]:
    """Register an ESM module and return ``__getattr__`` and ``__dir__`` for lazy class loading.

    Each ESM element package can use this in its ``__init__.py``:

        from ...dependencies import setup_esm_package
        __getattr__, __dir__ = setup_esm_package(__file__, __name__, 'nicegui-aggrid', {'AgGrid': '.aggrid'})
        __all__ = ['AgGrid']
    """
    dist = Path(package_file).parent / 'dist'
    register_esm(esm_name, dist, max_time=dist.stat().st_mtime)

    by_submodule: dict[str, list[str]] = {}
    for attr, submodule in exports.items():
        by_submodule.setdefault(submodule, []).append(attr)

    def __getattr__(name: str) -> object:
        if name not in exports:
            raise AttributeError(f'module {package_name!r} has no attribute {name!r}')
        submodule = exports[name]
        module = importlib.import_module(submodule, package=package_name)
        pkg = sys.modules[package_name]
        for attr in by_submodule[submodule]:
            setattr(pkg, attr, getattr(module, attr))
        return getattr(module, name)

    def __dir__() -> list[str]:
        return list(exports)

    return __getattr__, __dir__


def register_importmap_override(import_name: str, url: str) -> None:
    """Register an importmap override."""
    importmap_overrides[import_name] = url


_SPECIFIER_PATTERN = re.compile(
    r'''(?<![$\w.])(?P<head>(?:from|import)\s*(?:\(\s*)?)(?P<quote>['"])(?P<specifier>[^'"\n]+)(?P=quote)''')


# "vue" is missing here because its path depends on the prod_js config, which is not part of the resolver's cache key
_CORE_MODULE_PATHS = {
    'sass': 'static/sass.default.js',
    'immutable': 'static/immutable.es.js',
    'dompurify': 'static/dompurify.mjs',
}


def _core_module_paths() -> dict[str, str]:
    """Return the paths of the ESM modules NiceGUI itself ships, relative to ``/_nicegui/{version}/``."""
    prod = '.prod' if core.app.config.prod_js else ''
    return {'vue': f'static/vue.esm-browser{prod}.js', **_CORE_MODULE_PATHS}


def component_query() -> str:
    """Return a query string that changes whenever an importmap override changes the resolved component sources."""
    return f'?{hashlib.md5(str(sorted(importmap_overrides.items())).encode()).hexdigest()[:8]}' \
        if importmap_overrides else ''


def _resolve_specifier(specifier: str, up: str) -> str | None:
    """Resolve a bare module specifier to a URL relative to a component, or None if it is not registered."""
    if specifier in importmap_overrides:
        url = importmap_overrides[specifier]
        # a document-relative override would resolve differently inside a module, so leave those to the importmap
        return url if url.startswith(('/', 'http://', 'https://', '//')) else None
    if specifier in _CORE_MODULE_PATHS:
        return up + _CORE_MODULE_PATHS[specifier]
    for key, esm_module in esm_modules.items():
        if specifier == esm_module.name:
            return f'{up}esm/{key}/index.js'
        if specifier.startswith(esm_module.name + '/'):
            return f'{up}esm/{key}/{specifier[len(esm_module.name) + 1:]}'
    for key, library in libraries.items():
        if specifier == library.name:
            return f'{up}libraries/{key}'
    return None


def _component_source(key: str) -> str | None:
    """Return the JS of a registered component, or None if the key is unknown."""
    if key in js_components:
        return js_components[key].path.read_text(encoding='utf-8')
    if key in vue_components:
        return vue_components[key].script
    return None


def resolve_component_source(key: str) -> str | None:
    """Return the component's JS with bare module specifiers resolved to URLs, or None if there is nothing to resolve.

    This makes component modules self-contained, so that components loaded after the page has rendered
    (i.e. elements created dynamically over the websocket) do not depend on the page's importmap.
    """
    source = _component_source(key)
    if source is None:
        return None
    up = '../' * (key.count('/') + 1)

    def replace(match: re.Match) -> str:
        url = _resolve_specifier(match.group('specifier'), up)
        if url is None:
            return match.group(0)
        quote = match.group('quote')
        return match.group('head') + quote + url + quote

    resolved = _SPECIFIER_PATTERN.sub(replace, source)
    return resolved if resolved != source else None


@functools.cache
def compute_key(path: Path, *, max_time: float | None) -> str:
    """Compute a key for a given path using a hash function.

    If the path is relative to the NiceGUI base directory, the key is computed from the relative path.
    """
    NICEGUI_BASE = Path(__file__).parent
    try:
        rel_path = path.relative_to(NICEGUI_BASE)
    except ValueError:
        rel_path = path
    if path.is_file():
        return f'{hash_file_path(rel_path.parent, max_time=max_time)}/{path.name}'
    return hash_file_path(rel_path, max_time=max_time)


def _get_name(path: Path) -> str:
    return path.name.split('.', 1)[0]


def generate_resources(prefix: str, elements: Iterable[Element]) -> tuple[list[str],
                                                                          list[str],
                                                                          list[str],
                                                                          dict[str, str],
                                                                          list[str],
                                                                          list[str]]:
    """Generate the resources required by the elements to be sent to the client."""
    elements = list(elements)
    done_libraries: set[str] = set()
    done_components: set[str] = set()
    vue_scripts: list[str] = []
    vue_html: list[str] = []
    vue_styles: list[str] = []
    imports: dict[str, str] = {
        name: f'{prefix}/_nicegui/{__version__}/{path}' for name, path in _core_module_paths().items()
    }
    query = component_query()
    js_imports: list[str] = []
    js_imports_urls: list[str] = [imports['vue']]

    # build the importmap structure for libraries
    for key, library in libraries.items():
        if key not in done_libraries:
            imports[library.name] = f'{prefix}/_nicegui/{__version__}/libraries/{key}'
            done_libraries.add(key)

    # build the importmap structure for ESM modules
    for key, esm_module in esm_modules.items():
        imports[f'{esm_module.name}'] = f'{prefix}/_nicegui/{__version__}/esm/{key}/index.js'
        imports[f'{esm_module.name}/'] = f'{prefix}/_nicegui/{__version__}/esm/{key}/'

    # update the importmap with the overrides
    imports.update(importmap_overrides)

    # build the none-optimized component (i.e. the Vue component)
    for key, vue_component in vue_components.items():
        if key not in done_components:
            vue_html.append(vue_component.html)
            url = f'{prefix}/_nicegui/{__version__}/components/{vue_component.key}{query}'
            js_imports.append(f'import {{ default as {vue_component.name} }} from "{url}";')
            js_imports.append(f"{vue_component.name}.template = '#tpl-{vue_component.name}';")
            js_imports.append(f'app.component("{vue_component.tag}", {vue_component.name});')
            js_imports_urls.append(url)
            vue_styles.append(vue_component.style)
            done_components.add(key)

    # build the resources associated with the elements
    for element in elements:
        if element.component:
            js_component = element.component
            if js_component.key not in done_components and js_component.path.suffix.lower() == '.js':
                url = f'{prefix}/_nicegui/{__version__}/components/{js_component.key}{query}'
                js_imports.append(f'import {{ default as {js_component.name} }} from "{url}";')
                js_imports.append(f'app.component("{js_component.tag}", {js_component.name});')
                js_imports_urls.append(url)
                done_components.add(js_component.key)

    return vue_html, vue_styles, vue_scripts, imports, js_imports, js_imports_urls
