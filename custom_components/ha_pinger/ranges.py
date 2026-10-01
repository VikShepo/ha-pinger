"""Bounded explicit address ranges; never scan or expand arbitrary subnets."""

import ipaddress


def describe_range(value, limit=256):
    """Validate a range and return canonical text plus its usable addresses."""
    hosts = expand_range(value, limit)
    value = value.strip()
    canonical = (str(ipaddress.ip_network(value, strict=False)) if "/" in value
                 else f"{hosts[0]}-{hosts[-1]}" if "-" in value else hosts[0])
    return {"range": canonical, "count": len(hosts), "first": hosts[0], "last": hosts[-1],
            "version": ipaddress.ip_address(hosts[0]).version}


def expand_range(value, limit=256):
    if not isinstance(value, str) or len(value) > 160 or "%" in value:
        raise ValueError("Bitte einen IP-Bereich oder ein CIDR-Netz eingeben.")
    value = value.strip()
    try:
        if "/" in value:
            network = ipaddress.ip_network(value, strict=False)
            count = network.num_addresses
            if network.version == 4 and network.prefixlen < 31:
                count -= 2
            elif network.version == 6 and network.prefixlen < 127:
                count -= 1
            if count > limit:
                raise ValueError(f"Ein Bereich darf höchstens {limit} Adressen enthalten.")
            return [str(host) for host in network.hosts()]
        start, separator, end = value.partition("-")
        first = ipaddress.ip_address(start.strip())
        last = ipaddress.ip_address(end.strip()) if separator else first
        if first.version != last.version or int(last) < int(first):
            raise ValueError("Anfang und Ende müssen zum selben IP-Typ gehören und aufsteigend sein.")
        count = int(last) - int(first) + 1
        if count > limit:
            raise ValueError(f"Ein Bereich darf höchstens {limit} Adressen enthalten.")
        address_type = type(first)
        return [str(address_type(int(first) + offset)) for offset in range(count)]
    except ValueError as err:
        raise ValueError(f"Ungültiger IP-Bereich: {err}") from err
