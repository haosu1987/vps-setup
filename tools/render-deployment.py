#!/usr/bin/env python3
"""Render public templates into a private, new deployment workspace. No activation."""
import argparse
import hashlib
import ipaddress
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PORTS={'SSH_PORT','PROXY_PORT','PANEL_PORT','SUBSCRIPTION_PORT','HTTPS_PORT'}
LEGACY_PORTS={'SOCKS_PORT','DNS_PORT'}
IPV4={'SERVER_IPV4'}
LEGACY_IPV4={'LAN_GATEWAY_IPV4','LAN_DNS_IPV4'}
PATHS={'PROJECT_DIR','BACKUP_ROOT','XUI_INSTALL_DIR','XUI_DATA_DIR','XUI_LOG_DIR'}
LEGACY_PATHS={'MAC_WORK_DIR','MAC_STATE_DIR'}
NAMES={'SSH_USER'}
LEGACY_NAMES={'MAC_INTERFACE','MAC_NETWORK_SERVICE','TUN_NAME'}
HOSTS={'REALITY_SERVER_NAME','REALITY_TARGET_HOST'}
KEYS=PORTS|IPV4|PATHS|NAMES|HOSTS
LEGACY_KEYS=LEGACY_PORTS|LEGACY_IPV4|LEGACY_PATHS|LEGACY_NAMES|{'TUN_GATEWAY_CIDR'}
TOKEN=re.compile(r'@@([A-Z][A-Z0-9_]*)@@')
VENDOR_URL='https://raw.githubusercontent.com/MHSanaei/3x-ui/v3.11.0/install.sh'
VENDOR_SHA256='9684bae4f769b2127fcceceb4f200045657381311867529e6ba76c6b58e2825d'


def validate(profile):
    if not isinstance(profile,dict) or not KEYS <= set(profile) or set(profile) - (KEYS | LEGACY_KEYS):
        raise ValueError('Private deployment profile has missing or unknown keys')
    for key in (PORTS | LEGACY_PORTS) & profile.keys():
        if type(profile[key]) is not int or not 1<=profile[key]<=65535:
            raise ValueError('Port values must be integer inputs, not placeholders')
    for key in (IPV4 | LEGACY_IPV4) & profile.keys():
        ipaddress.IPv4Address(profile[key])
    if 'TUN_GATEWAY_CIDR' in profile:
        ipaddress.IPv4Interface(profile['TUN_GATEWAY_CIDR'])
    # Deliberately narrow interpolation alphabet: templates contain shell,
    # Python and JSON. Never accept quotes, newlines, expansions or code.
    for key in (PATHS | LEGACY_PATHS) & profile.keys():
        value=profile[key]
        if not isinstance(value,str) or not re.fullmatch(r'/[A-Za-z0-9_./-]+',value) or '..' in Path(value).parts:
            raise ValueError('Paths must be absolute safe POSIX paths without parent traversal')
    for key in (NAMES | LEGACY_NAMES) & profile.keys():
        if not isinstance(profile[key],str) or not re.fullmatch(r'[A-Za-z0-9_-]+',profile[key]):
            raise ValueError('User/interface/service names require simple safe identifiers')
    for key in HOSTS:
        if not isinstance(profile[key],str) or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?',profile[key]) or '..' in profile[key]:
            raise ValueError('REALITY names require safe DNS host names')
    values={k:str(v) for k,v in profile.items()}
    values['SSH_TARGET']=profile['SSH_USER']+'@'+profile['SERVER_IPV4']
    return values


def render(profile_path, output, fetch_vendor=False):
    os.umask(0o077)
    profile_path=Path(profile_path)
    if profile_path.is_symlink() or profile_path.stat().st_mode & 0o077:
        raise ValueError('Private profile must be a regular file with mode 0600 or stricter')
    values=validate(json.loads(profile_path.read_text()))
    base=ROOT/'.private'
    base.mkdir(mode=0o700,exist_ok=True)
    if base.is_symlink() or base.stat().st_mode & 0o077:
        raise ValueError('Private output root must be protected and cannot be a symlink')
    output=Path(output).absolute()
    if not output.resolve().is_relative_to(base.resolve()) or output.exists() or output.is_symlink():
        raise ValueError('Output must be a new directory inside this checkout private root')
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    values['OUTPUT_DIR']=str(output)
    try:
        for source in sorted((ROOT/'templates').rglob('*.in')):
            if source.is_symlink():raise ValueError('Template symlinks are not accepted')
            text=source.read_text()
            text=TOKEN.sub(lambda m:values[m[1]],text)
            if '@@' in text:raise ValueError('Unresolved template marker')
            dest=output/source.relative_to(ROOT/'templates')
            dest=dest.with_name(dest.name[:-3]);dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(text);dest.chmod(0o600)
            if dest.suffix=='.json':json.loads(text)
            if dest.suffix=='.sh':
                result=subprocess.run(['bash','-n',str(dest)],capture_output=True)
                if result.returncode:raise ValueError('Rendered shell syntax validation failed')
            if dest.suffix=='.py':compile(text,str(dest),'exec')
        portable=['proxyctl.sh','proxy-measure.sh','proxy-report.sh','proxy-targets.tsv']
        scripts=output/'scripts/proxy'
        (scripts/'toolset.sha256').write_text(''.join(hashlib.sha256((scripts/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in portable))
        if fetch_vendor:
            with urllib.request.urlopen(VENDOR_URL,timeout=30) as response:data=response.read(1024*1024+1)
            if len(data)>1024*1024 or hashlib.sha256(data).hexdigest()!=VENDOR_SHA256:
                raise ValueError('Pinned installer validation failed')
            dest=output/'scripts/proxy/vendor/3x-ui-v3.11.0-install.sh'
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);dest.chmod(0o600)
        print('Private workspace rendered and syntax checked; network settings unchanged.')
    except Exception:
        # Preserve a bounded marker, not confidential generated error text.
        (output/'RENDER_FAILED').write_text('Do not activate this incomplete workspace.\n')
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--fetch-vendor',action='store_true',help='Fetch and verify the pinned installer into private output')
    args=p.parse_args()
    try:render(args.profile,args.output,args.fetch_vendor)
    except Exception:
        print('Render failed; details suppressed to protect deployment values. Check profile permissions, required fields and new private output directory.',file=sys.stderr)
        sys.exit(1)
