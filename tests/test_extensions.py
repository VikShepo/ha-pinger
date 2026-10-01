import asyncio
import base64
import importlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from support import model

history = importlib.import_module('pinger_under_test.history')
media = importlib.import_module('pinger_under_test.media')
ranges = importlib.import_module('pinger_under_test.ranges')


def png(size=300):
    def chunk(kind, value):
        return struct.pack('>I',len(value))+kind+value+struct.pack('>I',zlib.crc32(kind+value)&0xffffffff)
    raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))
    raw+=chunk(b'IDAT',zlib.compress((b'\x00'+b'\x22\x88\xaa'*size)*size))+chunk(b'IEND',b'')
    return 'data:image/png;base64,'+base64.b64encode(raw).decode()


class ExtensionValidationTests(unittest.TestCase):
    def test_group_range_preview_checks_format_boundaries_and_members_without_mutation(self):
        monitor = model.Monitor(None, None)
        group = monitor.upsert_group({'name': 'LAN'})
        monitor.upsert({'name': 'Inside', 'host': '192.168.1.1', 'group_id': group})
        monitor.upsert({'name': 'Outside', 'host': '192.168.2.1', 'group_id': group})
        monitor.upsert({'name': 'Domain', 'host': 'device.example.org', 'kind': 'ddns', 'group_id': group})
        before = monitor.dump()
        info = monitor.preview_group_range({'ip_range': '192.168.1.12/24'}, group)
        self.assertEqual((info['range'], info['count'], info['first'], info['last']),
                         ('192.168.1.0/24', 254, '192.168.1.1', '192.168.1.254'))
        self.assertEqual(info['inside_count'], 1)
        self.assertEqual(info['outside'], [{'name': 'Outside', 'host': '192.168.2.1'}])
        self.assertEqual(monitor.dump(), before)
        self.assertEqual(ranges.describe_range('2001:db8::/126')['count'], 3)
        for value in ('192.168.1.256', '192.168.1.2-192.168.1.1', '::1-192.168.1.1', '192.168.1.0/33', '::/64', 'fe80::1%eth0'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                monitor.preview_group_range({'ip_range': value}, group)
        monitor.upsert_group({'ip_range': '192.168.1.12/24'}, group)
        self.assertEqual(monitor.groups[group]['ip_range'], '192.168.1.0/24')

    def test_group_range_persists_and_can_populate_without_changing_existing_entries(self):
        monitor = model.Monitor(None, None)
        self.assertEqual(model.validate_group({'name': 'Old group'})['ip_range'], '')
        group_id = monitor.upsert_group({'name': 'Office', 'ip_range': ' 192.168.1.0/30 '})
        restored = model.Monitor(None, None)
        restored.load(monitor.dump())
        self.assertEqual(restored.groups[group_id]['ip_range'], '192.168.1.0/30')
        self.assertEqual(restored.targets, {})
        result = restored.add_range({'range': restored.groups[group_id]['ip_range'], 'group_id': group_id})
        self.assertEqual(result['count'], 2)
        self.assertTrue(all(t['group_id'] == group_id for t in restored.targets.values()))
        for value in ('192.168.1.20-192.168.1.10', '::/0', 'invalid', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                restored.upsert_group({'ip_range': value}, group_id)
        self.assertEqual(restored.groups[group_id]['ip_range'], '192.168.1.0/30')
        restored.upsert_group({'ip_range': ''}, group_id)
        self.assertEqual(restored.groups[group_id]['ip_range'], '')
        self.assertEqual(len(restored.targets), 2)

    def test_ranges_are_bounded_and_ipv6_preserved(self):
        self.assertEqual(ranges.expand_range('192.168.1.20-192.168.1.22'),['192.168.1.20','192.168.1.21','192.168.1.22'])
        self.assertEqual(ranges.expand_range('192.168.1.0/30'),['192.168.1.1','192.168.1.2'])
        self.assertEqual(ranges.expand_range('::1-::2'),['::1','::2'])
        for value in ['0.0.0.0/0','::/0','192.168.1.10-192.168.1.1','192.168.1.1-::1']:
            with self.subTest(value=value),self.assertRaises(ValueError):ranges.expand_range(value)

    def test_bulk_add_atomic_and_duplicates_skipped(self):
        monitor=model.Monitor(None,None)
        monitor.upsert({'name':'Existing','host':'192.168.1.1'})
        fields={'name':'Office','range':'192.168.1.1-192.168.1.3'}
        result=monitor.add_range(fields,preview=True)
        self.assertEqual((result['count'],result['skipped']),(2,1))
        self.assertEqual(len(monitor.targets),1)
        monitor.add_range(fields)
        self.assertEqual(len(monitor.targets),3)
        with self.assertRaises(ValueError):monitor.add_range({'range':'192.168.2.0/24'})
        self.assertEqual(len(monitor.targets),3)
        with self.assertRaises(ValueError):monitor.add_range({'range':'192.168.3.1-192.168.3.2','network_id':'missing'})
        self.assertEqual(len(monitor.targets),3)

    def test_images_dimensions_integrity_and_path_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            store=media.ImageStore(folder)
            image_id=store.put(png())
            self.assertEqual(store.read(image_id),png())
            self.assertEqual(store.put(png()),image_id)
            for value in [png(299),'data:image/svg+xml;base64,PHN2Zz4=',png()[:-10]]:
                with self.assertRaises(ValueError):store.put(value)
            with self.assertRaises(ValueError):store.read('../secrets')
            store.remove(image_id)
            self.assertEqual(list(Path(folder).iterdir()),[])

    def test_history_retention_and_offline_not_overwritten(self):
        state={};now=40*86400+300
        history.record(state,now-31*86400,True)
        history.record(state,now,False)
        history.record(state,now+10,True)
        self.assertEqual(len(state['timeline']),1)
        self.assertEqual(state['timeline'][str(40*86400)][1],'3')
        history.record(state,now+20,None)
        self.assertEqual(state['timeline'][str(40*86400)][1],'7')


class ExtensionMonitorTests(unittest.IsolatedAsyncioTestCase):
    async def test_manual_checks_do_not_block_other_devices(self):
        slow_started,release=asyncio.Event(),asyncio.Event()
        calls=[]
        async def checker(target,settings):
            calls.append(target['host'])
            if target['host']=='192.168.1.1':slow_started.set();await release.wait()
            return {'online':True}
        monitor=model.Monitor(checker,None)
        first=monitor.upsert({'name':'Slow','host':'192.168.1.1'})
        second=monitor.upsert({'name':'Fast','host':'192.168.1.2'})
        job=asyncio.create_task(monitor.run_due(force=True,target_id=first))
        await slow_started.wait()
        self.assertTrue(await asyncio.wait_for(monitor.run_due(force=True,target_id=second),1))
        self.assertFalse(job.done())
        self.assertFalse(await monitor.run_due(force=True,target_id=first))
        release.set();await job
        self.assertEqual(len(calls),2)

    async def test_offline_continues_and_push_retry_is_visible(self):
        now=1000;calls=[];pushes=[];fail=True
        async def checker(target,settings):calls.append(now);return {'online':False}
        async def notify(*args):
            if fail:raise RuntimeError('offline push rejected')
            pushes.append(args)
        monitor=model.Monitor(checker,notify,clock=lambda:now)
        monitor.configure({'interval_minutes':10,'offline_after_minutes':1,'notify_service':'notify.mobile_app_phone'})
        key=monitor.upsert({'name':'Device','host':'192.168.1.1','notify':True})
        await monitor.run_due();now+=60;await monitor.run_notifications_due()
        self.assertIn('Push konnte',monitor.snapshot()['targets'][0]['notification_status'])
        self.assertEqual(monitor.states[key]['notification_next_attempt'],now+30)
        fail=False;now+=30;await monitor.run_notifications_due()
        self.assertEqual(len(pushes),1)
        now+=600;await monitor.run_due()
        self.assertEqual(len(calls),2);self.assertEqual(len(pushes),1)
        saved=monitor.get_history(key)
        self.assertTrue(saved['timeline']);self.assertTrue(saved['log'])
        monitor.clear_log(key)
        self.assertEqual(monitor.get_history(key)['log'],[])
        self.assertEqual(monitor.get_history(key)['timeline'],saved['timeline'])
        self.assertTrue(monitor.states[key]['outage_notified'])

    async def test_reenable_notifications_rearms_existing_outage(self):
        now=1000;pushes=[]
        async def checker(*args):return {'online':False}
        async def notifier(*args):pushes.append(args)
        monitor=model.Monitor(checker,notifier,clock=lambda:now)
        monitor.configure({'offline_after_minutes':0,'notify_service':'notify.mobile_app_phone'})
        key=monitor.upsert({'name':'Device','host':'192.168.1.1','notify':True})
        await monitor.run_due()
        monitor.upsert({'notify':False},key);monitor.upsert({'notify':True},key)
        await monitor.run_due()
        self.assertEqual(len(pushes),2)

    async def test_removed_pending_check_does_not_leave_spinner(self):
        monitor=model.Monitor(None,None)
        key=monitor.upsert({'name':'Device','host':'192.168.1.1'})
        jobs=monitor.start_due()
        monitor.remove(key)
        await asyncio.gather(*jobs)
        await asyncio.sleep(0)
        self.assertEqual(monitor.checking,set())

    async def test_pausing_and_rule_changes_preserve_device_history(self):
        async def checker(*args):return {'online':True}
        monitor=model.Monitor(checker,None)
        key=monitor.upsert({'name':'Device','host':'192.168.1.1'})
        await monitor.run_due()
        saved=monitor.get_history(key)
        for fields in ({'enabled':False},{'enabled':True},{'method':'both'}):
            monitor.upsert(fields,key)
            self.assertEqual(monitor.get_history(key)['timeline'],saved['timeline'])
            self.assertGreaterEqual(len(monitor.get_history(key)['log']),len(saved['log']))
        monitor.upsert({'host':'192.168.1.2'},key)
        self.assertEqual(monitor.get_history(key)['timeline'],{})
