"""Jinja2 rendering of one Skill into a TTL document."""
from jinja2 import Environment, PackageLoader, StrictUndefined

from .config import RenderConfig
from .model import Skill
from . import state_machine as sm


_ENV = Environment(
    loader=PackageLoader("fb2skill_core", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    undefined=StrictUndefined,
)


def render_skill(skill: Skill, config: RenderConfig) -> str:
    template = _ENV.get_template(f"{config.ontology}/skill.ttl.j2")
    return template.render(
        skill=skill,
        config=config,
        states=sm.STATES,
        commands=sm.COMMANDS,
        state_code=sm.STATE_CODE,
        command_code=sm.COMMAND_CODE,
        auto_transition_states=sm.AUTO_TRANSITION_STATES,
        command_target=sm.COMMAND_TARGET,
        auto_target=sm.AUTO_TARGET,
        state_outgoing=sm.STATE_OUTGOING,
        sk_type_xsd=sm.SK_TYPE_XSD,
    )
