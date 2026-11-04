#!/usr/bin/env python3
"""Scan staged content and publishable branch history without printing private values."""
import argparse
import json
import ipaddress
import re
import subprocess
import sys
from pathlib import Path


def git(*args):return subprocess.check_output(['git',*args])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',required=True)
    parser.add_argument('--history',default='HEAD',help='Only the branch history that will be published')
    parser.add_argument('--worktree',action='store_true',help='Also scan current tracked and non-ignored untracked files')
    args=parser.parse_args()
    profile_path=Path(args.profile)
    if profile_path.is_symlink() or profile_path.stat().st_mode & 0o077:raise ValueError('Unsafe private input')
    profile=json.loads(profile_path.read_text())
    rules=[]
    for key,value in profile.items():
        value=str(value)
        if key.endswith('_PORT'):
            pattern=rb'(?<![A-Za-z0-9])'+re.escape(value.encode())+rb'(?![A-Za-z0-9])'
        else:pattern=re.escape(value.encode())
        rules.append((key,re.compile(pattern)))
    if 'TUN_GATEWAY_CIDR' in profile:
        rules.append(('TUN_GATEWAY_IPV4',re.compile(re.escape(str(ipaddress.IPv4Interface(profile['TUN_GATEWAY_CIDR']).ip).encode()))))
    deny=profile_path.parent/'privacy-denylist.json'
    if deny.exists():
        if deny.is_symlink() or deny.stat().st_mode & 0o077:raise ValueError('Unsafe private denylist')
        for index,value in enumerate(json.loads(deny.read_text())):
            rules.append((f'PRIVATE_EXTRA_{index}',re.compile(re.escape(value.encode()))))
    client=profile_path.parent/'mac-xray-initial.json'
    if client.exists():
        if client.is_symlink() or client.stat().st_mode & 0o077:raise ValueError('Unsafe client input')
        config=json.loads(client.read_text())
        node=next(o for o in config['outbounds'] if o.get('tag')=='proxy')
        reality=node['streamSettings']['realitySettings']
        values={'CLIENT_ID':node['settings']['vnext'][0]['users'][0]['id'],
                'CLIENT_PUBLIC_KEY':reality['publicKey'],'CLIENT_SHORT_ID':reality['shortId']}
        for key,value in values.items():
            if value:rules.append((key,re.compile(re.escape(value.encode()))))
    findings=[]
    files=git('ls-files','-z').split(b'\0')
    for raw in files:
        if not raw:continue
        name=raw.decode()
        if name.startswith(('.private/','scripts/','deploy/')) or name.endswith(('.bundle','.local.json')):
            findings.append(('excluded-output-path',name));continue
        content=git('show',':'+name)
        for key,pattern in rules:
            if pattern.search(content):findings.append((key,name))
        if re.search(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',content):findings.append(('private-key',name))
    if args.worktree:
        working=set(git('ls-files','--cached','--others','--exclude-standard','-z').split(b'\0'))
        for raw in working:
            if not raw:continue
            name=raw.decode()
            path=Path(name)
            if path.is_symlink():
                findings.append(('worktree-symlink',name));continue
            if not path.is_file():continue
            content=path.read_bytes()
            for key,pattern in rules:
                if pattern.search(content):findings.append((key,name))
            if re.search(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',content):findings.append(('private-key',name))
    # Rooted history only: local incident backups must never become push refs.
    commits=git('rev-list',args.history).decode().splitlines()
    seen=set()
    for commit in commits:
        meta=git('show','-s','--format=%B%n%an%n%ae',commit)
        for key,pattern in rules:
            if pattern.search(meta):findings.append((key,'commit-metadata'))
        for row in git('ls-tree','-r',commit).splitlines():
            fields=row.split(None,3)
            if len(fields)<4:continue
            object_id=fields[2].decode()
            if object_id in seen:continue
            seen.add(object_id)
            data=git('cat-file','blob',object_id)
            for key,pattern in rules:
                if pattern.search(data):findings.append((key,'reachable-history-blob'))
    if findings:
        for key,path in sorted(set(findings)):print('BLOCK:',key,path)
        return 1
    print('PASS: staged tree, selected history'+(' and worktree' if args.worktree else '')+' contain no configured deployment identifiers.')
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        print('Public-tree check failed; no private input values were printed.',file=sys.stderr);sys.exit(1)
