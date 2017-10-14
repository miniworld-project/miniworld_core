
# a cleanup script in case the backend does not exit correctly

pkill -fe -9 mwserver
pkill -fe -9 RPCServer.py
killall -9 qemu-system-x86_64

umount /tmp/MiniWorld
rm -r /tmp/MiniWorld

brctl delbr mgmt
ip link del miniworld_tap
ip l d mgmt

# remove devices
remove_links() {
    for i in `ip l|grep $1| cut -d' ' -f2 | cut -d '@' -f1`; do ip link del $i; done
}
remove_links "gr_"
remove_links "gre_"
remove_links "wifi"
remove_links "vln"
remove_links "vxl"

ebtables --atomic-file /tmp/ebtables_atommic --atomic-init
ebtables --atomic-file /tmp/ebtables_atommic --atomic-commit

for i in `brctl show|grep br_| awk '{print $1}'`; do ifconfig $i down && brctl delbr $i; done
find . -name '*.pyc' -delete
