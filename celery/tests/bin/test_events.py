from __future__ import absolute_import

from nose import SkipTest
from mock import patch as mpatch

from celery.app import app_or_default
from celery.bin import events

from celery.tests.case import Case, _old_patch as patch


class MockCommand(object):
    executed = []

    def execute_from_commandline(self, **kwargs):
        self.executed.append(True)


def proctitle(prog, info=None):
    proctitle.last = (prog, info)
proctitle.last = ()


class test_events(Case):

    def setUp(self):
        self.app = app_or_default()
        self.ev = events.events(app=self.app)

    @patch('celery.events.dumper', 'evdump', lambda **kw: 'me dumper, you?')
    @patch('celery.bin.events', 'set_process_title', proctitle)
    def test_run_dump(self):
        self.assertEqual(self.ev.run(dump=True), 'me dumper, you?')
        self.assertIn('celery events:dump', proctitle.last[0])

    def test_run_top(self):
        try:
            import curses  # noqa
        except ImportError:
            raise SkipTest('curses monitor requires curses')

        @patch('celery.events.cursesmon', 'evtop', lambda **kw: 'me top, you?')
        @patch('celery.bin.events', 'set_process_title', proctitle)
        def _inner():
            self.assertEqual(self.ev.run(), 'me top, you?')
            self.assertIn('celery events:top', proctitle.last[0])
        return _inner()

    @patch('celery.events.snapshot', 'evcam', lambda *a, **k: (a, k))
    @patch('celery.bin.events', 'set_process_title', proctitle)
    def test_run_cam(self):
        a, kw = self.ev.run(camera='foo.bar.baz', logfile='logfile')
        self.assertEqual(a[0], 'foo.bar.baz')
        self.assertEqual(kw['freq'], 1.0)
        self.assertIsNone(kw['maxrate'])
        self.assertEqual(kw['loglevel'], 'INFO')
        self.assertEqual(kw['logfile'], 'logfile')
        self.assertIn('celery events:cam', proctitle.last[0])

    @mpatch('celery.events.snapshot.evcam')
    @mpatch('celery.bin.events.detached')
    def test_run_cam_detached(self, detached, evcam):
        self.ev.prog_name = 'celery events'
        self.ev.run_evcam('myapp.Camera', detach=True)
        self.assertTrue(detached.called)
        self.assertTrue(evcam.called)

    def test_get_options(self):
        self.assertTrue(self.ev.get_options())

    @patch('celery.bin.events', 'events', MockCommand)
    def test_main(self):
        MockCommand.executed = []
        events.main()
        self.assertTrue(MockCommand.executed)
