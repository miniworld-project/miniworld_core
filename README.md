# MiniWorld Core

Work-in-Progress! Code and documentation are following ...

## About
MiniWorld (Mobile Infrastructure'n'Network Integrated World) enables network emulation in Linux.

Distributed applications, routing algorithms, etc. can be tested with MiniWorld.

For that purpose, the software-under-test has to be deployed in a KVM VM. Afterwards, the VMs can be interconnected by a network backend. For each connection, different static or event-based link-impairment can be applied. The network topology changes with a step.

## Features
- Network emulation with Linux Bridges and VDE
	- Wired and wireless link emulation
- Qemu/KVM node virtualization
- Movement Patterns such as RandomWalk and [CORE](https://www.nrl.navy.mil/itd/ncs/products/core) integration
- Basic Link Quality models with Linux HTB and netem

## Contribute
MiniWorld is an open-source project.
Do you have some good ideas, improvements, or even want to get your hands dirty?
There is a lot of work in the backlog and we can assign you small issues such that you can have a closer look at the source code.
Do not hesitate to contact us!

## Backlog
- Documentation
- More advanced scenario editor (currently: CORE)
- High-fidelity link-emulation (integrate with ns-3?)
- Android-based emulation with location (lat/lon) set via adb
- Lightweight virtualization for cases where full-system virt. is not needed
- Web UI

## Demo

<iframe width="560" height="315" src="https://www.youtube.com/embed/j6D-43Tso04?list=PLU2J7CyV0Bom-gBxH_NdKPX8jfrQDtS5v" frameborder="0" allowfullscreen></iframe>
