#!/usr/bin/env bash
set -euo pipefail
probe_root=/data/liyufeng/paperb_signed_force_calibration_20261015_v3
chem_root=/mnt/nas/data/safelab/retreat/lyf-back/chembench
capsule=/tmp/chemrm-papera-v15/pilot/paperA/driver_library_isolation_v54_20261011/capsule_r2
local_sdk=/home/liyufeng/miniforge3/envs/safeduo
export LD_LIBRARY_PATH="$capsule"
export LD_PRELOAD="$local_sdk/lib/libstdc++.so.6"
gpu_uuid=${2:?explicit GPU UUID}
mapfile -t gpu_mapping < <(python3 "$probe_root/gpu_mapping.py" --uuid "$gpu_uuid" --shell-values)
if (( ${#gpu_mapping[@]} != 5 )); then printf 'GPU resource and mapping gate blocked\n'; exit 42; fi
gpu_minor=${gpu_mapping[0]}
gpu_card=${gpu_mapping[1]}
gpu_render=${gpu_mapping[2]}
runtime_local=/tmp/paperb-signed-force-calibration-runtime-v3-${gpu_uuid#GPU-}
mkdir -p "$runtime_local/"{tmp,cache,config,data,kit,omni,torch,cuda,driver}
exec bwrap --die-with-parent --ro-bind / / --tmpfs /home --ro-bind /home/liyufeng /home/liyufeng \
 --bind "$probe_root" "$probe_root" --bind "$runtime_local" "$probe_root/runtime" --ro-bind "$capsule" "$probe_root/runtime/driver" \
 --bind "$runtime_local/tmp" /tmp --bind "$runtime_local/tmp" /var/tmp \
 --dev /dev --dev-bind "/dev/nvidia$gpu_minor" "/dev/nvidia$gpu_minor" --dev-bind /dev/nvidiactl /dev/nvidiactl \
 --dev-bind /dev/nvidia-uvm /dev/nvidia-uvm --dev-bind /dev/nvidia-uvm-tools /dev/nvidia-uvm-tools \
 --dev-bind /dev/nvidia-modeset /dev/nvidia-modeset --dir /dev/dri \
 --dev-bind "/dev/dri/$gpu_card" "/dev/dri/$gpu_card" --dev-bind "/dev/dri/$gpu_render" "/dev/dri/$gpu_render" --proc /proc \
 --bind "$runtime_local/omni" /home/liyufeng/.nvidia-omniverse --chdir "$probe_root" -- \
 env -u CUDA_VISIBLE_DEVICES -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy \
 LD_LIBRARY_PATH="$probe_root/runtime/driver" LD_PRELOAD="$local_sdk/lib/libstdc++.so.6" \
 CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_MPS_PIPE_DIRECTORY=/tmp/paperb-signed-force-calibration-no-mps-v3 PYTHONDONTWRITEBYTECODE=1 \
 PYTHONPATH="$probe_root/code:/home/liyufeng/safeduo_isaaclab/source/isaaclab" \
 ISAAC_PATH="$local_sdk/lib/python3.11/site-packages/isaacsim" TERM=xterm OMNI_KIT_ACCEPT_EULA=YES PRIVACY_CONSENT=Y \
 XDG_CACHE_HOME="$probe_root/runtime/cache" XDG_CONFIG_HOME="$probe_root/runtime/config" XDG_DATA_HOME="$probe_root/runtime/data" \
 TMPDIR="$probe_root/runtime/tmp" TORCH_EXTENSIONS_DIR="$probe_root/runtime/torch" CUDA_CACHE_PATH="$probe_root/runtime/cuda" \
 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
 "$local_sdk/bin/python" -u "$probe_root/native_probe.py" --headless --device cpu \
 --experience /home/liyufeng/safeduo_isaaclab/apps/isaaclab.python.headless.rendering.kit \
 --kit_args "--portable --portable-root $probe_root/runtime/kit --/renderer/multiGpu/enabled=false --/renderer/multiGpu/autoEnable=false --/renderer/activeGpu=0 --/plugins/carb.tasking.plugin/threadCount=8" \
 --case "${1:?case}" --root "$probe_root"
