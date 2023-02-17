from __future__ import print_function

from . import tinybird


def pytest_addoption(parser):
    group = parser.getgroup('tinybird', 'reporting test results to tinybird')
    group.addoption(
        '--report-to-tinybird', default=False, action='store_true',
        help='send report to tinybird')


def pytest_configure(config):
    if not config.getoption("--report-to-tinybird"):
        return
    plugin = tinybird.TinybirdReport(config)
    config._tinybird = plugin
    config.pluginmanager.register(plugin)


def pytest_unconfigure(config):
    plugin = getattr(config, '_tinybird', None)
    if plugin is not None:
        del config._tinybird
        config.pluginmanager.unregister(plugin)
