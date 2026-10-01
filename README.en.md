# Network Control Center for Home Assistant

<img src="https://raw.githubusercontent.com/VikShepo/ha-pinger/master/custom_components/ha_pinger/brand/icon.png" width="72" height="72" alt="Network Control Center icon">

[Deutsche Anleitung](README.md) · **English**

Monitor your IP addresses and DDNS domains from one Home Assistant page. Choose ping, web checks or both, receive outage notifications, organize devices into groups and favorites, and inspect 30 days of history. A compact dashboard card and optional isolated WireGuard networks are included.

**Version 1.5.0 — German and English, with a softer dark theme.** Fresh installations start empty. Existing addresses, groups, images, notification settings and history are preserved on update.

## Installation and updates

### HACS

1. In **HACS → ⋮ → Custom repositories**, add `https://github.com/VikShepo/ha-pinger` as an **Integration**.
2. Find **Network Control Center** and download it.
3. Restart Home Assistant, then reload your browser or Companion app.
4. For a new installation, go to **Settings → Devices & services → Add integration → Network Control Center**.
5. Open **Network Control Center** in the sidebar and add your own addresses.

Home Assistant **2026.3 or later** is required. Adding this repository to HACS also supports updates for an existing manual installation. Configuration is stored separately from the integration code.

New GitHub releases appear through HACS at its next refresh. For optional automatic installation, import the [update blueprint](https://github.com/VikShepo/ha-pinger/blob/master/blueprints/automation/ha_pinger/release_update.yaml), create an automation from it and select the integration's HACS update entity. Automatic HA restart is **off by default**; without a restart, installed updates take effect at the next restart. The automation is not enabled just by installing this integration.

### Manual ZIP or installer

Download the ZIP from [Releases](https://github.com/VikShepo/ha-pinger/releases/latest). Copy the entire `HA-Pinger/custom_components/ha_pinger` folder to `/config/custom_components/ha_pinger`, replacing existing code when updating. On some systems, the configuration folder is `/homeassistant` instead of `/config`. The `manifest.json` file must sit directly inside `custom_components/ha_pinger`.

Alternatively, extract the package to `/config/HA-Pinger` and run:

```sh
sh /config/HA-Pinger/install.sh /config
```

Or, with Python 3:

```sh
python3 /config/HA-Pinger/install.py --config /config
```

The installer backs up existing code under `ha_pinger_backups`. It does not edit `configuration.yaml` or restart HA. Restart Home Assistant and reload the browser after installation. Add the integration in **Devices & services** if it is not configured yet.

### Dashboard card

Add a manual card to your dashboard:

```yaml
type: custom:ha-pinger-card
title: Network Control Center
compact: true
```

The card shows status totals and up to five favorites. Set `compact: false` for the full interface. The integration registers its JavaScript automatically. If a previously configured manual resource still exists, update it to `/ha_pinger_static/ha-pinger.js?v=1.5.0` as a JavaScript module.

## Language and appearance

Open **Settings → Language** and choose **Follow Home Assistant language**, **Deutsch** or **English**. Automatic mode follows the current HA profile's language; languages other than German use English. A fixed language selection is shared across Control Center views and survives restarts. Background push notifications use the HA system language in automatic mode. User-defined device and group names remain unchanged.

The sun/moon button switches between light mode and a soft charcoal background (`#282828`) with lighter cards (`#333333`). The theme choice is saved in the current browser. Without an override, the mode follows the HA theme. HA accent colors and typography are retained.

## Features

| Feature | How it works |
| --- | --- |
| Checks | Every 5 minutes by default; configurable from 1 to 1,440 minutes. Each device can override the default. |
| Check now | Each entry has an independent check button. The header checks all active addresses. |
| Ping / Web / Both | Separate results; choose whether one successful check or both are required. |
| Status | Green: reachable; red: no response; yellow: technical error; gray: pending or paused. |
| Groups and ordering | Group names and icons, manual arrows, sorting by address, name, status or last check. |
| Favorites and filters | Star individual entries; filter by name, address, status or favorites. |
| Images and icons | PNG/JPEG/WebP up to 10 MB, cropped to 300 × 300; 7,447 searchable Material Design Icons. |
| IP ranges | Optional start–end or CIDR input, including IPv6, with validation and a preview. Up to 256 addresses in total. |
| Group ranges | Optional range beside the group heading. Validation reports existing addresses outside the range. |
| Notifications | Select a Companion app phone, enable each device's bell, and configure the delay in seconds. |
| Recovery and DNS changes | Optional notifications per entry. |
| History | 30 daily rows; each bar represents 30 minutes. Short history bars also appear on mobile. |
| Log | Status changes, errors and push requests; clear per device without clearing history. |
| Web button | Opens the configured web interface for Web/Both entries. |
| WireGuard | Save remote networks; only the selected network is monitored. Selecting Home network closes the tunnel. |
| HA entities | A native connectivity binary sensor for each address. |

Only administrators can change settings or start manual checks. Other signed-in users can view the status. A new installation has no sample addresses or groups, and notifications are off for newly added addresses.

### Ping and web checks

Some devices block ICMP but respond in a browser. Choose **Web** or **Both** for these devices. Enter only the IP or domain in the address field; configure protocol, port and path separately. For `https://192.168.1.1:8443/status`, choose HTTPS, port 8443 and path `/status`.

Any HTTP response confirms reachability, including login pages, redirects and error pages. Page content and redirect destinations are not checked. HTTPS certificates are verified by default; verification can be disabled per device for a self-signed certificate. Existing TCP entries remain supported.

With **Both**, the default rule is **At least one check succeeds**. Web can therefore keep the overall status green when ping fails. Outage alerts, history and the HA entity follow the selected rule. A technical error is shown separately when no conclusive overall result is possible.

### Groups, ranges and images

Use **Group → Add group** to create up to 64 groups. Groups apply to both tabs. Assign addresses when adding or editing them. Moving entries with the arrows saves immediately.

A group range can be a single IP, a start–end range such as `192.168.1.20-192.168.1.30`, or CIDR such as `192.168.1.0/28`. Validation checks address formats, matching IP versions, ascending bounds and the 256-address limit. CIDR is normalized to its network address. Existing addresses outside the range are listed as a warning and preserved.

Saving a group range does not create devices automatically. Use **Add addresses from range**, choose a method and review the preview. Existing entries with the same address, method and network are skipped. Entries are created even when currently unreachable.

Upload a custom image when editing an individual address. **Remove image** restores its icon. The icon catalog supports English names and German search terms. Images and configuration stay local to HA. Icon source: [Pictogrammers / Material Design Icons](https://github.com/Templarian/MaterialDesign-SVG), version 7.4.47; license files are included.

## Phone notifications

1. Set up the Home Assistant Companion app and allow notifications.
2. Select your `notify.mobile_app_…` service in Control Center settings and save.
3. Reopen settings and use **Test saved phone**.
4. Enable the bell for each address that should alert you.
5. Set **Outage alert after · seconds** between 0 and 86,400. Zero sends after the first failed check.

The delay starts when a check first detects an outage. The notification scheduler runs independently of the check interval. For example, a failed check at 12:00:00 with a 10-second delay becomes due at 12:00:10 while the last result still indicates an outage. Old settings in minutes are converted: 5 minutes becomes 300 seconds.

One alert is sent per outage after a successful service call. If the service reports an error, it retries after 30 seconds while the outage persists. Test and outage notifications use the same saved service. A successful service call confirms handoff to HA, not delivery to the phone.

If a test arrives but an outage alert does not, check the inline push status and the device's **Log**. Verify the bell, delay and combined check rule. With Both/Any, an alert requires both ping and web to fail. Also check HA's `mobile_app` logs and phone notification permissions when the service reports success but no notification arrives.

## History, DDNS and remote networks

The heartbeat button opens 30 days of history. Each bar summarizes 30 minutes: red means at least one failed check, yellow a technical error, green a successful check, gray no measurement. Tap a bar for its time period. The log keeps up to 30 days and 2,000 entries per device. Clearing it preserves history. Pausing or changing the check method also preserves history; changing the target address or network starts a new history.

DDNS entries monitor domain names; they do not update your DDNS provider. Enter a domain without a URL prefix, port or path. DNS is resolved for each check, subject to DNS caches. A successful DNS lookup alone does not count as reachable. Ping and legacy TCP check up to eight resolved addresses; one response is enough. Web checks use the domain and its certificate.

For remote networks, install the optional [WireGuard app](addons/ncc_vpn/DOCS.en.md). Its isolated network stack keeps HA's routes unchanged. Only the selected network is monitored; other checks and outage timers pause. Network selection is shared across users. Opening a remote web interface requires the browser itself to have access to that network.

Brief outages between checks can go undetected. Availability percentages represent successful stored checks, not a continuous measurement. No checks occur while HA is stopped; after a restart, status remains pending until fresh results arrive.

## Troubleshooting icons and panel loading

**HACS says “Icon not available”:** The release includes `brand/icon.png` and `brand/icon@2x.png`. HACS 2.0.5 still uses the old public image server and does not display these locally bundled icons. The [HACS issue](https://github.com/hacs/integration/issues/5223) and [proposed fix](https://github.com/hacs/frontend/pull/937) remain open as of October 1, 2026. Reinstalling this integration does not resolve the HACS placeholder. HA 2026.3+ supports the icons in **Devices & services**.

**“Unable to load custom panel”:** Replace the complete integration folder, restart HA and reload the frontend. Version 1.5.0 loads `ha-pinger.js?v=1.5.0`, along with its CSS, translation module and bundled JSON files. Changing just the version in a URL does not update the files. Check the browser console and failed requests if the current complete package still fails.

## Data and complete removal

Settings and history are stored in `.storage/ha_pinger`, the app access key in `.storage/ha_pinger_secrets`, and images in `.storage/ha_pinger_images`. Updates preserve them. The optional WireGuard app has its own persistent profile storage. Include both integration data and the app in HA backups.

To remove everything:

1. Remove the integration in **Devices & services**, its dashboard cards, optional update automation and any manually added JavaScript resource.
2. Stop and uninstall the optional WireGuard app and remove its app data.
3. Stop HA. Remove `custom_components/ha_pinger` and only the three `.storage/ha_pinger…` paths listed above.
4. Remove any extracted package, local `/addons/ncc_vpn` folder, `ha_pinger_backups` and `ha_pinger_vpn_backups` if no longer needed. Start HA again.

Older HA backups may still contain saved profiles. No router settings or host routes are changed by this integration.

## Development

Run `python -m unittest discover -s tests -v`, `node tools/ui_smoke.mjs` and `go test ./...` inside the app folder. UI tests cover German and English, desktop and mobile, language switching and both themes. Push tests simulate the HA service boundary; real phone delivery and the user's Pi require verification on that installation.

Build with `python tools/build.py` and validate with `python tools/validate_release.py`. Matching version tags trigger the GitHub workflow, which tests the software, builds the WireGuard container and publishes the ZIP. Demo fixtures under `preview/` are excluded from the release and appear only with the explicit `?fixtures` flag.
