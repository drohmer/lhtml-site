"""The parts of a talk (themes slides and slides-pdf): theme/template/part.html, the slide of a
part repeated by the deck with `part: true`, and theme/template/plan.html, the plan."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import yaml

REPO = Path(__file__).resolve().parents[1]


class PartsTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lhtml parts ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write('src/00_plan/index.html.j2', "= Plan\n\n{% include 'theme/template/plan.html' %}\n")
        self.write('src/00_part/index.html.j2', "{% include 'theme/template/part.html' %}\n")
        for name in ('01_a', '02_b', '03_c'):
            self.write(f'src/{name}/index.html.j2', f"= {name}\n")
        self.site = self.root / 'site'

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def build(self, slides, theme='slides'):
        (self.root / 'deck.yaml').write_text(yaml.safe_dump({'slides': slides}, allow_unicode=True))
        (self.root / 'config.yaml').write_text(yaml.safe_dump({
            'source_directory': 'src', 'site_directory': 'site', 'deck': 'deck.yaml',
            'theme': str(REPO / 'src/lhtml_site/themes' / theme), 'plugin': []}))
        result = subprocess.run([sys.executable, str(REPO / 'generate.py'), '-i', str(self.root / 'config.yaml')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def page(self, name):
        return (self.site / name).read_text(encoding='utf-8')

    DECK = [
        '00_plan',
        {'path': '00_part', 'title': '1. Introduction', 'part': True, 'subtitle': 'Context', 'summary': 'Short'},
        '01_a',
        {'path': '00_part', 'title': '2. Methods', 'part': True, 'color': '#123456'},
        '02_b',
        {'path': '00_part', 'title': 'Results', 'part': True, 'subtitle': 'What we found'},
        '03_c',
    ]

    def test_each_occurrence_shows_its_part_and_links_the_others(self):
        for theme in ('slides', 'slides-pdf'):
            with self.subTest(theme=theme):
                self.build(self.DECK, theme)
                first, second, third = (self.page(f'00_part/{f}') for f in ('index.html', 'index-2.html', 'index-3.html'))
                # its number, its title without the number written in the deck, its subtitle, its color
                self.assertIn('<div class="part-num">1</div>', first)
                self.assertIn('<div class="part-title">Introduction</div>', first)
                self.assertIn('<div class="part-sub">Context</div>', first)
                self.assertIn('<div class="part" style="--color-part:#4c72b0">', first)
                self.assertIn('<div class="part" style="--color-part:#123456">', second)
                self.assertNotIn('part-sub', second)
                # a title without a number is kept as it is
                self.assertIn('<div class="part-title">Results</div>', third)
                self.assertIn('<h1>1. Introduction</h1>', first)
                # the list of the parts: the current one marked, each a link to its occurrence
                for html, current in ((first, 1), (second, 2), (third, 3)):
                    marked = re.findall(r'<li class="on"[^>]*><a href="[^"]*"><span>(\d)</span>', html)
                    self.assertEqual(marked, [str(current)])
                    self.assertEqual(re.findall(r'<a href="([^"]*)"><span>', html),
                                     ['../00_part/index.html', '../00_part/index-2.html', '../00_part/index-3.html'])

    def test_the_plan_lists_the_parts(self):
        self.build(self.DECK)
        plan = self.page('00_plan/index.html')
        self.assertIn('<h1', plan)
        self.assertEqual(re.findall(r'class="part-plan-item" href="([^"]*)"', plan),
                         ['../00_part/index.html', '../00_part/index-2.html', '../00_part/index-3.html'])
        self.assertEqual(re.findall(r'<div class="part-plan-title">([^<]*)</div>', plan),
                         ['Introduction', 'Methods', 'Results'])
        # the summary of a part, else its subtitle, else nothing
        self.assertEqual(re.findall(r'<div class="part-plan-sub">([^<]*)</div>', plan), ['Short', 'What we found'])

    def test_a_page_that_is_no_part_shows_its_title(self):
        """The template included by a page the deck does not mark as a part: no number, no part marked."""
        self.build(['01_a', {'path': '00_part', 'title': 'Alone'}])
        html = self.page('00_part/index.html')
        self.assertIn('<div class="part-title">Alone</div>', html)
        self.assertNotIn('part-num', html)
        self.assertIn('<ol class="part-toc"></ol>', html)


if __name__ == '__main__':
    unittest.main()
