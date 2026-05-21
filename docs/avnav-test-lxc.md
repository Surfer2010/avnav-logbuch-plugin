AVNav-Testumgebung in Proxmox LXC
Empfohlene Umgebung
```text
Debian 12 LXC
1 CPU
512 MB RAM
4-8 GB Disk
Netzwerk mit fester IP oder DHCP
```
AVNav installieren
```bash
apt update
apt install -y wget gpg

wget -O - https://www.free-x.de/debian/oss.boating.gpg.key | gpg --dearmor | tee /usr/share/keyrings/oss.boating.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/oss.boating.gpg] https://www.free-x.de/debian bookworm main contrib non-free" > /etc/apt/sources.list.d/boating.list

apt update
apt install -y avnav

systemctl enable avnav
systemctl start avnav
```
Zugriff
```text
http://IP-DES-LXC:8080
```
Plugin-Pfad
```text
/var/lib/avnav/plugins/logbook
```
Wichtige Logs
```bash
journalctl -u avnav -f
tail -f /var/lib/avnav/log/avnav.log
```
