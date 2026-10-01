# Set up WireGuard networks

[Deutsch](DOCS.md) · **English**

## Install the app

On Home Assistant OS, open **Settings → Apps → Store → ⋮ → Repositories** and add `https://github.com/VikShepo/ha-pinger`. Install **Network Control Center WireGuard**. Future app updates will be offered through the app store; automatic updates can be enabled on the app page.

The repository app uses an internal hostname such as `<repository-id>-ncc-vpn`. Run `ha addons list` and then `ha addons info <app-id>` in the HA terminal to find the hostname. Enter `http://<hostname>:8099` under **Networks → Connect app** in the Control Center.

Alternatively, extract the release ZIP to `/config/HA-Pinger` and run:

```sh
sh /config/HA-Pinger/install-vpn.sh /addons
```

Or copy `addons/ncc_vpn` into HA's separate `addons` share, then refresh the app store and install it under **Local apps**. The File Editor for `/homeassistant` usually does not expose the separate `/addons` folder. Building the app on the Pi may take several minutes and requires internet access to download dependencies.

A local app and a repository app have separate data stores. When migrating, set up the access key and upload the original WireGuard profiles again in the new app. Keep the old app until the replacement works.

## Connect to the integration

1. In Network Control Center, open **Networks → Connect app**.
2. Generate an access key and copy it.
3. Set the app URL. A local installation uses `http://local-ncc-vpn:8099`; a repository installation uses its own internal hostname. Save.
4. Paste the same key into the WireGuard app's **Access key / api_token** configuration and save.
5. Start the app and enable **Start on boot**.
6. In the Control Center, use **Networks → Test connection**.

The key must contain at least 32 characters. No API port needs to be published to the home network when using HA's internal app hostname. Configuration labels are available in German and English.

## Save and activate a network

1. Create a dedicated WireGuard client configuration on your VPN server or router. Reusing a profile that is active on another device can disrupt its connection.
2. Use **Networks → Add network**, name it, upload the `.conf` file and save.
3. Select **Activate** for that network. Add its addresses or assign existing entries to it.
4. Use **Check now** to test through the active tunnel.
5. Select **Home network → Activate** to close the tunnel and resume local checks.

Only the active network is monitored. Other profiles remain saved, but their tunnels, checks and outage timers are paused. Switching cancels running checks and begins fresh measurements while preserving history and logs. The selected network is shared by all Control Center users and is restored after restarting.

Up to 16 profiles and 256 total addresses are supported. Identical IP addresses in different profiles are separate entries. Before deleting a network, activate the home network and remove or reassign its addresses. Editing a network can replace its configuration or just rename it.

## Supported configurations and routing

The app uses an isolated WireGuard network stack inside its process. It does not request `NET_ADMIN` or `/dev/net/tun` and runs with `host_network: false`. Even a full-tunnel profile applies only to this isolated stack; HA's own host routes are unchanged.

Upload a standard WireGuard configuration of up to 32 KB with one Interface section and 1–8 peers. Script hooks and system-route commands are rejected. Supported interface fields: `PrivateKey`, `Address`, `DNS`, `MTU`, `ListenPort`. Peer fields: `PublicKey`, `PresharedKey`, `AllowedIPs`, `Endpoint`, `PersistentKeepalive`. `ListenPort` is accepted but the app uses independent ephemeral UDP sockets. Standard WireGuard is supported; vendor-specific protocol extensions are not.

The remote network must permit traffic from the configured WireGuard peer. DNS queries use the profile's DNS servers when configured. The remote endpoint must be reachable from HA's normal connection. A running tunnel alone does not prove the destination device is reachable.

The **Open web interface** button opens an address in your browser. That browser needs its own access to the remote network; the app's tunnel only carries background checks.

## Updates, backup and removal

Update repository installations through the HA app store. For local installations, copy the updated app files or run `install-vpn.sh` again, then rebuild/reinstall the local app using the app store controls. Keep the Network Control Center integration up to date too.

Profiles and private keys are stored in the app's persistent `/data` directory. Include the app in HA backups. Removing a network deletes its profile; removing the app and its data removes all profiles. Old backups can still contain earlier profiles.

For full removal, stop and uninstall the app, remove its data, and remove the local `/addons/ncc_vpn` source folder if used. The integration itself can be removed separately.
