"""Entry point for the frozen (PyInstaller) spektrafilm desktop app.

Set ``SPEKTRAFILM_SMOKE_TEST=1`` to build the GUI, run one small simulation
and exit; CI uses this to check that a bundle actually starts. Output goes to
the file named by ``SPEKTRAFILM_SMOKE_LOG`` when it is set.
"""

import multiprocessing
import os
import sys
import traceback
from pathlib import Path


def _user_cache_dir() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Caches'
    else:
        base = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
    return base / 'spektrafilm'


def _configure_environment() -> None:
    # The bundle directory may be read-only (e.g. an .app in /Applications),
    # so keep numba's on-disk JIT cache in the user cache directory.
    os.environ.setdefault('NUMBA_CACHE_DIR', str(_user_cache_dir() / 'numba'))
    # Windowed bundles start with no stdout/stderr; libraries that print
    # (progress bars, warnings) would otherwise crash.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')


def _smoke_test() -> int:
    import numpy as np
    import napari
    from qtpy import QtCore

    from spektrafilm import init_params, simulate
    from spektrafilm_gui.app import create_app

    params = init_params(film_profile='kodak_portra_400', print_profile='kodak_portra_endura')
    image = np.full((32, 32, 3), 0.18, dtype=np.float64)
    result = simulate(image, params)
    if not np.all(np.isfinite(result)):
        print('smoke test: simulation produced non-finite values', flush=True)
        return 1

    app = create_app()
    QtCore.QTimer.singleShot(3000, app.viewer.close)
    napari.run()
    print('smoke test: OK', flush=True)
    return 0


def main() -> None:
    smoke_log = os.environ.get('SPEKTRAFILM_SMOKE_LOG')
    if smoke_log:
        # Windowed bundles have no console, so the smoke test reports to a file.
        sys.stdout = sys.stderr = open(smoke_log, 'w', buffering=1)
    _configure_environment()
    if os.environ.get('SPEKTRAFILM_SMOKE_TEST'):
        try:
            status = _smoke_test()
        except BaseException:
            # An uncaught exception would make the windowed bootloader show a
            # blocking error dialog instead of exiting.
            traceback.print_exc()
            status = 1
        # Skip interpreter teardown: background warmup threads would otherwise
        # keep the process alive after the window closes.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(status)

    from spektrafilm_gui.app import main as gui_main
    gui_main()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
