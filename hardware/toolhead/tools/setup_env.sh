#!/usr/bin/env bash
# =============================================================================
# K1 toolhead CAD + CFD toolchain - idempotent environment setup (Ubuntu 24.04 x86_64, root)
#
#   sudo bash setup_env.sh [--with-cadquery] [--with-freecad] [--skip-apt] [--check]
#
# Installs / verifies:
#   * apt:   gmsh 4.12, openscad 2021.01, xvfb + Mesa/OSMesa (offscreen rendering), build tools
#   * OpenFOAM v2512 (ESI / openfoam.com), Debian packages 2512.0-2 downloaded from the official
#            OpenFOAM SourceForge mirror of the openfoam.com apt repository. Each .deb is
#            SHA256-pinned below (hashes taken from the repo's Packages index, which is itself
#            hashed in the signed InRelease). NB: dl.openfoam.com (the repo key) was not reachable
#            from the build container, so the GPG signature was NOT verified - integrity rests on
#            TLS to sourceforge.net + the pinned hashes.  Includes snappyHexMesh, cfMesh
#            (cartesianMesh), scotch decomposition, fanPressure BC.
#   * Python 3.13 venv /opt/k1th/venv (uv): build123d 0.13 (OCP 8.0), trimesh, lib3mf, pyvista/vtk,
#            matplotlib, numpy, scipy, gmsh (pip), meshio - exact pins in requirements-k1th.lock.txt
#   * optional: /opt/k1th/venv-cq   CadQuery 2.7 (needs OCP 7.8 -> separate venv, conflicts with build123d)
#   * optional: /opt/k1th/freecad   FreeCAD 1.0.2 AppImage (extracted; headless: freecadcmd)
#
# Do NOT use Ubuntu's own `openfoam` package (v1912): its function objects crash with
# 'error in IOstream "sha1"' and its scotch decomposition is a dummy stub. This script removes it.
#
# Afterwards:  source /opt/k1th/env.sh   (sets K1_PY, FOAM_BASHRC, aliases)
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX=/opt/k1th
VENV=$PREFIX/venv
OF_VER=2512
OF_DEB_VER=2512.0-2
OF_BASE="https://downloads.sourceforge.net/project/openfoam/repos/deb/dists/noble/main/pool/2512_0"
declare -A OF_SHA=(
  [openfoam2512_2512.0-2_amd64.deb]=c59e65ffd99c9143fd7c2594dc9776e9d7190124965efdb667e28677d93f3fed
  [openfoam2512-common_2512.0-2_all.deb]=f438ecbfaff0248b9273502f3b43a6cb1b4f81c07224dbda811f1b48d989026f
  [openfoam2512-tools_2512.0-2_amd64.deb]=fc0d19c1152819cc7d2a6165eec911c0f1ea3ab7d88cc04ee4a8070d11aa2e62
  [openfoam2512-tutorials_2512.0-2_all.deb]=4c87494c17a1381853af8a828e8df3a741d9cde5e06bb0212f3fc6940d889473
)
FREECAD_URL="https://github.com/FreeCAD/FreeCAD/releases/download/1.0.2/FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage"
FREECAD_SHA=e00be00ad9fdb12b05c5002bfd1aa2ea8126f2c1d4e2fb603eb7423b72904f61

WITH_CQ=0; WITH_FC=0; SKIP_APT=0; CHECK_ONLY=0
for a in "$@"; do
  case $a in
    --with-cadquery) WITH_CQ=1 ;;
    --with-freecad)  WITH_FC=1 ;;
    --skip-apt)      SKIP_APT=1 ;;
    --check)         CHECK_ONLY=1 ;;
    *) echo "unknown option $a"; exit 2 ;;
  esac
done
log() { printf '\n==> %s\n' "$*"; }
export DEBIAN_FRONTEND=noninteractive
mkdir -p $PREFIX

# ----------------------------------------------------------------------------- apt
if [[ $CHECK_ONLY == 0 && $SKIP_APT == 0 ]]; then
  log "apt packages"
  apt-get update -qq
  apt-get install -y -qq --no-install-recommends \
    ca-certificates curl gnupg xz-utils \
    gmsh openscad xvfb libgl1 libglu1-mesa libosmesa6 libxrender1 libxcursor1 libxft2 libxinerama1 \
    >/dev/null
  if dpkg -s openfoam >/dev/null 2>&1 || dpkg -s libopenfoam >/dev/null 2>&1; then
    log "removing Ubuntu openfoam v1912 (broken function objects, dummy scotch)"
    apt-get purge -y -qq openfoam libopenfoam >/dev/null
  fi
fi

# ----------------------------------------------------------------------------- OpenFOAM v2512
if [[ $CHECK_ONLY == 0 ]] && ! dpkg -s openfoam${OF_VER} 2>/dev/null | grep -q "Version: ${OF_DEB_VER}"; then
  log "OpenFOAM v${OF_VER} (${OF_DEB_VER})"
  D=$(mktemp -d)
  for f in "${!OF_SHA[@]}"; do
    case $f in *_all.deb) url="$OF_BASE/binary-all/$f" ;; *) url="$OF_BASE/binary-amd64/$f" ;; esac
    curl -fsSL -o "$D/$f" "$url"
    echo "${OF_SHA[$f]}  $D/$f" | sha256sum -c --quiet -
  done
  apt-get install -y -qq --no-install-recommends "$D"/*.deb >/dev/null
  rm -rf "$D"
fi

# ----------------------------------------------------------------------------- Python venv
if [[ $CHECK_ONLY == 0 ]]; then
  if ! command -v uv >/dev/null; then
    log "installing uv"
    python3 -m pip install --quiet --user --break-system-packages uv==0.11.32 || \
      python3 -m pip install --quiet --break-system-packages uv==0.11.32
    export PATH="$HOME/.local/bin:$PATH"
  fi
  if [[ ! -x $VENV/bin/python ]]; then
    log "creating $VENV"
    uv venv -q --python 3.13 $VENV
  fi
  log "syncing $VENV from requirements-k1th.lock.txt"
  uv pip sync -q --python $VENV/bin/python "$HERE/requirements-k1th.lock.txt"
  if [[ $WITH_CQ == 1 ]]; then
    [[ -x $PREFIX/venv-cq/bin/python ]] || uv venv -q --python 3.13 $PREFIX/venv-cq
    uv pip sync -q --python $PREFIX/venv-cq/bin/python "$HERE/requirements-k1th-cq.lock.txt"
  fi
  if [[ $WITH_FC == 1 && ! -x $PREFIX/freecad/squashfs-root/usr/bin/freecadcmd ]]; then
    log "FreeCAD 1.0.2 AppImage (~800 MB)"
    D=$(mktemp -d)
    curl -fsSL -o "$D/FreeCAD.AppImage" "$FREECAD_URL"
    echo "$FREECAD_SHA  $D/FreeCAD.AppImage" | sha256sum -c --quiet -
    chmod +x "$D/FreeCAD.AppImage"
    mkdir -p $PREFIX/freecad && (cd $PREFIX/freecad && "$D/FreeCAD.AppImage" --appimage-extract >/dev/null)
    rm -rf "$D"
  fi
fi

# ----------------------------------------------------------------------------- env file
cat > $PREFIX/env.sh <<EOF
# source me: K1 toolhead toolchain
export K1_PY=$VENV/bin/python
export FOAM_BASHRC=/usr/lib/openfoam/openfoam${OF_VER}/etc/bashrc
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
alias of${OF_VER}='source \$FOAM_BASHRC'
[[ -x $PREFIX/freecad/squashfs-root/usr/bin/freecadcmd ]] && alias freecadcmd=$PREFIX/freecad/squashfs-root/usr/bin/freecadcmd
EOF

# ----------------------------------------------------------------------------- checks
log "verification"
fail=0
chk() { if eval "$2" >/dev/null 2>&1; then echo "  [ok]   $1"; else echo "  [FAIL] $1"; fail=1; fi; }
chk "OpenFOAM v${OF_VER} simpleFoam"   "bash -c 'source /usr/lib/openfoam/openfoam${OF_VER}/etc/bashrc && simpleFoam -help'"
chk "OpenFOAM scotch decomposition"    "bash -c 'source /usr/lib/openfoam/openfoam${OF_VER}/etc/bashrc && foamHasLibrary scotchDecomp'"
chk "OpenFOAM fanPressure BC"          "bash -c 'source /usr/lib/openfoam/openfoam${OF_VER}/etc/bashrc && strings \$FOAM_LIBBIN/libfiniteVolume.so | grep -qx fanPressure'"
chk "cfMesh cartesianMesh"             "bash -c 'source /usr/lib/openfoam/openfoam${OF_VER}/etc/bashrc && command -v cartesianMesh'"
chk "gmsh (apt)"                       "gmsh --version"
chk "openscad (apt)"                   "openscad --version"
chk "python stack imports"             "$VENV/bin/python -c 'import build123d, trimesh, lib3mf, pyvista, vtk, gmsh, matplotlib, scipy'"
chk "CAD self-test (STEP/STL/3MF/booleans)" "$VENV/bin/python $HERE/cad_selftest.py $(mktemp -d)"
chk "pyvista offscreen render"         "$VENV/bin/python -c 'import pyvista as pv; p=pv.Plotter(off_screen=True); p.add_mesh(pv.Sphere()); p.screenshot(\"$(mktemp -u).png\")'"
[[ -x $PREFIX/venv-cq/bin/python ]] && chk "CadQuery venv" "$PREFIX/venv-cq/bin/python -c 'import cadquery'"
[[ -x $PREFIX/freecad/squashfs-root/usr/bin/freecadcmd ]] && chk "FreeCAD freecadcmd" "echo 'import FreeCAD' > /tmp/_fc.py && $PREFIX/freecad/squashfs-root/usr/bin/freecadcmd /tmp/_fc.py"
echo
[[ $fail == 0 ]] && echo "All checks passed. source $PREFIX/env.sh" || { echo "Some checks FAILED"; exit 1; }
