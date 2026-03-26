from __future__ import annotations

from app.core.database import SessionLocal
from app.modules.cli_converter.schemas import CliOutputType
from app.modules.cli_converter.service import CliConverterService


CONFIG = '''
hostname edge-01
!
interface GigabitEthernet1
 description Uplink
 ip address 10.0.0.1 255.255.255.0
!
line vty 0 4
 login local
 transport input ssh
'''


def test_cli_converter_generates_tasks():
    with SessionLocal() as session:
        service = CliConverterService(session)
        result = service.generate(CONFIG, CliOutputType.TASKS)
        assert 'cisco.ios.ios_config' in result.generated_content
        assert any(block.kind == 'interface' for block in result.parsed.blocks)
