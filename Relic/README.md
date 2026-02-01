**This version is no longer supported! Instructions may not be current!**

# HydraRoute v.0.0.1b(202501300900)

**The main purpose** is to redirect traffic to **individual domains** via VPN. Anything not listed will be opened directly.

## Installation:
1. Connect to the router via SSH (to Entware).
2. Run the command:
```
curl -L -s "https://github.com/Ground-Zerro/HydraRoute/raw/refs/heads/main/Relic/hydraroute.sh" > /opt/tmp/hydraroute.sh && chmod +x /opt/tmp/hydraroute.sh && /opt/tmp/hydraroute.sh
```
3. Select VPN from the list.

## Additional information:
### How to add domains to ipset

1. The turn web-panel.
   - web-панель доступна по адресу: [http://192.168.1.1:2000/](http://192.168.1.1:2000/)
     * (where `192.168.1.1` is the router's IP address)
2. Manually, by editing the `ipset.conf` file.

    <details>
    <summary>нажать, чтобы прочесть подробней</summary>
    
    1. Чтобы добавить домены для перенаправления, отредактируйте файл: `/opt/etc/AdGuardHome/ipset.conf`.
        ```
        nano /opt/etc/AdGuardHome/ipset.conf
        ```

        <details>
        <summary>Синтаксис файла ipset.conf (нажать, чтобы прочесть подробней)</summary>
    
        ```
        instagram.com,cdninstagram.com/bypass,bypass6
        openai.com,chatgpt.com/bypass,bypass6
        ```
        - On the left side, domains that require crawling are indicated, separated by commas.
        - On the right after the slash is ipset, into which AGH adds the results of DNS name resolution. The example shows the `ipset` created by the script for IPv4 and IPv6: `/bypass,bypass6`.
        - You can specify everything in one line, or you can divide it logically into several lines, as in the example.
        - Domains of the third level and higher are included themselves, i.e. the indication `intel.com` also includes `www.intel.com`, `download.intel.com` and so on.
        </details>
    2. After adding domains, you need to restart **AdGuard Home** with the command:
        ```
        /opt/etc/init.d/S99adguardhome restart
        ```
    </details>

## Removal:
```
curl -Ls "https://ground-zerro.github.io/release/keenetic/hr-uninstall.sh" | sh
```
