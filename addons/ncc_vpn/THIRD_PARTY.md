# Dependencies

The module versions and checksums are pinned in `go.mod` and `go.sum`. The Docker build downloads their source using Go modules.

- [WireGuard Go](https://git.zx2c4.com/wireguard-go/) — MIT license, including its netstack adapter.
- [gVisor](https://github.com/google/gvisor) — Apache License 2.0.
- [Go supplementary libraries](https://go.googlesource.com/) — BSD-style licenses; see each module's LICENSE file.
- [Google B-tree](https://github.com/google/btree) — Apache License 2.0.

The Docker build copies dependency license and notice files into `/usr/share/licenses/ncc-vpn` in the resulting image.
