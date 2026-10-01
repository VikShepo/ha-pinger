import importlib.util
from pathlib import Path
import tempfile
import unittest

from support import root

spec=importlib.util.spec_from_file_location("installer",root/"install.py")
installer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_fresh_install_update_and_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            config=Path(temporary)
            (config/"configuration.yaml").write_text("default_config:\n",encoding="utf-8")
            (config/".storage").mkdir()
            (config/".storage"/"ha_pinger").write_text('{"important":"data"}',encoding="utf-8")
            target,backup=installer.install(config)
            self.assertIsNone(backup)
            self.assertTrue((target/"frontend"/"ha-pinger.js").exists())
            (target/"old_file.txt").write_text("previous version",encoding="utf-8")
            target,backup=installer.install(config)
            self.assertEqual((backup/"old_file.txt").read_text(),"previous version")
            self.assertFalse((target/"old_file.txt").exists())
            self.assertEqual((config/"configuration.yaml").read_text(),"default_config:\n")
            self.assertEqual((config/".storage"/"ha_pinger").read_text(),'{"important":"data"}')

    def test_refuses_wrong_directory_and_dry_run_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            config=Path(temporary)
            with self.assertRaises(ValueError):
                installer.install(config)
            (config/"configuration.yaml").write_text("",encoding="utf-8")
            installer.install(config,dry_run=True)
            self.assertFalse((config/"custom_components").exists())
