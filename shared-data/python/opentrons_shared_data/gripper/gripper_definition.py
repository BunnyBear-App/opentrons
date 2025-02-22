"""Gripper configurations."""

from typing_extensions import Literal
from typing import TYPE_CHECKING, List, Dict, Tuple, Any, NewType
from pydantic import BaseModel, Field, conint, confloat
from enum import Enum


def _snake_to_camel_case(snake: str) -> str:
    """Turns snake_case to camelCase."""
    return "".join(
        [s.capitalize() if i > 0 else s.lower() for i, s in enumerate(snake.split("_"))]
    )


GripperModelStr = NewType("GripperModelStr", str)


# TODO (spp, 2023-01-31): figure out if we want to keep this a string enum or revert to
#  a regular enum with custom stringification
class GripperModel(str, Enum):
    """Gripper models."""

    v1 = "gripperV1"

    def __str__(self) -> str:
        """Model name."""
        enum_to_str = {self.__class__.v1: "gripperV1"}
        return enum_to_str[self]


GripperSchemaVersion = Literal[1]

GripperSchema = Dict[str, Any]


if TYPE_CHECKING:
    _StrictNonNegativeInt = int
    _StrictNonNegativeFloat = float
else:
    _StrictNonNegativeInt = conint(strict=True, ge=0)
    _StrictNonNegativeFloat = confloat(strict=True, ge=0.0)


class GripperBaseModel(BaseModel):
    """Gripper base model."""

    class Config:
        """Config."""

        alias_generator = _snake_to_camel_case
        allow_population_by_field_name = True


Offset = Tuple[float, float, float]


class Geometry(GripperBaseModel):
    """Gripper geometry definition."""

    base_offset_from_mount: Offset
    jaw_center_offset_from_base: Offset
    pin_one_offset_from_base: Offset
    pin_two_offset_from_base: Offset
    jaw_width: Dict[str, float]


class ZMotorConfigurations(GripperBaseModel):
    """Gripper z motor configurations."""

    idle: float = Field(
        ...,
        description="Motor idle current in A",
        ge=0.02,
        le=1.0,
    )
    run: float = Field(
        ...,
        description="Motor active current in A",
        ge=0.67,
        le=2.5,
    )


class JawMotorConfigurations(GripperBaseModel):
    """Gripper z motor configurations."""

    vref: float = Field(
        ...,
        description="Reference voltage in V",
        ge=0.5,
        le=2.5,
    )


PolynomialTerm = Tuple[_StrictNonNegativeInt, float]


class GripForceProfile(GripperBaseModel):
    """Gripper force profile."""

    polynomial: List[PolynomialTerm] = Field(
        ...,
        description="Polynomial function to convert a grip force in Newton to the jaw motor duty cycle value, which will be read by the gripper firmware.",
        min_items=1,
    )
    default_grip_force: _StrictNonNegativeFloat
    default_home_force: _StrictNonNegativeFloat
    min: _StrictNonNegativeFloat
    max: _StrictNonNegativeFloat


class GripperDefinition(GripperBaseModel):
    """Gripper definition."""

    schema_version: GripperSchemaVersion = Field(
        ..., description="Which schema version a gripper is using"
    )
    display_name: str = Field(..., description="Gripper display name.")
    model: GripperModel
    geometry: Geometry
    z_motor_configurations: ZMotorConfigurations
    jaw_motor_configurations: JawMotorConfigurations
    grip_force_profile: GripForceProfile
