"""Actual local HTTP transport for the integration-to-app bridge."""
import importlib
import unittest

from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from support import model

vpn = importlib.import_module('pinger_under_test.vpn')


class BridgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_authenticated_profile_check_and_unavailable_app(self):
        requests=[]
        async def check(request):
            self.assertEqual(request.headers['Authorization'],'Bearer '+'x'*40)
            requests.append(await request.json())
            return web.json_response({'online':True,'resolved_ips':['10.0.0.1'],'checks':{'ping':{'online':True}}})
        app=web.Application();app.router.add_post('/check',check)
        async with TestServer(app) as server, ClientSession() as session:
            client=vpn.AgentClient(session,{'agent_url':str(server.make_url('')).rstrip('/'),'agent_token':'x'*40})
            target=model.TARGET|{'host':'10.0.0.1','network_id':'remote','name':'Private label'}
            result=await client.check(target,model.SETTINGS)
            self.assertTrue(result['online'])
            self.assertEqual(requests[0]['profile_id'],'remote')
            self.assertNotIn('name',requests[0]['target'])
            self.assertNotIn('notify_service',requests[0]['settings'])
            await server.close()
            failed=await client.check(target,model.SETTINGS)
            self.assertIsNone(failed['online'])
            self.assertIn('nicht erreichbar',failed['error'])

    async def test_auth_and_invalid_response_are_errors(self):
        async def response(request):
            if request.path=='/denied':return web.json_response({'error':'denied'},status=401)
            if request.path=='/redirect':return web.json_response({'online':True},status=302,headers={'Location':'/other'})
            return web.json_response([])
        app=web.Application();app.router.add_get('/{name}',response)
        async with TestServer(app) as server, ClientSession() as session:
            client=vpn.AgentClient(session,{'agent_url':str(server.make_url('')).rstrip('/'),'agent_token':'x'*40})
            for path in ['/denied','/invalid','/redirect']:
                with self.subTest(path=path),self.assertRaises(ValueError):await client.request('GET',path)
            client.secrets={}
            with self.assertRaises(ValueError):await client.request('GET','/health')
