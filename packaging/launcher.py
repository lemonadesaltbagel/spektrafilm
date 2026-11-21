"""Entry point for the frozen (PyInstaller) spektrafilm desktop app.

Set ``SPEKTRAFILM_SMOKE_TEST=1`` to build the GUI, run one small simulation
and exit; CI uses this to check that a bundle actually starts. Output goes to
the file named by ``SPEKTRAFILM_SMOKE_LOG`` when it is set.
"""

import faulthandler
import multiprocessing
import os
import sys
import time
import traceback
from pathlib import Path

_START = time.monotonic()
SMOKE_TEST_TIMEOUT_S = 600


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


def _smoke_log(message: str) -> None:
    print(f'smoke test [{time.monotonic() - _START:6.1f}s]: {message}', flush=True)


def _smoke_test() -> int:
    # If anything hangs, dump every thread's stack and exit non-zero.
    faulthandler.dump_traceback_later(SMOKE_TEST_TIMEOUT_S, exit=True)

    import numpy as np
    import napari
    from qtpy import QtCore, QtWidgets

    from spektrafilm import init_params, simulate
    from spektrafilm_gui.app import create_app
    from spektrafilm_gui.napari_layout import show_viewer_window
    _smoke_log('imports done')

    # Same cheap settings as the test suite: this checks that the bundled
    # code, data and native libraries work, not the full pipeline.
    params = init_params(film_profile='kodak_portra_400', print_profile='kodak_portra_endura')
    params.debug.deactivate_spatial_effects = True
    params.debug.deactivate_stochastic_effects = True
    params.settings.use_enlarger_lut = False
    params.settings.use_scanner_lut = False
    image = np.full((16, 16, 3), 0.18, dtype=np.float64)
    result = simulate(image, params)
    if not np.all(np.isfinite(result)):
        _smoke_log('simulation produced non-finite values')
        return 1
    _smoke_log('simulation done')

    app = create_app()
    _smoke_log('GUI created')
    show_viewer_window(app.viewer)
    # The viewer lives inside spektrafilm's own main window, so closing the
    # viewer alone does not end the event loop; quit the application instead.
    QtCore.QTimer.singleShot(3000, QtWidgets.QApplication.instance().quit)
    napari.run()
    _smoke_log('OK')
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
