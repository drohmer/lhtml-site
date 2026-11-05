"""The keys of the slides reach the deck from a demo in an iframe.

A demo shown by demo:: takes the keyboard once it is clicked. The slides theme
(themes/slides/js/navigation.js) listens to the keys of its demos: the arrows and
Page Down / Page Up still change the slide, once, unless the demo keeps the key
(preventDefault) or a field of the demo has the focus. A demo of another site
posts {slide: {key}}. Real Chromium over HTTP (a page opened as a file has no
access to its frames): LHTML_BROWSER_TEST=1 python -m pytest tests/test_demo_navigation.py
"""
from pathlib import Path
import functools
import http.server
import os
import subprocess
import sys
import tempfile
import threading
import unittest

import yaml

REPO = Path(__file__).resolve().parents[1]

# The page of a demo: a field, a button, and a key kept for itself with ?keep=ArrowRight
DEMO = '''<!DOCTYPE html><html><head><meta charset="utf-8"><title>demo</title></head>
<body style="margin:0">
<button id="b">a button of the demo</button> <input id="field" value="text">
<script>
  const keep = new URLSearchParams(location.search).get('keep');
  window.addEventListener('keydown', (e) => { if (e.key === keep) e.preventDefault(); });
</script></body></html>'''

# The page of a demo of another site: it posts the key to the slide
REMOTE_DEMO = '''<!DOCTYPE html><html><head><meta charset="utf-8"><title>remote</title></head>
<body><button id="b">remote demo</button>
<script>
  window.addEventListener('keydown', (e) => { parent.postMessage({slide: {key: e.key}}, '*'); });
</script></body></html>'''


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(root):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@unittest.skipUnless(os.environ.get('LHTML_BROWSER_TEST') == '1', 'Set LHTML_BROWSER_TEST=1 for Chromium')
class DemoNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest('playwright')
        cls.temp = tempfile.TemporaryDirectory(prefix='lhtml-demo-keys-')
        root = Path(cls.temp.name).resolve()
        remote_root = root / 'remote'
        remote_root.mkdir()
        (remote_root / 'index.html').write_text(REMOTE_DEMO)
        cls.remote = serve(remote_root)
        remote_url = f'http://127.0.0.1:{cls.remote.server_address[1]}/index.html'

        # three slides; the first one shows a demo
        src = root / 'project/src'
        pages = {
            '01_a': "{% set layout = 'side' %}\n= Slide A\n\nText.\n\nmedia::\ndemo::assets/demo/index.html\n::\n",
            '02_b': '= Slide B\n',
            '03_c': '= Slide C\n',
        }
        for name, text in pages.items():
            (src / name).mkdir(parents=True)
            (src / name / 'index.html.j2').write_text(text)
        (src / '01_a/assets/demo').mkdir(parents=True)
        (src / '01_a/assets/demo/index.html').write_text(DEMO)
        config = root / 'project/configure.yaml'
        config.write_text(yaml.safe_dump({'source_directory': 'src', 'site_directory': 'out',
                                          'theme': str(REPO / 'src/lhtml_site/themes/slides')}))
        result = subprocess.run([sys.executable, str(REPO / 'generate.py'), '-i', str(config)],
                                cwd=root / 'project', capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        site = root / 'project/out'
        # the first slide again, with a demo of another site, next to it in the site
        first = (site / '01_a/index.html').read_text()
        (site / '01_a/remote.html').write_text(first.replace('assets/demo/index.html', remote_url))
        cls.server = serve(site)
        cls.base = f'http://127.0.0.1:{cls.server.server_address[1]}'
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.remote.shutdown()
        cls.temp.cleanup()

    def open_first(self, page='01_a/index.html'):
        tab = self.browser.new_page()
        errors = []
        tab.on('pageerror', lambda e: errors.append(str(e)))
        self.addCleanup(lambda: self.assertEqual(errors, []))
        self.addCleanup(tab.close)
        tab.goto(f'{self.base}/{page}', wait_until='load')
        tab.wait_for_function("document.querySelector('iframe.demo') && document.querySelector('#link-next a')")
        return tab

    def click_in_demo(self, tab, selector='#b'):
        tab.frame_locator('iframe.demo').locator(selector).click()

    def slide(self, tab):
        tab.wait_for_timeout(400)
        return tab.url.rsplit('/', 2)[-2]

    def test_the_arrow_in_the_slide_changes_the_slide(self):
        tab = self.open_first()
        tab.keyboard.press('ArrowRight')
        self.assertEqual(self.slide(tab), '02_b')

    def test_the_arrow_in_a_demo_changes_the_slide_once(self):
        tab = self.open_first()
        self.click_in_demo(tab)
        tab.keyboard.press('ArrowRight')
        self.assertEqual(self.slide(tab), '02_b')   # not 03_c: one step only

    def test_page_down_in_a_demo_changes_the_slide(self):
        """Page Down / Page Up are the keys of the remote controls of presentations."""
        tab = self.open_first()
        self.click_in_demo(tab)
        tab.keyboard.press('PageDown')
        self.assertEqual(self.slide(tab), '02_b')

    def test_page_down_in_the_slide_changes_the_slide(self):
        tab = self.open_first()
        tab.keyboard.press('PageDown')
        self.assertEqual(self.slide(tab), '02_b')

    def test_a_field_of_the_demo_keeps_the_arrows(self):
        tab = self.open_first()
        self.click_in_demo(tab, '#field')
        tab.keyboard.press('ArrowRight')
        self.assertEqual(self.slide(tab), '01_a')

    def test_a_demo_that_keeps_a_key_keeps_it(self):
        tab = self.open_first()
        tab.evaluate("document.querySelector('iframe.demo').src = 'assets/demo/index.html?keep=ArrowRight'")
        tab.wait_for_timeout(400)
        self.click_in_demo(tab)
        tab.keyboard.press('ArrowRight')
        self.assertEqual(self.slide(tab), '01_a')
        tab.keyboard.press('PageDown')                  # not kept by the demo
        self.assertEqual(self.slide(tab), '02_b')

    def test_a_demo_of_another_site_posts_its_keys(self):
        tab = self.open_first('01_a/remote.html')
        self.click_in_demo(tab)
        tab.keyboard.press('ArrowRight')
        self.assertEqual(self.slide(tab), '02_b')

    def test_a_message_from_the_page_itself_is_ignored(self):
        """Only the frames of the slide may change it by a message."""
        tab = self.open_first()
        tab.evaluate("window.postMessage({slide: {key: 'ArrowRight'}}, '*')")
        self.assertEqual(self.slide(tab), '01_a')


if __name__ == '__main__':
    unittest.main()
