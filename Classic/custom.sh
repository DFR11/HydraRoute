#!/bin/sh

# Utility functions and variables
LOG="/opt/var/log/HydraRoute.log"
echo "$(date "+%Y-%m-%d %H:%M:%S") Starting the CRUTCH installation" >> "$LOG"

## animation
animation() {
	local pid=$1
	local message=$2
	local spin='-\|/'

	echo -n "$message... "

	while kill -0 $pid 2>/dev/null; do
		for i in $(seq 0 3); do
			echo -ne "\b${spin:$i:1}"
			usleep 100000  # 0.1 sec
		done
	done

	wait $pid
	if [ $? -eq 0 ]; then
		echo -e "\b✔ Done!"
	else
		echo -e "\b✖ Error!"
	fi
}

# Getting a list and selecting an interface
get_interfaces() {
    ## display a list of interfaces to choose from
    echo "Available interfaces:"
    i=1
    interfaces=$(ip a | sed -n 's/.*: \(.*\): <.*UP.*/\1/p')
    interface_list=""
    for iface in $interfaces; do
        ## check if the interface exists, ignoring errors 'ip: can't find device'
        if ip a show "$iface" &>/dev/null; then
            ip_address=$(ip a show "$iface" | grep -oP 'inet \K[\d.]+')

            if [ -n "$ip_address" ]; then
                echo "$i. $iface: $ip_address"
                interface_list="$interface_list $iface"
                i=$((i+1))
            fi
        fi
    done

    ## we ask the user for the interface name with input verification
    while true; do
        read -p "Enter the NAME of the interface through which traffic will be redirected:" net_interface

        if echo "$interface_list" | grep -qw "$net_interface"; then
            echo "Interface selected: $net_interface"
			break
		else
			echo "Incorrect choice, you must enter the interface NAME from the list."
		fi
	done
}

# Installing packages
opkg_install() {
	opkg update
	opkg install ip-full jq
}

# Generating files
files_create() {
## ipset
	cat << EOF > /opt/etc/init.d/S52ipset
#!/bin/sh

PATH=/opt/sbin:/opt/bin:/opt/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

if [ "\$1" = "start" ]; then
    ipset create bypass hash:ip
    ip rule add fwmark 1001 table 1001
fi
EOF
	
## routing scripts
	cat << EOF > /opt/etc/ndm/ifstatechanged.d/010-bypass-table.sh
#!/bin/sh

[ "\$system_name" == "$net_interface" ] || exit 0
[ ! -z "\$(ipset --quiet list bypass)" ] || exit 0
[ "\${connected}-\${link}-\${up}" == "yes-up-up" ] || exit 0

if [ -z "\$(ip route list table 1001)" ]; then
    ip route add default dev \$system_name table 1001
fi
EOF

## traffic marking scripts
	cat << EOF > /opt/etc/ndm/netfilter.d/010-bypass.sh
#!/bin/sh

[ "\$type" == "ip6tables" ] && exit
[ "\$table" != "mangle" ] && exit
[ -z "\$(ip link list | grep $net_interface)" ] && exit
[ -z "\$(ipset --quiet list bypass)" ] && exit

iptables -w -t mangle -C PREROUTING ! -i $net_interface -m conntrack --ctstate NEW -m set --match-set bypass dst -j CONNMARK --set-mark 1001 2>/dev/null || \
iptables -w -t mangle -A PREROUTING ! -i $net_interface -m conntrack --ctstate NEW -m set --match-set bypass dst -j CONNMARK --set-mark 1001

iptables -w -t mangle -C PREROUTING ! -i $net_interface -m set --match-set bypass dst -j CONNMARK --restore-mark 2>/dev/null || \
iptables -w -t mangle -A PREROUTING ! -i $net_interface -m set --match-set bypass dst -j CONNMARK --restore-mark
EOF
}

# A basic list of domains for a crutch with 3D protection, just in case...))
domain_add() {
	config_file="/opt/etc/AdGuardHome/ipset.conf"
	pattern="googlevideo.com\|ggpht.com\|googleapis.com\|googleusercontent.com\|gstatic.com\|nhacmp3youtube.com\|youtu.be\|youtube.com\|ytimg.com"
	sed -i "/$pattern/d" "$config_file"
	echo "googlevideo.com,ggpht.com,googleapis.com,googleusercontent.com,gstatic.com,nhacmp3youtube.com,youtu.be,youtube.com,ytimg.com/bypass" >> "$config_file"
}

# Setting permissions for scripts
chmod_set() {
	chmod +x /opt/etc/init.d/S52ipset
	chmod +x /opt/etc/ndm/ifstatechanged.d/010-bypass-table.sh
	chmod +x /opt/etc/ndm/netfilter.d/010-bypass.sh
}

# Disabling ipv6 on your provider
disable_ipv6() {
	curl -kfsS "localhost:79/rci/show/interface/" | jq -r '
	  to_entries[] | 
	  select(.value.defaultgw == true or .value.via != null) | 
	  if .value.via then "\(.value.id) \(.value.via)" else "\(.value.id)" end
	' | while read -r iface via; do
	  ndmc -c "no interface $iface ipv6 address"
	  if [ -n "$via" ]; then
		ndmc -c "no interface $via ipv6 address"
	  fi
	done
	ndmc -c 'system configuration save'
}

# Message installation OK
complete_info() {
	echo "CRUTCH installation is complete"
	echo "Press Enter to reboot (required)."
}

# === main ===
# Requesting an interface from the user
get_interfaces

# Installing packages
opkg_install >>"$LOG" 2>&1 &
animation $! "Installing required packages"

# Formation of scripts
files_create >>"$LOG" 2>&1 &
animation $! "Generating scripts"

# Adding YOUTUBE to ipset
domain_add >>"$LOG" 2>&1 &
animation $! "Adding to ipset YOUTUBE via a crutch"

# Setting permissions to execute scripts
chmod_set >>"$LOG" 2>&1 &
animation $! "Setting permissions to execute scripts"

# Disabling ipv6
disable_ipv6 >>"$LOG" 2>&1 &
animation $! "Disabling ipv6"

# Completion
echo ""
complete_info
rm -- "$0"

# We wait for Enter and reboot
read -r
reboot
