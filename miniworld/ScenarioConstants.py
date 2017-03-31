import re
import subprocess

from miniworld.management.ShellHelper import run_sub_process_popen


def get_nic_models():
    output = run_sub_process_popen("qemu-system-x86_64 -device ?", stdout=subprocess.PIPE, stderr=subprocess.PIPE)[0].communicate()[1].decode()
    output = ''.join(output.split("Network devices:")[1:]).split("Input devices:")[0]
    return re.findall('name\s+"([^"]+)', output, re.MULTILINE)