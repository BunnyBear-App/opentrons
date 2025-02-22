from typing import Any, Dict, cast, List, Iterable, Tuple
from typing_extensions import Final
from dataclasses import asdict

from opentrons.hardware_control.types import OT3AxisKind
from .types import (
    OT3Config,
    ByGantryLoad,
    OT3CurrentSettings,
    OT3MotionSettings,
    OT3Transform,
    Offset,
    OT3CalibrationSettings,
    CapacitivePassSettings,
    LiquidProbeSettings,
    ZSenseSettings,
    EdgeSenseSettings,
)

DEFAULT_PIPETTE_OFFSET = [0.0, 0.0, 0.0]

DEFAULT_LIQUID_PROBE_SETTINGS: Final[LiquidProbeSettings] = LiquidProbeSettings(
    starting_mount_height=100,
    max_z_distance=40,
    min_z_distance=5,
    mount_speed=10,
    plunger_speed=5,
    sensor_threshold_pascals=100,
    expected_liquid_height=110,
    log_pressure=True,
    aspirate_while_sensing=False,
    data_file="/var/pressure_sensor_data.csv",
)

DEFAULT_CALIBRATION_SETTINGS: Final[OT3CalibrationSettings] = OT3CalibrationSettings(
    z_offset=ZSenseSettings(
        pass_settings=CapacitivePassSettings(
            prep_distance_mm=3,
            max_overrun_distance_mm=2,
            speed_mm_per_s=1.0,
            sensor_threshold_pf=0.5,
        ),
    ),
    edge_sense=EdgeSenseSettings(
        overrun_tolerance_mm=0.1,
        early_sense_tolerance_mm=0.1,
        pass_settings=CapacitivePassSettings(
            prep_distance_mm=0.2,
            max_overrun_distance_mm=0.5,
            speed_mm_per_s=0.5,
            sensor_threshold_pf=0.5,
        ),
        search_initial_tolerance_mm=5.0,
        search_iteration_limit=10,
    ),
    edge_sense_binary=EdgeSenseSettings(
        overrun_tolerance_mm=0.5,
        early_sense_tolerance_mm=0.2,
        pass_settings=CapacitivePassSettings(
            prep_distance_mm=1,
            max_overrun_distance_mm=1,
            speed_mm_per_s=1,
            sensor_threshold_pf=1.0,
        ),
        search_initial_tolerance_mm=5.0,
        search_iteration_limit=10,
    ),
    probe_length=44.5,
)

ROBOT_CONFIG_VERSION: Final = 1
DEFAULT_LOG_LEVEL: Final = "INFO"
DEFAULT_DECK_TRANSFORM: Final[OT3Transform] = [
    [-1.0, 0.0, 0.0],
    [0.0, -1.0, 0.0],
    [0.0, 0.0, -1.0],
]
DEFAULT_CARRIAGE_OFFSET: Final[Offset] = (477.20, 493.8, 253.475)
DEFAULT_LEFT_MOUNT_OFFSET: Final[Offset] = (-13.5, -60.5, 255.675)
DEFAULT_RIGHT_MOUNT_OFFSET: Final[Offset] = (40.5, -60.5, 255.675)
DEFAULT_GRIPPER_MOUNT_OFFSET: Final[Offset] = (84.55, -12.75, 93.85)
DEFAULT_Z_RETRACT_DISTANCE: Final = 2
DEFAULT_GRIPPER_JAW_HOME_DUTY_CYCLE: Final = 25

DEFAULT_MAX_SPEEDS: Final[ByGantryLoad[Dict[OT3AxisKind, float]]] = ByGantryLoad(
    high_throughput={
        OT3AxisKind.X: 500,
        OT3AxisKind.Y: 500,
        OT3AxisKind.Z: 35,
        OT3AxisKind.P: 5,
        OT3AxisKind.Z_G: 100,
        OT3AxisKind.Q: 5.5,
    },
    low_throughput={
        OT3AxisKind.X: 500,
        OT3AxisKind.Y: 500,
        OT3AxisKind.Z: 65,
        OT3AxisKind.P: 45,
        OT3AxisKind.Z_G: 100,
    },
)

DEFAULT_ACCELERATIONS: Final[ByGantryLoad[Dict[OT3AxisKind, float]]] = ByGantryLoad(
    high_throughput={
        OT3AxisKind.X: 1000,
        OT3AxisKind.Y: 1000,
        OT3AxisKind.Z: 100,
        OT3AxisKind.P: 10,
        OT3AxisKind.Z_G: 20,
        OT3AxisKind.Q: 10,
    },
    low_throughput={
        OT3AxisKind.X: 1000,
        OT3AxisKind.Y: 1000,
        OT3AxisKind.Z: 100,
        OT3AxisKind.P: 50,
        OT3AxisKind.Z_G: 20,
    },
)

DEFAULT_MAX_SPEED_DISCONTINUITY: Final[
    ByGantryLoad[Dict[OT3AxisKind, float]]
] = ByGantryLoad(
    high_throughput={
        OT3AxisKind.X: 10,
        OT3AxisKind.Y: 10,
        OT3AxisKind.Z: 10,
        OT3AxisKind.P: 10,
        OT3AxisKind.Z_G: 10,
        OT3AxisKind.Q: 10,
    },
    low_throughput={
        OT3AxisKind.X: 10,
        OT3AxisKind.Y: 10,
        OT3AxisKind.Z: 10,
        OT3AxisKind.P: 10,
        OT3AxisKind.Z_G: 10,
    },
)

DEFAULT_DIRECTION_CHANGE_SPEED_DISCONTINUITY: Final[
    ByGantryLoad[Dict[OT3AxisKind, float]]
] = ByGantryLoad(
    high_throughput={
        OT3AxisKind.X: 5,
        OT3AxisKind.Y: 5,
        OT3AxisKind.Z: 5,
        OT3AxisKind.P: 5,
        OT3AxisKind.Q: 5,
        OT3AxisKind.Z_G: 5,
    },
    low_throughput={
        OT3AxisKind.X: 5,
        OT3AxisKind.Y: 5,
        OT3AxisKind.Z: 5,
        OT3AxisKind.P: 5,
        OT3AxisKind.Z_G: 5,
    },
)

DEFAULT_HOLD_CURRENT: Final[ByGantryLoad[Dict[OT3AxisKind, float]]] = ByGantryLoad(
    high_throughput={
        OT3AxisKind.X: 0.5,
        OT3AxisKind.Y: 0.5,
        OT3AxisKind.Z: 0.8,
        OT3AxisKind.P: 0.3,
        OT3AxisKind.Z_G: 0.2,
        OT3AxisKind.Q: 0.3,
    },
    low_throughput={
        OT3AxisKind.X: 0.5,
        OT3AxisKind.Y: 0.5,
        OT3AxisKind.Z: 0.1,
        OT3AxisKind.P: 0.3,
        OT3AxisKind.Z_G: 0.2,
    },
)

DEFAULT_RUN_CURRENT: Final[ByGantryLoad[Dict[OT3AxisKind, float]]] = ByGantryLoad(
    high_throughput={
        OT3AxisKind.X: 1.4,
        OT3AxisKind.Y: 1.4,
        OT3AxisKind.Z: 1.4,
        # TODO: verify this value
        OT3AxisKind.P: 2.0,
        OT3AxisKind.Z_G: 0.67,
        OT3AxisKind.Q: 1.5,
    },
    low_throughput={
        OT3AxisKind.X: 1.4,
        OT3AxisKind.Y: 1.4,
        OT3AxisKind.Z: 1.4,
        # TODO: verify this value
        OT3AxisKind.P: 1.0,
        OT3AxisKind.Z_G: 0.67,
    },
)


def _build_dict_with_default(
    from_conf: Any,
    default: Dict[OT3AxisKind, float],
) -> Dict[OT3AxisKind, float]:
    if not isinstance(from_conf, dict):
        return {k: v for k, v in default.items()}
    else:
        validated: Dict[OT3AxisKind, float] = {}
        # Keep what is specified, handling it being
        # either enum element name string or enum element directly
        for k, v in from_conf.items():
            if isinstance(k, OT3AxisKind):
                validated[k] = v
            else:
                try:
                    enumval = OT3AxisKind[k]
                except KeyError:  # not an enum entry
                    pass
                else:
                    validated[enumval] = v
        # Add what's missing relative to the default
        for k, default_v in default.items():
            if k in from_conf:
                validated[k] = from_conf[k]
            elif k.name in from_conf:
                validated[k] = from_conf[k.name]
            else:
                validated[k] = default_v
        return validated


def _build_default_bpk(
    from_conf: Any, default: ByGantryLoad[Dict[OT3AxisKind, float]]
) -> ByGantryLoad[Dict[OT3AxisKind, float]]:
    return ByGantryLoad(
        low_throughput=_build_dict_with_default(
            from_conf.get("low_throughput", {}), default.low_throughput
        ),
        high_throughput=_build_dict_with_default(
            from_conf.get("high_throughput", {}), default.high_throughput
        ),
    )


def _build_default_offset(from_conf: Any, default: Offset) -> Offset:
    if not isinstance(from_conf, (list, tuple)) or len(from_conf) != 3:
        return default
    return cast(Offset, tuple(from_conf))


def _build_default_transform(
    from_conf: Any, default: List[List[float]]
) -> List[List[float]]:
    if (
        not isinstance(from_conf, list)
        or len(from_conf) != 3
        or not all(isinstance(elem, list) for elem in from_conf)
        or not all(len(e) == 3 for e in from_conf)
        or not all(
            all(isinstance(elem, (int, float)) for elem in vec) for vec in from_conf
        )
    ):
        return default
    return cast(OT3Transform, from_conf)


def _build_default_cap_pass(
    from_conf: Any, default: CapacitivePassSettings
) -> CapacitivePassSettings:
    return CapacitivePassSettings(
        prep_distance_mm=from_conf.get("prep_distance_mm", default.prep_distance_mm),
        max_overrun_distance_mm=from_conf.get(
            "max_overrun_distance_mm", default.max_overrun_distance_mm
        ),
        speed_mm_per_s=from_conf.get("speed_mm_per_s", default.speed_mm_per_s),
        sensor_threshold_pf=from_conf.get(
            "sensor_threshold_pf", default.sensor_threshold_pf
        ),
    )


def _build_default_liquid_probe(
    from_conf: Any, default: LiquidProbeSettings
) -> LiquidProbeSettings:
    return LiquidProbeSettings(
        starting_mount_height=from_conf.get(
            "starting_mount_height", default.starting_mount_height
        ),
        max_z_distance=from_conf.get("max_z_distance", default.max_z_distance),
        min_z_distance=from_conf.get("min_z_distance", default.min_z_distance),
        mount_speed=from_conf.get("mount_speed", default.mount_speed),
        plunger_speed=from_conf.get("plunger_speed", default.plunger_speed),
        sensor_threshold_pascals=from_conf.get(
            "sensor_threshold_pascals", default.sensor_threshold_pascals
        ),
        expected_liquid_height=from_conf.get(
            "expected_liquid_height", default.expected_liquid_height
        ),
        log_pressure=from_conf.get("log_pressure", default.log_pressure),
        aspirate_while_sensing=from_conf.get(
            "aspirate_while_sensing", default.aspirate_while_sensing
        ),
        data_file=from_conf.get("data_file", default.data_file),
    )


def _build_default_z_pass(from_conf: Any, default: ZSenseSettings) -> ZSenseSettings:
    return ZSenseSettings(
        pass_settings=_build_default_cap_pass(
            from_conf.get("pass_settings", {}), default.pass_settings
        ),
    )


def _build_default_edge_sense(
    from_conf: Any, default: EdgeSenseSettings
) -> EdgeSenseSettings:
    return EdgeSenseSettings(
        overrun_tolerance_mm=from_conf.get(
            "overrun_tolerance_mm", default.overrun_tolerance_mm
        ),
        early_sense_tolerance_mm=from_conf.get(
            "early_sense_tolerance_mm", default.early_sense_tolerance_mm
        ),
        pass_settings=_build_default_cap_pass(
            from_conf.get("pass_settings", {}), default.pass_settings
        ),
        search_initial_tolerance_mm=from_conf.get(
            "search_initial_tolerance_mm", default.search_initial_tolerance_mm
        ),
        search_iteration_limit=from_conf.get(
            "search_iteration_limit", default.search_iteration_limit
        ),
    )


def _build_default_calibration(
    from_conf: Any, default: OT3CalibrationSettings
) -> OT3CalibrationSettings:
    return OT3CalibrationSettings(
        z_offset=_build_default_z_pass(from_conf.get("z_offset", {}), default.z_offset),
        edge_sense=_build_default_edge_sense(
            from_conf.get("edge_sense", {}), default.edge_sense
        ),
        edge_sense_binary=_build_default_edge_sense(
            from_conf.get("edge_sense_binary", {}), default.edge_sense_binary
        ),
        probe_length=from_conf.get("probe_length", default.probe_length),
    )


def build_with_defaults(robot_settings: Dict[str, Any]) -> OT3Config:
    motion_settings = robot_settings.get("motion_settings", {})
    current_settings = robot_settings.get("current_settings", {})
    return OT3Config(
        model="OT-3 Standard",
        version=ROBOT_CONFIG_VERSION,
        name=robot_settings.get("name", "Grace Hopper"),
        log_level=robot_settings.get("log_level", DEFAULT_LOG_LEVEL),
        motion_settings=OT3MotionSettings(
            default_max_speed=_build_default_bpk(
                motion_settings.get("default_max_speed", {}), DEFAULT_MAX_SPEEDS
            ),
            acceleration=_build_default_bpk(
                motion_settings.get("acceleration", {}), DEFAULT_ACCELERATIONS
            ),
            max_speed_discontinuity=_build_default_bpk(
                motion_settings.get("max_speed_discontinuity", {}),
                DEFAULT_MAX_SPEED_DISCONTINUITY,
            ),
            direction_change_speed_discontinuity=_build_default_bpk(
                motion_settings.get("direction_change_speed_discontinuity", {}),
                DEFAULT_DIRECTION_CHANGE_SPEED_DISCONTINUITY,
            ),
        ),
        current_settings=OT3CurrentSettings(
            hold_current=_build_default_bpk(
                current_settings.get("hold_current", {}),
                DEFAULT_HOLD_CURRENT,
            ),
            run_current=_build_default_bpk(
                current_settings.get("run_current", {}),
                DEFAULT_RUN_CURRENT,
            ),
        ),
        z_retract_distance=robot_settings.get(
            "z_retract_distance", DEFAULT_Z_RETRACT_DISTANCE
        ),
        grip_jaw_home_duty_cycle=robot_settings.get(
            "grip_jaw_home_duty_cycle", DEFAULT_GRIPPER_JAW_HOME_DUTY_CYCLE
        ),
        deck_transform=_build_default_transform(
            robot_settings.get("deck_transform", []), DEFAULT_DECK_TRANSFORM
        ),
        carriage_offset=_build_default_offset(
            robot_settings.get("carriage_offset", []), DEFAULT_CARRIAGE_OFFSET
        ),
        left_mount_offset=_build_default_offset(
            robot_settings.get("left_mount_offset", []), DEFAULT_LEFT_MOUNT_OFFSET
        ),
        right_mount_offset=_build_default_offset(
            robot_settings.get("right_mount_offset", []), DEFAULT_RIGHT_MOUNT_OFFSET
        ),
        gripper_mount_offset=_build_default_offset(
            robot_settings.get("gripper_mount_offset", []), DEFAULT_GRIPPER_MOUNT_OFFSET
        ),
        calibration=_build_default_calibration(
            robot_settings.get("calibration", {}), DEFAULT_CALIBRATION_SETTINGS
        ),
        liquid_sense=_build_default_liquid_probe(
            robot_settings.get("liquid_sense", {}), DEFAULT_LIQUID_PROBE_SETTINGS
        ),
    )


def serialize(config: OT3Config) -> Dict[str, Any]:
    def _build_dict(pairs: Iterable[Tuple[Any, Any]]) -> Dict[str, Any]:
        def _normalize_key(key: Any) -> Any:
            if isinstance(key, OT3AxisKind):
                return key.name
            return key

        def _normalize_value(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    _normalize_key(k): _normalize_value(v) for k, v in value.items()
                }
            else:
                return value

        return dict((_normalize_key(key), _normalize_value(val)) for key, val in pairs)

    return asdict(config, dict_factory=_build_dict)
