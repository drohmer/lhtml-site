"""lhtml-site doctor, and the helpers the build shares with it (lhtml_site/doctor.py)."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lhtml_site import doctor

REPO = Path(__file__).resolve().parents[1]


class InstallHintTest(unittest.TestCase):

    def test_after_pipx_a_python_package_is_injected_into_its_environment(self):
        with patch.object(doctor, 'installation', return_value='pipx'):
            self.assertEqual(doctor.install_hint('matplotlib numpy'), 'pipx inject lhtml-site matplotlib numpy')
            self.assertEqual(doctor.install_hint('ffpb', command=True), 'pipx inject --include-apps lhtml-site ffpb')

    def test_otherwise_it_goes_into_the_python_that_runs_the_generator(self):
        with patch.object(doctor, 'installation', return_value='pip'):
            self.assertEqual(doctor.install_hint('libsass'), f'{sys.executable} -m pip install libsass')

    def test_this_checkout_is_seen_as_one(self):
        self.assertEqual(doctor.installation(), 'checkout')

    def test_the_documents_give_the_commands_of_the_doctor_after_pipx(self):
        """pipx refuses `--include-apps` on a package without a command (pypdf):
        the reference and the example configuration inject each package as the
        doctor does."""
        package = REPO / 'src/lhtml_site'
        reference = ' '.join((package / 'docs/reference.md').read_text(encoding='utf-8').split())
        example = ' '.join(line.lstrip('# ') for line in
                           (package / 'configure_example.yaml').read_text(encoding='utf-8').splitlines())
        with patch.object(doctor, 'installation', return_value='pipx'):
            pdf = doctor.playwright_install_command().split(', then ') + [doctor.playwright_browser_command()]
            ffpb = doctor.install_hint('ffpb', command=True)
        self.assertNotIn('playwright pypdf', reference)
        for command in pdf:
            self.assertIn(f'`{command}`', reference)
        self.assertIn(ffpb, example)


class LookupTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_a_command_next_to_the_python_is_found_without_the_path(self):
        command = self.tmp / 'lhtml-test-command'
        command.write_text('#!/bin/sh\n')
        command.chmod(0o755)
        with patch.object(doctor.sys, 'executable', str(self.tmp / 'python')), \
                patch.dict(os.environ, {'PATH': os.devnull}):
            self.assertEqual(doctor.find_command('lhtml-test-command'), str(command))
            self.assertIsNone(doctor.find_command('lhtml-no-such-command'))


class CommandTest(unittest.TestCase):

    def run_doctor(self, env=None):
        return subprocess.run([sys.executable, str(REPO / 'generate.py'), 'doctor'], capture_output=True,
                              text=True, env=env, cwd=tempfile.gettempdir())

    def test_it_lists_every_feature_and_changes_nothing(self):
        result = self.run_doctor()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for feature in ('HTML pages and slides', 'PDF export', 'Layout report', 'Videos in several codecs',
                        'SASS', 'Figures in code', 'Code of other repositories'):
            self.assertIn(feature, result.stdout)

    def test_without_chromium_it_says_what_to_install_for_the_pdf_export_and_the_layout_report(self):
        env = {**os.environ, 'PLAYWRIGHT_BROWSERS_PATH': str(Path(tempfile.mkdtemp()) / 'none')}
        result = self.run_doctor(env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Node', result.stdout)
        self.assertNotIn('puppeteer', result.stdout)
        if importlib.util.find_spec('playwright') is None:
            self.assertRegex(result.stdout, r'Layout report .*: missing playwright, Chromium')
        else:
            self.assertRegex(result.stdout, r'Layout report .*: missing Chromium')
        self.assertRegex(result.stdout, r'missing  Chromium   -> .* -m playwright install --only-shell chromium')


if __name__ == '__main__':
    unittest.main()
