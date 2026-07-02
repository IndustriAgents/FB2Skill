"""Parse a deployment ``System.<resource>.opcua.xml`` (UANodeSet) offline and
resolve each skill's OPC UA interface + child variables.

We do this without connecting to a live server (PLC2Skill needs a live OPC UA
endpoint; we don't, because the deployment XML already contains the GUIDs that
the server publishes).
"""
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from .model import OpcUaNode, Skill, SkillVariable
from .state_machine import IEC_TYPE_DEFAULT
from .fbt_parser import ParsedFbt

UA_NS = "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"
UA = f"{{{UA_NS}}}"


# OPC UA alias name -> our CaSk variable-type string.
_UA_TYPE_MAP = {
    "Boolean": "bool",
    "SByte": "int", "Byte": "int",
    "Int16": "int", "UInt16": "int",
    "Int32": "int", "UInt32": "int",
    "Int64": "int", "UInt64": "int",
    "Float": "float", "Double": "float",
    "String": "string",
}


class SkillResolutionError(RuntimeError):
    pass


@dataclass
class NodeSet:
    # rt_path -> OpcUaNode (from UAVariable with RTAddress)
    variables: dict[str, OpcUaNode] = field(default_factory=dict)
    # browse_name -> OpcUaNode (from UAObject with a GUID NodeId)
    skill_objs: dict[str, OpcUaNode] = field(default_factory=dict)
    # variable rt_path -> trigger token from RTAddress (e.g. "INPUT", "SKILL_INPUT") or ""
    triggers: dict[str, str] = field(default_factory=dict)


def _parse_path_and_trigger(rta: str) -> tuple[str | None, str]:
    """Split ``V1;Path=A.B.C;Trigger=INPUT`` into (path, trigger)."""
    path = None
    trigger = ""
    for part in rta.split(";"):
        if part.startswith("Path="):
            path = part[len("Path="):]
        elif part.startswith("Trigger="):
            trigger = part[len("Trigger="):]
    return path, trigger


def _strip_browse_prefix(browse: str | None) -> str:
    """``"1:skLoad"`` -> ``"skLoad"``. Returns ``""`` for None."""
    if not browse:
        return ""
    return browse.split(":", 1)[-1]


def _guid_from_node_id(node_id: str | None) -> str | None:
    if not node_id:
        return None
    for part in node_id.split(";"):
        if part.startswith("g="):
            return part[2:]
    return None


def load_node_set(opcua_xml: Path, target_ns: int = 2) -> NodeSet:
    tree = etree.parse(str(opcua_xml))
    root = tree.getroot()
    ns = NodeSet()

    for v in root.iter(f"{UA}UAVariable"):
        rta_el = v.find(f"{UA}Extensions/{UA}Extension/RTAddress")
        if rta_el is None or not rta_el.text:
            continue
        path, trigger = _parse_path_and_trigger(rta_el.text)
        if not path:
            continue
        guid = _guid_from_node_id(v.get("NodeId"))
        if guid is None:
            continue
        browse = _strip_browse_prefix(v.get("BrowseName"))
        node = OpcUaNode(
            node_id_guid=guid,
            namespace_idx=target_ns,
            browse_name=browse,
            data_type=v.get("DataType", ""),
            rt_path=path,
        )
        ns.variables[path] = node
        ns.triggers[path] = trigger

    for o in root.iter(f"{UA}UAObject"):
        guid = _guid_from_node_id(o.get("NodeId"))
        if guid is None:
            continue
        browse = _strip_browse_prefix(o.get("BrowseName"))
        if not browse:
            continue
        ns.skill_objs[browse] = OpcUaNode(
            node_id_guid=guid,
            namespace_idx=target_ns,
            browse_name=browse,
            data_type="",
            rt_path="",
        )
    return ns


def _sk_type_for_node(n: OpcUaNode) -> str:
    return _UA_TYPE_MAP.get(n.data_type, "int")


def _default_for(sk_type: str) -> str:
    return IEC_TYPE_DEFAULT.get(sk_type, "0")


def resolve_bindings(
    parsed: ParsedFbt, ns: NodeSet, instance_names: dict[str, str] | None = None
) -> Skill:
    """Resolve the OPC UA bindings for one skill. Composite FBs with multiple
    inner SKILL_CMD nodes resolve to the shortest path (most direct child).

    The OPC UA deployment exposes an object by the *instance* name it was
    given in the FBNetwork, not by the skill's *type* name. When the type
    name isn't found directly, ``instance_names`` (type name -> instance
    name, from ``project.build_instance_name_index``) is used as a fallback.
    """
    browse_name = parsed.name
    if browse_name not in ns.skill_objs:
        alt = (instance_names or {}).get(parsed.name)
        if alt is None:
            raise SkillResolutionError(
                f"no UAObject with BrowseName={parsed.name!r} found in deployment XML, "
                f"and {parsed.name!r} is not instantiated anywhere in the project's FB networks"
            )
        if alt not in ns.skill_objs:
            raise SkillResolutionError(
                f"skill {parsed.name!r} is instantiated as {alt!r} in the project, "
                f"but no matching UAObject exists in the deployment XML"
            )
        browse_name = alt
    interface = ns.skill_objs[browse_name]

    cmd_paths = [
        p for p in ns.variables
        if f".{browse_name}." in p and p.endswith(".IThis.SKILL_CMD")
    ]
    if not cmd_paths:
        raise SkillResolutionError(
            f"no SKILL_CMD UAVariable found under skill {browse_name!r}"
        )
    primary_prefix = min(cmd_paths, key=lambda p: p.count(".")).rsplit(".", 1)[0]
    # primary_prefix = "PLC1.RES0.skLoad.Skill_Commands.IThis"

    def at(name: str) -> OpcUaNode | None:
        return ns.variables.get(f"{primary_prefix}.{name}")

    skill_cmd = at("SKILL_CMD")
    current_state = at("CURRENT_STATE")
    if skill_cmd is None or current_state is None:
        raise SkillResolutionError(
            f"skill {parsed.name!r} missing SKILL_CMD/CURRENT_STATE under {primary_prefix}"
        )

    parameters: list[SkillVariable] = []
    outputs: list[SkillVariable] = []
    # Find every UAVariable under this IThis (excluding SKILL_CMD/CURRENT_STATE).
    prefix_dot = primary_prefix + "."
    for path, node in ns.variables.items():
        if not path.startswith(prefix_dot):
            continue
        tail = path[len(prefix_dot):]
        if "." in tail:
            continue  # only direct children of IThis
        if tail in ("SKILL_CMD", "CURRENT_STATE"):
            continue
        sk_type = _sk_type_for_node(node)
        trigger = ns.triggers.get(path, "")
        direction = "input" if trigger == "INPUT" else "output"
        var = SkillVariable(
            name=tail,
            direction=direction,
            iec_type=node.data_type,
            sk_type=sk_type,
            default=_default_for(sk_type),
            required=False,
            opcua=node,
        )
        if direction == "input":
            parameters.append(var)
        else:
            outputs.append(var)

    # Stable ordering: input/output name sorted alphabetically (IN1, IN2, …, OUT1, OUT2, …).
    parameters.sort(key=lambda v: v.name)
    outputs.sort(key=lambda v: v.name)

    return Skill(
        name=parsed.name,
        fbt_path=parsed.fbt_path,
        interface_node=interface,
        skill_command=skill_cmd,
        current_state=current_state,
        parameters=parameters,
        outputs=outputs,
    )
