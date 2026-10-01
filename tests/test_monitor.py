import asyncio
import unittest

from support import model


class ValidationTests(unittest.TestCase):
    def test_web_fields_and_groups_are_validated(self):
        for fields in [{"web_scheme":"file"},{"web_port":0},{"web_port":True},
                       {"web_path":"//elsewhere.test/"},{"web_path":"/\r\nHost: x"},
                       {"web_path":"https://example.org"},{"web_path":"/x#fragment"},
                       {"verify_tls":"false"},{"availability_mode":"maybe"},{"group_id":[]}]:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                model.validate_target({"name":"Web","host":"192.168.1.1"}|fields)
        for fields in [{"name":" "},{"name":"x","icon":"<svg>"},{"name":"x","extra":True}]:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                model.validate_group(fields)

    def test_migrate_old_storage_and_persist_group_order(self):
        monitor=model.Monitor(None,None)
        monitor.load({"settings":dict(model.SETTINGS),"targets":[
            {"id":"old","name":"Existing","host":"192.168.1.1","favorite":True,"notify":True}],
            "states":{"old":{"history":[{"time":1,"online":True}],"outage_notified":True}}})
        self.assertEqual(monitor.targets["old"]["group_id"],"")
        self.assertTrue(monitor.targets["old"]["notify"])
        first=monitor.upsert_group({"name":"Büro","icon":"office"})
        second=monitor.upsert_group({"name":"Lager","icon":"storage"})
        monitor.upsert({"group_id":first},"old")
        other=monitor.upsert({"name":"Second","host":"192.168.1.2","group_id":first})
        monitor.move({"scope":"targets","direction":-1},other)
        monitor.move({"scope":"groups","direction":-1},second)
        restored=model.Monitor(None,None)
        restored.load(monitor.dump())
        self.assertEqual(list(restored.groups),[second,first])
        self.assertEqual(list(restored.targets),[other,"old"])
        self.assertEqual(restored.states["old"]["history"],[{"time":1,"online":True}])
        self.assertTrue(restored.states["old"]["outage_notified"])
        restored.remove_group(first)
        self.assertEqual(len(restored.targets),2)
        self.assertEqual(restored.targets["old"]["group_id"],"")
        self.assertEqual(len(restored.states["old"]["history"]),1)

    def test_order_respects_tab_and_group_and_rejects_stale_edits(self):
        monitor=model.Monitor(None,None)
        g=monitor.upsert_group({"name":"Network"})
        a=monitor.upsert({"name":"A","host":"192.168.1.1","group_id":g})
        ddns=monitor.upsert({"name":"Domain","host":"a.example.org","kind":"ddns","group_id":g})
        other=monitor.upsert({"name":"Other","host":"192.168.1.3"})
        b=monitor.upsert({"name":"B","host":"192.168.1.2","group_id":g})
        monitor.move({"scope":"targets","direction":-1},b)
        self.assertEqual(list(monitor.targets),[b,ddns,other,a])
        monitor.move({"scope":"targets","direction":-1},b)
        self.assertEqual(list(monitor.targets),[b,ddns,other,a])
        for scope,direction,item in [("targets",True,a),("targets",2,a),("targets",1,"gone"),("bad",1,a)]:
            with self.subTest(scope=scope,direction=direction),self.assertRaises(ValueError):
                monitor.move({"scope":scope,"direction":direction},item)
        with self.assertRaises(ValueError):
            monitor.upsert_group({"name":"network"})
        monitor.remove_group(g)
        with self.assertRaises(ValueError):
            monitor.upsert({"group_id":g},a)
        with self.assertRaises(ValueError):
            monitor.upsert_group({"name":"Changed"},g)

    def test_empty_installation_and_saved_addresses_survive_restart(self):
        monitor = model.Monitor(None, None)
        monitor.load(None)
        self.assertEqual(monitor.targets, {})
        self.assertEqual(monitor.groups, {})
        self.assertEqual(monitor.events, [])
        self.assertEqual(monitor.settings["interval_minutes"], 5)
        key=monitor.upsert({"name":"My router","host":"192.168.1.1"})
        restored=model.Monitor(None,None)
        restored.load(monitor.dump())
        self.assertEqual(restored.targets[key]["name"],"My router")
        monitor.remove(key)
        restored = model.Monitor(None, None)
        restored.load(monitor.dump())
        self.assertEqual(restored.targets, {})

    def test_reject_bad_hosts_and_unknown_fields(self):
        for host in ["", "192.168.1.999", "127.0.0.1; reboot", "https://host", "::1%eth0"]:
            with self.subTest(host=host), self.assertRaises(ValueError):
                model.validate_target({"name": "Test", "host": host})
        for host in ["https://home.example.org", "a..com", "a.b/path", "--.com", "1.2.3.4"]:
            with self.subTest(host=host), self.assertRaises(ValueError):
                model.validate_target({"name": "Test", "host": host, "kind": "ddns"})
        with self.assertRaises(ValueError):
            model.validate_target({"name": "Test", "host": "::1", "inject": True})

    def test_normalization(self):
        self.assertEqual(model.validate_target({"name":" Büro ","host":"BÜRO.Example.Org.","kind":"ddns"})["host"], "xn--bro-hoa.example.org")
        self.assertEqual(model.validate_target({"name":"v6","host":"2001:0db8::1"})["host"], "2001:db8::1")

    def test_strict_ranges_booleans_and_notify_services(self):
        for data in [{"interval_minutes":0}, {"interval_minutes":True}, {"attempts":6},
                     {"notify_service":"shell_command.run"}, {"notify_service":"notify.everyone"}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                model.validate_settings(data)
        for data in [{"port":65536},{"notify":"false"},{"favorite":1},{"interval_minutes":-1}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                model.validate_target({"name":"Test","host":"127.0.0.1"}|data)


class MonitorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now = 1000
        self.result = {"online":True,"latency_ms":2.1,"resolved_ips":["192.168.1.1"]}
        self.calls = []
        self.pushes = []
        self.fail_push = False

        async def checker(target, settings):
            self.calls.append((target["host"], self.now))
            return self.result.copy()

        async def notifier(service, title, message):
            if self.fail_push:
                raise RuntimeError("phone unavailable")
            self.pushes.append((service,title,message))

        self.monitor = model.Monitor(checker, notifier, clock=lambda:self.now)
        self.monitor.configure({"notify_service":"notify.mobile_app_phone"})
        self.key = self.monitor.upsert({"name":"Gateway","host":"192.168.1.1","notify":True})

    async def test_default_interval_and_override(self):
        await self.monitor.run_due()
        self.now += 299
        await self.monitor.run_due()
        self.assertEqual(len(self.calls),1)
        self.now += 1
        await self.monitor.run_due()
        self.assertEqual(len(self.calls),2)
        self.monitor.upsert({"interval_minutes":1},self.key)
        await self.monitor.run_due()
        self.now += 60
        await self.monitor.run_due()
        self.assertEqual(len(self.calls),4)

    async def test_single_manual_check_and_pause(self):
        second=self.monitor.upsert({"name":"Second","host":"192.168.1.2"})
        await self.monitor.run_due()
        self.calls.clear()
        self.now+=10
        await self.monitor.run_due(force=True,target_id=second)
        self.assertEqual(self.calls,[("192.168.1.2",self.now)])
        self.monitor.upsert({"enabled":False},second)
        with self.assertRaises(ValueError):
            await self.monitor.run_due(force=True,target_id=second)

    async def test_group_and_order_changes_preserve_running_probe(self):
        group=self.monitor.upsert_group({"name":"Büro","icon":"office"})
        other=self.monitor.upsert({"name":"Other","host":"192.168.1.2"})
        started,release=asyncio.Event(),asyncio.Event()
        async def checker(target,settings):
            started.set()
            await release.wait()
            return {"online":True,"checks":{"ping":{"online":False},"web":{"online":True}}}
        self.monitor.checker=checker
        job=asyncio.create_task(self.monitor.run_due(force=True,target_id=self.key))
        await started.wait()
        self.monitor.move({"scope":"targets","direction":-1},other)
        self.monitor.upsert({"group_id":group},self.key)
        self.monitor.remove_group(group)
        release.set()
        await job
        self.assertTrue(self.monitor.states[self.key]["online"])
        self.assertFalse(self.monitor.states[self.key]["checks"]["ping"]["online"])
        self.assertTrue(self.monitor.states[self.key]["checks"]["web"]["online"])

    async def test_single_outage_and_recovery(self):
        self.result["online"] = False
        await self.monitor.run_due()
        self.assertEqual(self.monitor.snapshot()["targets"][0]["status"], "offline")
        self.assertEqual(self.pushes,[])
        self.now += 300
        await self.monitor.run_due()
        self.assertEqual(len(self.pushes),1)
        self.now += 300
        await self.monitor.run_due()
        self.assertEqual(len(self.pushes),1)
        self.result["online"] = True
        self.now += 300
        await self.monitor.run_due()
        self.assertEqual(len(self.pushes),2)
        self.assertIn("Wieder erreichbar",self.pushes[-1][1])

    async def test_second_timer_sends_without_waiting_for_next_probe(self):
        self.monitor.configure({"offline_after_seconds":7})
        self.result["online"] = False
        await self.monitor.run_due()
        self.assertEqual(self.monitor.states[self.key]["next_check"],1300)
        self.now = 1006
        await self.monitor.run_notifications_due()
        self.assertEqual(self.pushes,[])
        self.now = 1007
        await self.monitor.run_notifications_due()
        self.assertEqual(len(self.pushes),1)
        self.assertEqual(len(self.calls),1)
        self.assertIn('7 Sekunden',self.pushes[0][2])

    async def test_no_false_alarm_if_recovers_before_threshold(self):
        self.result["online"] = False
        await self.monitor.run_due()
        self.now += 100
        self.result["online"] = True
        await self.monitor.run_due(force=True)
        self.now += 300
        await self.monitor.run_due()
        self.assertEqual(self.pushes,[])

    async def test_notification_failure_retries_and_is_visible(self):
        self.monitor.configure({"offline_after_minutes":0})
        self.fail_push=True
        self.result["online"]=False
        await self.monitor.run_due()
        self.assertFalse(self.monitor.states[self.key]["outage_notified"])
        self.assertIsNotNone(self.monitor.states[self.key]["notification_error"])
        self.fail_push=False
        self.now += 300
        await self.monitor.run_due()
        self.assertEqual(len(self.pushes),1)
        self.assertIsNone(self.monitor.states[self.key]["notification_error"])

    async def test_restart_keeps_outage_dedup_but_starts_unknown(self):
        self.monitor.configure({"offline_after_minutes":0})
        self.result["online"]=False
        await self.monitor.run_due()
        restored=model.Monitor(self.monitor.checker,self.monitor.notifier,clock=lambda:self.now)
        restored.load(self.monitor.dump())
        self.assertEqual(restored.snapshot()["targets"][0]["status"],"unknown")
        await restored.run_due()
        self.assertEqual(len(self.pushes),1)

    async def test_dns_change_order_independent_and_notification_opt_in(self):
        self.monitor.upsert({"kind":"ddns","host":"home.example.org","notify_dns":True},self.key)
        self.result["resolved_ips"]=["203.0.113.1","2001:db8::1"]
        await self.monitor.run_due()
        self.assertEqual(self.pushes,[])
        self.result["resolved_ips"].reverse()
        await self.monitor.run_due(force=True)
        self.assertEqual(self.pushes,[])
        self.result["resolved_ips"]=["203.0.113.2"]
        await self.monitor.run_due(force=True)
        self.assertEqual(len(self.pushes),1)
        self.assertIn("DNS geändert", self.pushes[0][1])
        await self.monitor.run_due(force=True)
        self.assertEqual(len(self.pushes),1)

    async def test_technical_errors_are_not_offline(self):
        self.monitor.configure({"offline_after_minutes":0})
        self.result={"online":None,"error":"No ICMP permissions"}
        await self.monitor.run_due()
        row=self.monitor.snapshot()["targets"][0]
        self.assertEqual(row["status"],"error")
        self.assertEqual(row["history"],[])
        self.assertEqual(self.pushes,[])

    async def test_delete_or_edit_during_check_discards_result(self):
        for delete in [True,False]:
            started,release=asyncio.Event(),asyncio.Event()
            key=self.monitor.upsert({"name":"Temporary","host":"192.168.1.200"})
            async def checker(target,settings):
                started.set()
                await release.wait()
                return {"online":True}
            self.monitor.checker=checker
            job=asyncio.create_task(self.monitor.run_due(force=True,target_id=key))
            await started.wait()
            if delete:
                self.monitor.remove(key)
            else:
                self.monitor.upsert({"host":"192.168.1.201"},key)
            release.set()
            await job
            if delete:
                self.assertNotIn(key,self.monitor.states)
            else:
                self.assertIsNone(self.monitor.states[key]["online"])

    async def test_overlap_is_coalesced(self):
        started,release=asyncio.Event(),asyncio.Event()
        async def checker(target,settings):
            started.set()
            await release.wait()
            return {"online":True}
        self.monitor.checker=checker
        job=asyncio.create_task(self.monitor.run_due())
        await started.wait()
        self.assertFalse(await self.monitor.run_due(force=True))
        release.set()
        self.assertTrue(await job)

    async def test_pause_and_notification_opt_out(self):
        self.monitor.upsert({"enabled":False},self.key)
        await self.monitor.run_due(force=True)
        self.assertEqual(self.calls,[])
        self.assertEqual(self.monitor.snapshot()["targets"][0]["status"],"paused")
        self.monitor.upsert({"enabled":True,"notify":False},self.key)
        self.monitor.configure({"offline_after_minutes":0})
        self.result["online"]=False
        await self.monitor.run_due()
        self.assertEqual(self.pushes,[])

    async def test_history_bounded_and_snapshot_detached(self):
        for i in range(60):
            self.now += 300
            self.result["online"] = i % 2 == 0
            await self.monitor.run_due()
        row=self.monitor.snapshot()["targets"][0]
        self.assertEqual(len(row["history"]),48)
        self.assertEqual(row["availability"],50)
        row["history"].clear()
        self.assertEqual(len(self.monitor.states[self.key]["history"]),48)

    async def test_duplicate_rejected_and_limit(self):
        with self.assertRaises(ValueError):
            self.monitor.upsert({"name":"Duplicate","host":"192.168.1.1"})
        self.monitor.upsert({"name":"TCP","host":"192.168.1.1","method":"tcp"})
        for i in range(model.MAX_TARGETS-2):
            self.monitor.upsert({"name":str(i),"host":f"10.0.{i//254}.{i%254+1}"})
        with self.assertRaises(ValueError):
            self.monitor.upsert({"name":"Too many","host":"10.1.1.1"})
