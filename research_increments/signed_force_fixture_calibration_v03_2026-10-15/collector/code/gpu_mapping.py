"""Read-only UUID, PCI, device-minor and DRM admission; no GPU allocation."""
import argparse
import json
from pathlib import Path
import re
import subprocess

def mapping(uuid,minimum_free_mib=24576):
    if not re.fullmatch(r'GPU-[0-9a-fA-F-]{36}',uuid):raise ValueError('explicit GPU UUID required')
    matches=[]
    for p in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        text=p.read_text()
        if uuid in text:matches.append((p,text))
    if len(matches)!=1:raise ValueError('GPU UUID has no unique physical PCI device')
    p,info=matches[0];pci=p.parent.name;minor=int(re.search(r'Device Minor:\s*(\d+)',info).group(1))
    drm=[]
    for d in Path('/sys/class/drm').iterdir():
        if re.fullmatch(r'card\d+|renderD\d+',d.name) and (d/'device').resolve().name==pci:
            drm.append(d.name)
    cards=sorted(x for x in drm if x.startswith('card'));renders=sorted(x for x in drm if x.startswith('renderD'))
    if len(cards)!=1 or len(renders)!=1:raise ValueError('UUID does not have a unique DRM pair')
    line=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,pci.bus_id,memory.free','--format=csv,noheader,nounits','-i',uuid],text=True).strip()
    reported_uuid,reported_pci,free=[x.strip() for x in line.split(',')]
    canonical_pci=reported_pci.lower().split(':')
    if reported_uuid!=uuid or ':'.join([canonical_pci[0][-4:],*canonical_pci[1:]])!=pci:
        raise ValueError('NVML and kernel UUID/PCI disagree')
    free=int(free)
    if free<minimum_free_mib:raise ValueError(f'GPU free memory {free} MiB below frozen admission {minimum_free_mib} MiB')
    required=[f'/dev/nvidia{minor}','/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools','/dev/nvidia-modeset',
              f'/dev/dri/{cards[0]}',f'/dev/dri/{renders[0]}']
    if not all(Path(x).exists() for x in required):raise ValueError('native device nodes unavailable')
    return dict(schema='paperb-gpu-readonly-admission-v2',gpu_uuid=uuid,pci_bus_id=pci,device_minor=minor,
                drm_card=cards[0],drm_render=renders[0],free_mib=free,minimum_free_mib=minimum_free_mib,
                isolated_renderer_active_gpu=0,foreign_processes_signaled=False,global_driver_changes=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--uuid',required=True);p.add_argument('--shell-values',action='store_true')
    a=p.parse_args();m=mapping(a.uuid)
    if a.shell_values:print('\n'.join([str(m['device_minor']),m['drm_card'],m['drm_render'],m['pci_bus_id'],str(m['free_mib'])]))
    else:print(json.dumps(m,sort_keys=True))

if __name__=='__main__':main()
