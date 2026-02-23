from pathlib import Path

from ...dependencies import register_esm

_dist_path = Path(__file__).parent / 'dist'
if _dist_path.exists():
    _max_time = max((p.stat().st_mtime for p in _dist_path.glob('*')), default=None)
    register_esm('nicegui-sortable', _dist_path, max_time=_max_time)
