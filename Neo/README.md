# HydraRoute Neo

**HydraRoute Neo** is the next stage in the development of HydraRoute.

---

## 📚 Table of contents

- [🚀 What can Neo do?](#-what-neo-can-do)
- [📋 System requirements](#-system-requirements)
- [📁 Configuration](#-configuration)
- [🌐 IPv6](#-ipv6)
- [🔧 Control](#-control)
- [🔍 Checking and Debugging](#-checking-and-debugging)
- [💾 Installation](#-installation)
- [🔀 Multitunneling](#-multitunneling)
- [🧬Bandwidth summation](#-bandwidth summation)
- [🔄 Update](#-update)
- [❌ Deletion](#-deletion)
- [⚙️ Principles and stages of work](#️-principles-and-stages-of-work)
- [☕ Donate](#-donate)
- [⚠️ Disclaimer](#️-disclaimer)

---

## 🚀 What can Neo do?

Neo supports all the features of the classic version, plus:

- **Does not require disabling the system DNS server**.
- **The user himself sets the names and number of policies**.
- **IPv6 support (including ipset and ip6tables)**.

> ⚠️ The project is presented as a concept and serves to confirm the viability of the idea, without being a finished product.
> Technical support - **not provided**.

---

## 📋 System requirements

To install and operate HydraRoute Neo you need:

- Роутер Keenetic с установленным [Entware](https://help.keenetic.com/hc/ru/articles/360021214160-Установка-системы-пакетов-репозитория-Entware-на-USB-накопитель)
- Installed `curl` package:
  ```
  opkg install curl
  ```

---

## 📁 Configuration

### 📄 Domains file:
`/opt/etc/HydraRoute/domain.conf`

Format:
```
example.com,domain.net/PolicyName
google.com,youtube.com/Warp
```

- The separator is **comma**.
- After the slash - **policy name**.
- Spaces in lines are **not allowed**.
- Domains in different lines **must not intersect**.

### ⚙️ Neo configuration:
`/opt/etc/HydraRoute/hrneo.conf`

Default configuration:
```
watchlistPath=/opt/etc/HydraRoute/domain.conf
interfaceName=br0
reconnect=true
log=false
logfile=/opt/var/log/hrneo.log
```

- `watchlistPath` - full path to the file with the list of domains.
- `interfaceName` is the system interface for tracking. Specify `any` if you want to track everything. Changing the interface is **not recommended**.
- `reconnect` - close existing connections to an IP when it is first added to ipset: `true`, `false`.
- `log` — logging level: `console`, `file`, `false`. Enabling the log without debugging purposes is **not recommended**.
- `logfile` — path to the log file, if `log=file`.

---

## 🌐 IPv6

IPv6 support is available.
If you don’t use it, disable IPv6 in the connection settings of your provider and/or VPN connection.
👉 Для работы [IPv6 через VPN](https://yandex.ru/search/?text=Для+работы+IPv6+через+VPN&clid=6799014&banerid=6500000000&win=672&lr=79) необходимо соблюдение всех четырех условий одновременно:  
- ipv6 must be from the main provider
- The VPN server must have ipv6
- ipv6 must be on the `WG` (`PPTP`, `L2TP`, `OpenVPN` etc.) peer
- ipv6 routing must be configured on the VPS

---

## 🔧 Management

| Team | Description |
|:--------------|:-----------------|
| `neo status` | Check status |
| `neo start` | Launch |
| `neo stop` | Stop |
| `neo restart` | Restart |

Alternatively:
```
/opt/etc/init.d/S99hrneo status|start|stop|restart
```

---

## 🔍 Checking and debugging

### 🚦 iptables:

Check for rules in iptables
```
iptables -t mangle -S | grep -E 'HydraRoute'       # IPv4
ip6tables -t mangle -S | grep -E 'HydraRoute'      # IPv6
```

### 🗃️ ipset:

Check if IPset is full
```
ipset list HydraRoute        # IPv4
ipset list HydraRoutev6      # IPv6
```

### 🧹 Cleaning ipset:

Clear ipset from accumulated IP addresses
```
ipset flush HydraRoute        # IPv4
ipset flush HydraRoutev6      # IPv6
```
  - or protso [restart HydraRoute Neo](#-control)

> 👉 Replace `HydraRoute` with **name of your policy**

---

## 💾 Installation

1. 📦 Добавить [репозиторий](https://ground-zerro.github.io/release/) в Entware:
```
curl -Ls "https://ground-zerro.github.io/release/keenetic/install-feed.sh" | sh
```

2. 🚀 Install HydraRoute Neo:
```
opkg install hrneo
```

> 👉 HydraRoute Neo is ready to work immediately after installation. The service starts automatically.

---

## 🔀 Multi-tunneling

To redirect individual domains to different separate tunnels, create separate
lines in `domain.conf` with different policy names (for example, `/Warp`, `/Obhod`, `/Zakop`, etc.).

After [restarting the HydraRoute Neo service](#-management), the policy will be created automatically.
👉 In the router's Web interface, you need to specify and activate the required connection for the new policy.

---

## 🧬 Capacity summing

В одной политике можно указать несколько VPN-подключений одновременно, активировав [режим многопутевой маршрутизации Keenetic](https://help.keenetic.com/hc/ru/articles/7490633500572-Многопутевая-передача-суммирование-пропускной-способности-нескольких-интернет-соединений).  
👉 In this mode, all connections included in the policy transmit traffic by aggregating channel bandwidth.

---

## 🔄 Update

Conmada for updating installed packages:
```
opkg update && opkg upgrade
```

---

## ❌ Removal

Standard:
```
opkg remove hrneo
```

Complete deletion (including files, logs, etc.) with a rollback of all changes in the system to standard:
```
curl -Ls "https://ground-zerro.github.io/release/keenetic/hr-uninstall.sh" | sh
```

---

## ⚙️ Principles and stages of work

1. **Loading configuration**
Loading settings: interface, log file, domains.

2. **Formation of IPSET groups**
Creation of ipset groups for IPv4/IPv6 for each domain.

3. **Creating routing policies**
Checking and automatic creation of policies via `ndmc`.

4. **Traffic routing**
Setting iptables/ip6tables rules using `CONNMARK`.

5. **Analysis of DNS queries**
Monitor DNS and add domain IP addresses to ipset if there is a match.

6. **Control and configuration**
Closing sessions, maintaining and updating routing rules, logging, configuration via config.

---

## ☕ Donate

If HydraRoute Neo was useful, you can thank the author:

- [Угостив](https://boosty.to/ground_zerro/donate) кружечкой горячего какао 😋
- Став [подписчиком](https://boosty.to/ground_zerro)

---

## ⚠️ Disclaimer

> The author is not responsible for any consequences. Using this script, you act at your own peril and risk.
