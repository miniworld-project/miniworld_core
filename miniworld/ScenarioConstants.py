import re

import subprocess32

from miniworld.management.ShellHelper import run_shell_get_output, run_sub_process_popen


def get_nic_models():
    output = run_sub_process_popen("qemu-system-x86_64 -device ?", stdout=subprocess32.PIPE, stderr=subprocess32.PIPE)[0].communicate()[1]
    output = ''.join(output.split("Network devices:")[1:]).split("Input devices:")[0]
    return re.findall('name\s+"([^"]+)', output, re.MULTILINE)