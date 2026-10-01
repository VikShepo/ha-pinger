import asyncio
import importlib
from types import SimpleNamespace
import unittest

from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from support import model

notifications=importlib.import_module('pinger_under_test.notifications')
probe=importlib.import_module('pinger_under_test.probe')


class PushAndSwitchTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_web_outage_uses_same_service_and_payload_as_phone_test(self):
        now=1000;calls=[]
        async def service_call(domain,name,payload,*,blocking):calls.append((domain,name,payload,blocking))
        hass=SimpleNamespace(services=SimpleNamespace(has_service=lambda *args:True,async_call=service_call))
        service='notify.mobile_app_selected_phone'
        async def notify(*args):await notifications.send_mobile_push(hass,*args)
        await notify(service,'Network Control Center','Test erfolgreich.')
        async def ok(request):return web.Response(text='online')
        app=web.Application();app.router.add_get('/',ok)
        async with TestServer(app) as server,ClientSession() as session:
            async def checker(target,settings):return await probe.check_target(target,settings,session=session)
            monitor=model.Monitor(checker,notify,clock=lambda:now)
            monitor.configure({'notify_service':service,'offline_after_seconds':2,'attempts':1,'timeout_seconds':1})
            key=monitor.upsert({'name':'Webgerät','host':'127.0.0.1','method':'web','web_port':server.port,'notify':True})
            await monitor.run_due()
            await server.close()
            await monitor.run_due(force=True)
            self.assertEqual(monitor.snapshot()['targets'][0]['status'],'offline')
            now+=2
            await monitor.run_notifications_due()
            self.assertEqual(len(calls),2)
            self.assertEqual(calls[0][:2],calls[1][:2])
            self.assertEqual(calls[0][2]['data'],calls[1][2]['data'])
            self.assertTrue(calls[1][3])
            self.assertIn('2 Sekunden',calls[1][2]['message'])
            self.assertTrue(monitor.states[key]['outage_notified'])
            self.assertTrue(any(e['kind']=='push_attempt' for e in monitor.get_history(key)['log']))

    async def test_old_minutes_migrate_and_timer_retries_without_new_probe(self):
        now=1000;attempts=[];fail=True
        async def checker(*args):return {'online':False}
        async def notify(*args):
            attempts.append(now)
            if fail:raise ValueError('service unavailable')
        monitor=model.Monitor(checker,notify,clock=lambda:now)
        monitor.load({'settings':{'offline_after_minutes':2,'notify_service':'notify.mobile_app_phone'},'targets':[]})
        self.assertEqual(monitor.settings['offline_after_seconds'],120)
        key=monitor.upsert({'name':'Device','host':'127.0.0.1','notify':True})
        await monitor.run_due()
        now+=120
        await asyncio.gather(monitor.run_notifications_due(),monitor.run_notifications_due())
        self.assertEqual(len(attempts),1)
        fail=False;now+=29
        await monitor.run_notifications_due()
        self.assertEqual(len(attempts),1)
        now+=1;await monitor.run_notifications_due()
        self.assertEqual(len(attempts),2)
        self.assertEqual(monitor.states[key]['last_checked'],1000)

    async def test_network_switch_stops_old_jobs_and_does_not_alarm_inactive_network(self):
        calls=[];switches=[];pushes=[];now=1000
        async def checker(target,settings):calls.append(target['network_id']);return {'online':False}
        async def notify(*args):pushes.append(args)
        async def switch(network):switches.append(network)
        monitor=model.Monitor(checker,notify,clock=lambda:now,network_switcher=switch)
        monitor.networks={'office':{'name':'Office'}}
        monitor.configure({'notify_service':'notify.mobile_app_phone','offline_after_seconds':10})
        home=monitor.upsert({'name':'Home','host':'10.0.0.1','notify':True})
        remote=monitor.upsert({'name':'Remote','host':'10.0.0.1','network_id':'office','notify':True})
        await monitor.run_due()
        self.assertEqual(calls,[''])
        await monitor.select_network('office')
        now+=20;await monitor.run_notifications_due()
        self.assertEqual(pushes,[])
        await monitor.run_due()
        self.assertEqual(calls,['','office'])
        self.assertEqual(monitor.snapshot()['targets'][0]['status'],'paused')
        with self.assertRaises(ValueError):await monitor.run_due(force=True,target_id=home)
        started=asyncio.Event()
        async def slow(*args):started.set();await asyncio.sleep(100)
        monitor.checker=slow
        pending=asyncio.create_task(monitor.run_due(force=True,target_id=remote))
        await started.wait()
        await monitor.select_network('')
        with self.assertRaises(ValueError):await pending
        now+=20;await monitor.run_notifications_due()
        self.assertEqual(pushes,[])
        self.assertEqual(switches,['office',''])
        self.assertEqual(monitor.active_network,'')
        restored=model.Monitor(checker,notify);restored.load(monitor.dump())
        self.assertEqual(restored.active_network,'')
