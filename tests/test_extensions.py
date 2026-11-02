"""The contract of an extension: content in, content out (lhtml_site/extensions.py)."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

REPO = Path(__file__).resolve().parents[1]


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='lhtml extensions ')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.write('src/a/index.html.j2', '= A\n\nbody of a\n')
        self.write('src/b/index.html.j2', '= B\n\nbody of b\n')

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def build(self, plugin, **options):
        self.write('ext.py', plugin)
        self.write('c.yaml', yaml.safe_dump({'source_directory': 'src', 'site_directory': 'site',
                                             'plugin': ['ext.py'], 'plugin_arg': options}))
        result = subprocess.run([sys.executable, str(REPO / 'generate.py'), '-i', 'c.yaml'],
                                cwd=self.root, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def html(self, name):
        return (self.root / 'site' / name / 'index.html').read_text()

    def test_each_stage_receives_the_page_and_returns_it(self):
        code, output = self.build(
            "seen = []\n"
            "def prepare(context):\n    seen.append(context.options['word'])\n"
            "def pre_process(text, context):\n    return text + '\\n**' + context.page['title'] + '**\\n'\n"
            "def mid_process(html, context):\n    return html.replace('body', seen[0])\n"
            "def post_process(html, context):\n    return html.replace('<strong>', '<strong class=\"x\">')\n",
            word='text')
        self.assertEqual(code, 0, output)
        self.assertIn('text of a', self.html('a'))
        self.assertIn('<strong class="x">B</strong>', self.html('b'))
        self.assertNotIn('**', (self.root / 'src/a/index.html.j2').read_text())     # the sources untouched

    def test_a_warning_names_the_page_and_a_failure_fails_it(self):
        code, output = self.build(
            "def mid_process(html, context):\n"
            "    if '= B' in html or 'body of b' in html:\n        raise ValueError('no b')\n"
            "    context.warning('look at a')\n    return html\n")
        self.assertEqual(code, 1, output)
        self.assertIn('src/a/index.html.j2: warning: ext.py: look at a', output)
        self.assertIn('src/b/index.html.j2: error: ext.py: mid_process: ValueError: no b', output)

    def test_a_page_an_extension_failed_leaves_the_build_and_keeps_its_previous_version(self):
        self.assertEqual(self.build("def pre_process(text, context):\n    return text\n")[0], 0)
        self.write('src/b/index.html.j2', '= B\n\nnew body of b\n')
        self.write('ext.py', "def pre_process(text, context):\n"
                             "    if 'new body' in text:\n        raise ValueError('no b')\n    return text\n"
                             "def mid_process(html, context):\n"
                             "    context.warning('mid sees ' + context.page['dir'])\n    return html\n")
        result = subprocess.run([sys.executable, str(REPO / 'generate.py'), '-i', 'c.yaml', '--only', 'b'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('error: ext.py: pre_process: ValueError: no b', result.stdout)
        self.assertNotIn('mid sees b/', result.stdout)                      # the later stages leave it out
        self.assertIn('body of b', self.html('b'))
        self.assertNotIn('new body', self.html('b'))                        # its previous version

    def test_a_prepare_that_fails_keeps_its_extension_away_from_the_pages(self):
        code, output = self.build("state = None\n"
                                  "def prepare(context):\n    raise RuntimeError('cannot prepare')\n"
                                  "def pre_process(text, context):\n    return state + text\n")
        self.assertEqual(code, 1)
        self.assertIn('c.yaml: error: ext.py: prepare: RuntimeError: cannot prepare', output)
        self.assertEqual(output.count('error: ext.py'), 1, output)

    def test_each_call_gets_its_own_options(self):
        code, output = self.build("def pre_process(text, context):\n"
                                  "    context.options['k'].append(1)\n"
                                  "    context.warning(str(context.options['k']))\n    return text\n", k=[0])
        self.assertEqual(code, 0, output)
        self.assertEqual(output.count('ext.py: [0, 1]'), 2, output)

    def test_a_stage_returns_the_text(self):
        code, output = self.build("def pre_process(text, context):\n    pass\n")
        self.assertEqual(code, 1)
        self.assertIn('pre_process returned NoneType, not the text of the page', output)

    def test_the_hooks_of_version_2_are_refused_by_name(self):
        for hook, reason in (("def pre_process(meta):\n    pass\n", 'takes meta'),
                             ("def pre_process(meta, log=None):\n    pass\n", 'takes meta'),
                             ("def mid_process(html):\n    pass\n", 'cannot be called with 2 argument(s)')):
            with self.subTest(hook=hook):
                code, output = self.build(hook)
                self.assertEqual(code, 1)
                self.assertIn(f'{reason}; an extension defines', ' '.join(output.split()))

    def test_any_signature_that_accepts_the_arguments_is_one(self):
        code, output = self.build("def pre_process(*args):\n    return args[0]\n"
                                  "def mid_process(html, context, *, strict=False):\n    return html\n")
        self.assertEqual(code, 0, output)

    def test_an_extension_that_cannot_be_imported_is_named(self):
        code, output = self.build("import os\nos.environ['NOT_SET_XYZ']\n")
        self.assertEqual(code, 1)
        self.assertIn("ext.py: KeyError: 'NOT_SET_XYZ'", output)

    def test_pre_include_and_code_include(self):
        self.write('macro.html', '{% macro hello() %}Hello{% endmacro %}')
        self.write('code/lib/f.hpp', 'int foo();\nint bar(int x);\n')
        self.write('src/a/index.html.j2', "= A\n{{ hello() }}\ncode::[c++]\n"
                                          "includeadv::{filepath:'lib/f.hpp', research:'bar'}\ncode::[-]\n"
                                          "code::[c++]\nincludeadv::{filepath:'lib/f.hpp'}\ncode::[-]\n")
        self.write('c.yaml', yaml.safe_dump({'source_directory': 'src', 'site_directory': 'site',
                                             'plugin': ['plugins/pre_include.py', 'plugins/code_include.py'],
                                             'plugin_arg': {'pre_include': ['macro.html']}}))
        result = subprocess.run([sys.executable, str(REPO / 'generate.py'), '-i', 'c.yaml'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        html = self.html('a')
        self.assertIn('Hello', html)
        self.assertEqual(html.count('bar'), 2)              # the line, then the whole file
        self.assertEqual(html.count('foo'), 1)
        self.assertNotIn('includeadv', html)


    def test_code_include_clones_each_repository_under_its_key(self):
        """`plugin_arg: includeadv: {course: <url>}`: the repository is cloned into
        code/course, whatever its name, and updated by the next build."""
        repository = self.root / 'repos/course-code'
        self.write('repos/course-code/f.hpp', 'int foo();\nint bar(int x);\n')
        for command in (['init', '-q'], ['add', '.'],
                        ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'f']):
            subprocess.run(['git'] + command, cwd=repository, check=True, capture_output=True)
        self.write('src/a/index.html.j2', "= A\ncode::[c++]\n"
                                          "includeadv::{filepath: 'course/f.hpp', research: 'bar'}\ncode::[-]\n")
        self.write('c.yaml', yaml.safe_dump({'source_directory': 'src', 'site_directory': 'site',
                                             'plugin': ['plugins/code_include.py'],
                                             'plugin_arg': {'includeadv': {'course': repository.as_uri()}}}))
        for build in ('clone', 'pull'):
            result = subprocess.run([sys.executable, str(REPO / 'generate.py'), '-i', 'c.yaml'],
                                    cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, build + ': ' + result.stdout + result.stderr)
            self.assertTrue((self.root / 'code/course/f.hpp').is_file())
            html = self.html('a')
            self.assertEqual(html.count('bar'), 1)          # the line found, highlighted
            self.assertNotIn('foo', html)
            self.assertNotIn('includeadv', html)
        self.assertFalse((self.root / 'code/course-code').exists())

if __name__ == '__main__':
    unittest.main()
