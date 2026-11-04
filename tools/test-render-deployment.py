#!/usr/bin/env python3
"""Synthetic privacy/render checks. Never load a real deployment profile."""
import copy
import importlib.util
import json
import re
import shutil
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('renderer',ROOT/'tools/render-deployment.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
profile={
 'SERVER_IPV4':'203.0.113.17','SSH_USER':'exampleuser','PROJECT_DIR':'/srv/example/project',
 'BACKUP_ROOT':'/opt/example/backups',
 'XUI_INSTALL_DIR':'/opt/example/panel','XUI_DATA_DIR':'/opt/example/data','XUI_LOG_DIR':'/opt/example/logs',
 'REALITY_SERVER_NAME':'sni.example.org','REALITY_TARGET_HOST':'target.example.org'
}
for index,key in enumerate(sorted(module.PORTS)):profile[key]=24000+index
assert set(profile)==module.KEYS
base=ROOT/'.private';base.mkdir(mode=0o700,exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='render-test-',dir=base));stage.chmod(0o700)
try:
 source=stage/'profile.json';source.write_text(json.dumps(profile));source.chmod(0o600)
 output=stage/'generated';module.render(source,output)
 for template in (ROOT/'templates').rglob('*.in'):
  target=output/template.relative_to(ROOT/'templates');target=target.with_name(target.name[:-3])
  text=target.read_text();assert '@@' not in text
  assert target.stat().st_mode & 0o077 == 0
  sha=re.compile(r'\b[0-9a-f]{64}\b')
  assert set(sha.findall(template.read_text()))==set(sha.findall(text)), 'Immutable hash was changed by parameter substitution'
 manifest=output/'scripts/proxy/toolset.sha256'
 assert {line.split()[1] for line in manifest.read_text().splitlines()} == {'proxyctl.sh','proxy-measure.sh','proxy-report.sh','proxy-targets.tsv'}
 legacy=dict(profile,SOCKS_PORT=25001,DNS_PORT=25002,LAN_GATEWAY_IPV4='192.0.2.9',LAN_DNS_IPV4='192.0.2.10',MAC_INTERFACE='en9',MAC_NETWORK_SERVICE='ExampleNetwork',TUN_NAME='utun99',TUN_GATEWAY_CIDR='192.0.2.13/30',MAC_WORK_DIR='/opt/example/client',MAC_STATE_DIR='/opt/example/state')
 assert set(legacy)==module.KEYS|module.LEGACY_KEYS
 source.write_text(json.dumps(legacy));module.render(source,stage/'legacy')
 for target in output.rglob('*'):
  if target.is_file():assert target.read_text().replace(str(output.absolute()),'<OUTPUT>')==(stage/'legacy'/target.relative_to(output)).read_text().replace(str((stage/'legacy').absolute()),'<OUTPUT>'), 'Legacy fields affected server output'
 source.write_text(json.dumps(profile))
 print('PASS: server-only manifest and legacy profile compatibility')
 print('PASS: synthetic profile rendering, protected modes, immutable hashes and source syntax')
 for key,value in [('PROJECT_DIR','/tmp/$(id)'),('SSH_USER','user;id'),('PROXY_PORT',True),('REALITY_SERVER_NAME','host\ncommand'),('MAC_WORK_DIR','/tmp/$(id)'),('UNKNOWN_FIELD','value')]:
  bad=copy.deepcopy(profile);bad[key]=value
  try:module.validate(bad)
  except ValueError:pass
  else:raise AssertionError('Unsafe interpolation accepted')
 print('PASS: executable/special input and invalid ports rejected')
 source.chmod(0o644)
 try:module.render(source,stage/'unsafe-mode')
 except ValueError:pass
 else:raise AssertionError('World-readable input accepted')
 source.chmod(0o600)
 try:module.render(source,ROOT/'unexpected-generated-output')
 except ValueError:pass
 else:raise AssertionError('Public output accepted')
 try:module.render(source,output)
 except ValueError:pass
 else:raise AssertionError('Existing effective directory overwritten')
 print('PASS: public permissions, public output and overwrites rejected')

finally:shutil.rmtree(stage)
