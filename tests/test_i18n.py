import importlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

from support import model

i18n = importlib.import_module('pinger_under_test.i18n')
notifications = importlib.import_module('pinger_under_test.notifications')
frontend = Path(__file__).resolve().parents[1] / 'custom_components/ha_pinger/frontend'


class LanguageTests(unittest.TestCase):
    def test_existing_settings_migrate_and_selection_survives_restart(self):
        monitor = model.Monitor(None, None)
        monitor.load({'settings': {'interval_minutes': 5}, 'targets': []})
        self.assertEqual(monitor.settings['language'], 'auto')
        monitor.configure({'language': 'en'})
        saved = monitor.dump()
        restored = model.Monitor(None, None)
        restored.load(saved)
        self.assertEqual(restored.settings['language'], 'en')
        self.assertEqual(restored.targets, {})
        for value in ('fr', None, [], True):
            with self.assertRaises(ValueError):
                model.validate_settings({'language': value})

    def test_nested_messages_keep_user_names_and_addresses(self):
        name = 'Nicht erreichbar · Büro {name} <router>'
        message = f'{name} (192.168.1.1) ist nicht erreichbar. Seit 30 Sekunden keine erfolgreiche Prüfung. Ping: Keine Antwort · Web: Webdienst antwortet nicht.'
        self.assertEqual(i18n.translate_message(message, 'en-GB'),
                         f'{name} (192.168.1.1) is unreachable. No successful check for 30 seconds. Ping: No response · Web: Web service is not responding.')
        self.assertEqual(i18n.translate_message(message, 'de-DE'), message)
        self.assertEqual(i18n.translate_message('Ungültiger IP-Bereich: Ein Bereich darf höchstens 256 Adressen enthalten.', 'en'),
                         'Invalid IP range: A range can contain at most 256 addresses.')
        self.assertEqual(i18n.translate_message('Push-Aufruf an notify.mobile_app_phone: Nicht erreichbar · Büro', 'en'),
                         'Push request to notify.mobile_app_phone: Unreachable · Büro')
        self.assertEqual(i18n.translate_message('Unknown system error: EIO', 'en'), 'Unknown system error: EIO')

    def test_catalogs_keep_all_placeholders(self):
        for name in ('strings.en.json', 'messages.en.json'):
            catalog = json.loads((frontend / name).read_text(encoding='utf-8'))
            for source, target in catalog.items():
                self.assertEqual(set(re.findall(r'\{(\w+)\}', source)), set(re.findall(r'\{(\w+)\}', target)), source)
        self.assertEqual(i18n.language('de-CH'), 'de')
        self.assertEqual(i18n.language('en-US'), 'en')
        self.assertEqual(i18n.language('fr'), 'en')


class LocalizedPushTests(unittest.IsolatedAsyncioTestCase):
    async def test_phone_service_receives_localized_test_outage_recovery_and_dns(self):
        calls = []
        async def call(domain, name, payload, **kwargs):
            calls.append((domain, name, payload, kwargs))
        hass = SimpleNamespace(services=SimpleNamespace(has_service=lambda *args: True, async_call=call))
        cases = [
            ('Network Control Center', 'Test erfolgreich. Hier erhältst du deine Netzwerk-Meldungen.', 'Test successful.'),
            ('Nicht erreichbar · Büro', 'Büro (192.168.1.1) ist nicht erreichbar. Seit 2 Sekunden keine erfolgreiche Prüfung. Keine Antwort', 'Büro (192.168.1.1) is unreachable.'),
            ('Wieder erreichbar · Büro', 'Büro (192.168.1.1) ist wieder erreichbar.', 'Büro (192.168.1.1) is reachable again.'),
            ('DNS geändert · Büro', 'home.example.org zeigt jetzt auf 192.168.1.1.', 'home.example.org now resolves to 192.168.1.1.'),
        ]
        for title, message, expected in cases:
            await notifications.send_mobile_push(hass, 'notify.mobile_app_phone', title, message, locale='en')
            self.assertTrue(calls[-1][2]['message'].startswith(expected))
            self.assertEqual(calls[-1][0:2], ('notify', 'mobile_app_phone'))
            self.assertTrue(calls[-1][3]['blocking'])
        await notifications.send_mobile_push(hass, 'notify.mobile_app_phone', cases[1][0], cases[1][1], locale='de')
        self.assertEqual(calls[-1][2]['message'], cases[1][1])
