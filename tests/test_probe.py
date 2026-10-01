import asyncio
import importlib
import socket
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

import aiohttp
from aiohttp import web
from support import model

# Only the ICMP library boundary is mocked; TCP tests use real loopback sockets.
icmp=types.ModuleType("icmplib")
icmp.ICMPLibError=type("ICMPLibError",(Exception,),{})
icmp.SocketPermissionError=type("SocketPermissionError",(icmp.ICMPLibError,),{})
icmp.async_ping=AsyncMock()
with patch.dict(sys.modules,{"icmplib":icmp}):
    probe=importlib.import_module("pinger_under_test.probe")


class ProbeTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_responses_including_login_errors_and_redirects(self):
        paths=[]
        async def reply(request):
            paths.append(str(request.rel_url))
            self.assertEqual(request.method,"GET")
            return web.Response(status=int(request.match_info["status"]),
                                headers={"Location":"http://invalid.example.org/"},text="fixture")
        app=web.Application()
        app.router.add_get("/{status}",reply)
        runner=web.AppRunner(app)
        await runner.setup()
        site=web.TCPSite(runner,"127.0.0.1",0)
        await site.start()
        port=site._server.sockets[0].getsockname()[1]
        try:
            for status in [200,302,401,403,404,500]:
                with self.subTest(status=status),patch.object(probe,"async_ping",AsyncMock()) as ping:
                    result=await probe.check_target({"host":"127.0.0.1","method":"web",
                        "web_port":port,"web_path":f"/{status}?test=1"},model.SETTINGS)
                    self.assertTrue(result["online"])
                    self.assertEqual(result["checks"]["web"]["http_status"],status)
                    ping.assert_not_awaited()
                    self.assertEqual(paths[-1],f"/{status}?test=1")
                    self.assertEqual(result["resolved_ips"],["127.0.0.1"])
            # Real HTTP response plus a nonresponding ICMP device: this is the
            # user's case, and must keep both independent outcomes visible.
            with patch.object(probe,"async_ping",AsyncMock(return_value=types.SimpleNamespace(is_alive=False,avg_rtt=0))):
                target={"host":"127.0.0.1","method":"both","web_port":port,"web_path":"/200"}
                result=await probe.check_target(target,model.SETTINGS)
                self.assertTrue(result["online"])
                self.assertFalse(result["checks"]["ping"]["online"])
                self.assertTrue(result["checks"]["web"]["online"])
                result=await probe.check_target(target|{"availability_mode":"all"},model.SETTINGS)
                self.assertFalse(result["online"])
        finally:
            await runner.cleanup()
        result=await probe.check_target({"host":"127.0.0.1","method":"web","web_port":port},
                                        dict(model.SETTINGS,attempts=1))
        self.assertFalse(result["online"])
        self.assertTrue(result["checks"]["web"]["detail"])

    async def test_ping_and_web_combination_rules(self):
        expected_results={
            (True,True):(True,True), (True,False):(True,False), (True,None):(True,None),
            (False,True):(True,False), (False,False):(False,False), (False,None):(None,False),
            (None,True):(True,None), (None,False):(None,False), (None,None):(None,None),
        }
        for ping_value in [True,False,None]:
            for web_value in [True,False,None]:
                for rule in ["any","all"]:
                    with self.subTest(ping=ping_value,web=web_value,rule=rule):
                        def result(value):
                            return {"online":value,"error":"Prüffehler" if value is None else None}
                        with patch.object(probe,"network_check",AsyncMock(return_value=result(ping_value))), \
                             patch.object(probe,"web_check_with_session",AsyncMock(return_value=result(web_value))):
                            value=await probe.check_target({"host":"127.0.0.1","method":"both","availability_mode":rule},model.SETTINGS)
                        expected=expected_results[ping_value,web_value][0 if rule=="any" else 1]
                        self.assertIs(value["online"],expected)
                        self.assertIs(value["checks"]["ping"]["online"],ping_value)
                        self.assertIs(value["checks"]["web"]["online"],web_value)
                        self.assertEqual(bool(value["error"]),expected is None)

    async def test_web_timeout_and_tls_option(self):
        class Request:
            async def __aenter__(self):
                raise TimeoutError
            async def __aexit__(self,*args):
                pass
        session=types.SimpleNamespace(get=unittest.mock.Mock(return_value=Request()))
        result=await probe.check_target({"host":"::1","method":"web","web_scheme":"https",
            "web_port":8443,"verify_tls":False},dict(model.SETTINGS,attempts=2),session=session)
        self.assertFalse(result["online"])
        self.assertIn("Zeitüberschreitung",result["detail"])
        self.assertEqual(session.get.call_count,2)
        self.assertEqual(session.get.call_args.args[0],"https://[::1]:8443/")
        self.assertFalse(session.get.call_args.kwargs["ssl"])
        self.assertFalse(session.get.call_args.kwargs["allow_redirects"])

    async def test_real_tcp_open_then_closed(self):
        def accept(reader,writer):
            writer.close()
        server=await asyncio.start_server(accept,"127.0.0.1",0)
        port=server.sockets[0].getsockname()[1]
        target={"host":"127.0.0.1","method":"tcp","port":port}
        result=await probe.check_target(target,model.SETTINGS)
        self.assertTrue(result["online"])
        self.assertGreaterEqual(result["latency_ms"],0)
        server.close()
        await server.wait_closed()
        result=await probe.check_target(target,model.SETTINGS)
        self.assertFalse(result["online"])

    async def test_dns_failure_is_offline(self):
        with patch.object(asyncio.get_running_loop(),"getaddrinfo",AsyncMock(side_effect=socket.gaierror())):
            result=await probe.check_target({"host":"invalid.example.org","method":"icmp"},model.SETTINGS)
        self.assertFalse(result["online"])

    async def test_permission_fallback_and_permission_error(self):
        target={"host":"127.0.0.1","method":"icmp"}
        answer=types.SimpleNamespace(is_alive=True,avg_rtt=1.2)
        with patch.object(probe,"async_ping",AsyncMock(side_effect=[icmp.SocketPermissionError(),answer])) as ping:
            result=await probe.check_target(target,model.SETTINGS)
            self.assertTrue(result["online"])
            self.assertFalse(ping.call_args_list[0].kwargs["privileged"])
            self.assertTrue(ping.call_args_list[1].kwargs["privileged"])
        with patch.object(probe,"async_ping",AsyncMock(side_effect=icmp.SocketPermissionError())):
            result=await probe.check_target(target,model.SETTINGS)
            self.assertIsNone(result["online"])
            self.assertIn("Berechtigung",result["error"])

    async def test_dns_success_does_not_count_as_ping_success(self):
        records=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("203.0.113.1",0))]
        with patch.object(asyncio.get_running_loop(),"getaddrinfo",AsyncMock(return_value=records)), patch.object(probe,"async_ping",AsyncMock(return_value=types.SimpleNamespace(is_alive=False,avg_rtt=0))):
            result=await probe.check_target({"host":"home.example.org","method":"icmp"},model.SETTINGS)
            self.assertFalse(result["online"])
            self.assertEqual(result["resolved_ips"],["203.0.113.1"])

    async def test_any_responding_dns_address_counts(self):
        records=[(socket.AF_INET,socket.SOCK_STREAM,6,"",(host,0)) for host in ["203.0.113.1","203.0.113.2"]]
        async def ping(address,**kwargs):
            return types.SimpleNamespace(is_alive=address.endswith(".2"),avg_rtt=3)
        with patch.object(asyncio.get_running_loop(),"getaddrinfo",AsyncMock(return_value=records)),patch.object(probe,"async_ping",ping):
            result=await probe.check_target({"host":"home.example.org","method":"icmp"},model.SETTINGS)
            self.assertTrue(result["online"])
            self.assertEqual(len(result["resolved_ips"]),2)
