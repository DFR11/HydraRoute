# HydraRoute

**HydraRoute** is a tool for separate routing of traffic across domains using VPN on **Keenetic** routers.

💡 Traffic to the specified domains is sent through the VPN, and everything else is sent directly.
Policy management - via the router's Web interface or configuration files.

---

## 🚀 Opportunities

- Redirect traffic of individual domains via VPN.
- Supports multiple policies and routing to different tunnels.
- IPv6 and ip6tables support (in Neo).
- Configuration via Web interface or manually.
- Supports multi-WAN and link aggregation.
- Secure DNS over TLS.
- Possibility of summing channel capacity.
- Redirect individual domains through different VPNs.
- WARP compatible.
- Ad filtering (in Classic).

---

## 🧬HydraRoute versions

### 🔹 Classic

- Easy to install and manage.
- Manage connections via the Keenetic web interface.
- Editing domain lists in the RydraRoute Web interface.
- Supports up to 3 preset policies.
- IPset integration with AdGuard Home.
- Suitable for most users.

[Подробнее →](https://github.com/Ground-Zerro/HydraRoute/tree/main/Classic)

---

### 🔸 Neo

- For advanced users.
- Does not require system DNS to be disabled.
- The user himself sets the names and number of policies.
- Full IPv6 support.

[Подробнее →](https://github.com/Ground-Zerro/HydraRoute/tree/main/Neo)

⚠️ *Neo is a concept and proof of the viability of the approach. Support is limited.*

---

## 📋 Requirements

- Router with KeenOS
- Entware (installed and configured)
- Configured VPN connection (WireGuard, OpenVPN, etc.)
- Installed `curl`

---

## 🧭 Plans for the future

- vless support
- Интеграция с [zapret](https://github.com/bol-van/zapret)
- Updates from WebUI

---

## ☕ Support

If the project was useful to you, you can support the author:

- [Поддержать на Boosty](https://boosty.to/ground_zerro)
