# HydraRoute Classic

**HydraRoute Classic** - you can choose where to redirect individual domains or a group/list of domains
simply by changing the connection in the access policy of the router's web interface.

---

## 📚 Table of contents

- [🚀 Classic features](#-classic features)
- [📋 System requirements](#-system-requirements)
- [💾 Installation](#-installation)
- [📁 Working with domains](#-working-with-domains)
- [🔧 Access policies](#-access-policies)
- [🔄 Update](#-update)
- [❌ Deletion](#-deletion)
- [ℹ️ Notes](#️-notes)
- [☕ Donate](#-donate)

---

## 🚀 Classic features

- Redirect domain traffic to VPN.
- Supports up to 3 access policies.
- Changing the connection for a group of domains without restarting.
- WARP compatible.

---

## 📋 System requirements

- Роутер Keenetic с установленным [Entware](https://help.keenetic.com/hc/ru/articles/360021214160)
- Installed `curl` package:
  ```
  opkg install curl
  ```

---

## 💾 Installation

1. 📦 Add repository:
```
curl -Ls "https://ground-zerro.github.io/release/keenetic/install-feed.sh" | sh
```

2. 🚀 Install HydraRoute Classic:
```
opkg install hydraroute
```

> ⚠️ After installation, the device will automatically reboot.

3. ✅ Settings after downloading:
   - Router web interface → **Connection priorities → Internet access policies**
   - Find the **HydraRoute1st** policy and mark the desired connection

---

## 📁 Working with domains

Choice: via the Web interface **OR** manually.

### 🖥️ Via the Web interface:

- Открыть [http://hr.net/](http://hr.net/) или [http://192.168.1.1:2000/](http://192.168.1.1:2000/)
- Default password: `keenetic`

### ✍️ Manually:

1. Open file:
`/opt/etc/AdGuardHome/domain.conf`
```
nano /opt/etc/AdGuardHome/domain.conf
```

2. Add domains:
```
youtube.com,googlevideo.com/hr1
openai.com,chatgpt.com/hr2
```

- Domains are separated by comma
- After `/` - the name of the ipset group (see table below)

| Politics | ipset |
|:------------------|:------|
| HydraRoute1st     | hr1   |
| HydraRoute2nd     | hr2   |
| HydraRoute3rd     | hr3   |

3. 💡 Restarting AdGuard Home:
```
agh restart
```

> 👉 Subdomains (`*.google.com`, `*.yandex.ru` etc.) are picked up automatically

---

## 🔧 Access policies

- Policies can be assigned to both domains and devices.
- If all connections are disabled in the policy, domain traffic is blocked.
- The order of tunnels in the policy specifies the switching priority when connection is lost.

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
opkg remove hydraroute
```

Complete deletion (including files, logs, etc.) with a rollback of all changes in the system to standard:
```
curl -Ls "https://ground-zerro.github.io/release/keenetic/hr-uninstall.sh" | sh
```

---

## ℹ️ Notes

- Do not rename or delete the `HydraRoute` policies (`1st`, `2nd`, `3rd`), otherwise the script will stop working.

---

## ☕ Donate

If HydraRoute was useful to you, you can thank the author:

- [Угостив](https://boosty.to/ground_zerro/donate) кружечкой горячего какао 😋
- Став [подписчиком](https://boosty.to/ground_zerro)
