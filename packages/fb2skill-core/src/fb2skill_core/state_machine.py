"""Static ISA-88 / PackML state machine tables.

State and command names and their integer codes are fixed by the BasicSKILL
function block; reproducing the values is what makes the rendered TTL match
the hand-written exemplars.
"""

# Ordered: int code = index + 1.
STATES: tuple[str, ...] = (
    "Idle",
    "Starting",
    "Execute",
    "Completing",
    "Complete",
    "Resetting",
    "Holding",
    "Held",
    "Unholding",
    "Suspending",
    "Suspended",
    "Unsuspending",
    "Stopping",
    "Stopped",
    "Aborting",
    "Aborted",
    "Clearing",
)
STATE_CODE: dict[str, int] = {name: i + 1 for i, name in enumerate(STATES)}

# Ordered: int code = index + 1.
COMMANDS: tuple[str, ...] = (
    "Start",
    "Reset",
    "Hold",
    "Unhold",
    "Suspend",
    "Unsuspend",
    "Clear",
    "Stop",
    "Abort",
)
COMMAND_CODE: dict[str, int] = {name: i + 1 for i, name in enumerate(COMMANDS)}

# Auto-transitions (each state that emits a "<State>_State_Complete" transition).
AUTO_TRANSITION_STATES: tuple[str, ...] = (
    "Starting",
    "Execute",
    "Completing",
    "Holding",
    "Unholding",
    "Suspending",
    "Unsuspending",
    "Resetting",
    "Stopping",
    "Clearing",
    "Aborting",
)

# Transition (command) -> target state.
COMMAND_TARGET: dict[str, str] = {
    "StartCommand": "Starting",
    "ResetCommand": "Resetting",
    "HoldCommand": "Holding",
    "UnholdCommand": "Unholding",
    "SuspendCommand": "Suspending",
    "UnsuspendCommand": "Unsuspending",
    "ClearCommand": "Clearing",
    "StopCommand": "Stopping",
    "AbortCommand": "Aborting",
}

# Auto-transition (state_complete) -> target state.
AUTO_TARGET: dict[str, str] = {
    "Starting_State_Complete": "Execute",
    "Execute_State_Complete": "Completing",
    "Completing_State_Complete": "Complete",
    "Holding_State_Complete": "Held",
    "Unholding_State_Complete": "Execute",
    "Suspending_State_Complete": "Suspended",
    "Unsuspending_State_Complete": "Execute",
    "Resetting_State_Complete": "Idle",
    "Stopping_State_Complete": "Stopped",
    "Clearing_State_Complete": "Stopped",
    "Aborting_State_Complete": "Aborted",
}

# State -> outgoing transitions, in the order they appear in the exemplars.
STATE_OUTGOING: dict[str, tuple[str, ...]] = {
    "Idle":         ("StartCommand", "StopCommand", "AbortCommand"),
    "Starting":     ("Starting_State_Complete", "StopCommand", "AbortCommand"),
    "Execute":      ("Execute_State_Complete", "HoldCommand", "SuspendCommand", "StopCommand", "AbortCommand"),
    "Completing":   ("Completing_State_Complete", "StopCommand", "AbortCommand"),
    "Complete":     ("ResetCommand", "StopCommand", "AbortCommand"),
    "Resetting":    ("Resetting_State_Complete", "StopCommand", "AbortCommand"),
    "Holding":      ("Holding_State_Complete", "StopCommand", "AbortCommand"),
    "Held":         ("UnholdCommand", "StopCommand", "AbortCommand"),
    "Unholding":    ("Unholding_State_Complete", "StopCommand", "AbortCommand"),
    "Suspending":   ("Suspending_State_Complete", "StopCommand", "AbortCommand"),
    "Suspended":    ("UnsuspendCommand", "StopCommand", "AbortCommand"),
    "Unsuspending": ("Unsuspending_State_Complete", "StopCommand", "AbortCommand"),
    "Stopping":     ("Stopping_State_Complete", "AbortCommand"),
    "Stopped":      ("ResetCommand", "AbortCommand"),
    "Aborting":     ("Aborting_State_Complete",),
    "Aborted":      ("ClearCommand",),
    "Clearing":     ("Clearing_State_Complete", "AbortCommand"),
}

# IEC 61499 type -> CaSk skill-variable type.
IEC_TYPE_MAP: dict[str, str] = {
    "INT":    "int",
    "UINT":   "int",
    "SINT":   "int",
    "USINT":  "int",
    "DINT":   "int",
    "UDINT":  "int",
    "LINT":   "int",
    "ULINT":  "int",
    "WORD":   "int",
    "DWORD":  "int",
    "REAL":   "float",
    "LREAL":  "float",
    "BOOL":   "bool",
    "STRING": "string",
    "WSTRING": "string",
}

# Normalized sk_type -> XSD datatype IRI (for MAESTRO skill:paramType).
SK_TYPE_XSD: dict[str, str] = {
    "int": "http://www.w3.org/2001/XMLSchema#integer",
    "float": "http://www.w3.org/2001/XMLSchema#double",
    "bool": "http://www.w3.org/2001/XMLSchema#boolean",
    "string": "http://www.w3.org/2001/XMLSchema#string",
}

IEC_TYPE_DEFAULT: dict[str, str] = {
    "int": "0",
    "float": "0.0",
    "bool": "false",
    "string": "",
}
