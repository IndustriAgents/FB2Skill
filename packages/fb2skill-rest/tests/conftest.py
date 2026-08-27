import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fb2skill_rest.app import create_app

FESTO_ROOT = Path("D:/FESTO_DS_skills/IEC61499")
EXEMPLARS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "fb2skill-core" / "tests" / "exemplars"
)


def _have_festo() -> bool:
    return FESTO_ROOT.is_dir() and (FESTO_ROOT / "bin/Deploy").exists()


requires_festo = pytest.mark.skipif(
    not _have_festo(),
    reason="FESTO_DS_skills project not available at D:\\FESTO_DS_skills",
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def exemplars_dir() -> Path:
    return EXEMPLARS_DIR


@pytest.fixture
def festo_zip() -> bytes:
    """Pack D:/FESTO_DS_skills/IEC61499 into an in-memory zip with top-level dir IEC61499/."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in FESTO_ROOT.rglob("*"):
            if not p.is_file():
                continue
            arcname = Path("IEC61499") / p.relative_to(FESTO_ROOT)
            zf.write(p, arcname.as_posix())
    return buf.getvalue()


_DEMO_FBT = """<?xml version="1.0" encoding="UTF-8"?>
<FBType Name="skDemo">
  <InterfaceList>
    <InputVars><VarDeclaration Name="Speed" Type="REAL"/></InputVars>
    <OutputVars><VarDeclaration Name="Done" Type="BOOL"/></OutputVars>
  </InterfaceList>
  <FBNetwork><FB Name="Skill_Commands" Type="BasicSKILL"/></FBNetwork>
</FBType>
"""

_DEMO_OPCUA_XML = """<?xml version="1.0" encoding="utf-8"?>
<UANodeSet xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd">
  <UAObject NodeId="ns=1;g=11111111-1111-1111-1111-111111111111" BrowseName="1:skDemo"/>
  <UAVariable NodeId="ns=1;g=22222222-2222-2222-2222-222222222222" BrowseName="1:SKILL_CMD" DataType="Int32">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.SKILL_CMD;Trigger=INPUT</RTAddress></Extension></Extensions>
  </UAVariable>
  <UAVariable NodeId="ns=1;g=33333333-3333-3333-3333-333333333333" BrowseName="1:CURRENT_STATE" DataType="Int32">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.CURRENT_STATE</RTAddress></Extension></Extensions>
  </UAVariable>
  <UAVariable NodeId="ns=1;g=44444444-4444-4444-4444-444444444444" BrowseName="1:Speed" DataType="Float">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.Speed;Trigger=INPUT</RTAddress></Extension></Extensions>
  </UAVariable>
  <UAVariable NodeId="ns=1;g=55555555-5555-5555-5555-555555555555" BrowseName="1:Done" DataType="Boolean">
    <Extensions><Extension><RTAddress xmlns="">V1;Path=PLC1.RES0.skDemo.Skill_Commands.IThis.Done</RTAddress></Extension></Extensions>
  </UAVariable>
</UANodeSet>
"""


@pytest.fixture
def demo_zip() -> bytes:
    """Minimal synthetic project: one BasicSKILL fbt + deployment OPC UA XML."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("DemoProj/skDemo.fbt", _DEMO_FBT)
        zf.writestr("DemoProj/bin/Deploy/PLC1/System.demo.opcua.xml", _DEMO_OPCUA_XML)
    return buf.getvalue()
