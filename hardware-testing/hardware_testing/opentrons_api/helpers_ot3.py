"""Opentrons helper methods."""
from dataclasses import dataclass
from datetime import datetime
from subprocess import run
from time import time
from typing import List, Optional, Dict, Tuple, Union

from opentrons_hardware.firmware_bindings.constants import SensorId
from opentrons_hardware.sensors import sensor_driver, sensor_types

from opentrons_shared_data.deck import load as load_deck
from opentrons_shared_data.labware import load_definition as load_labware

from opentrons.config.robot_configs import build_config_ot3, load_ot3 as load_ot3_config
from opentrons.hardware_control.backends.ot3utils import sensor_node_for_mount

# TODO (lc 10-27-2022) This should be changed to an ot3 pipette object once we
# have that well defined.
from opentrons.hardware_control.instruments.ot2.pipette import Pipette as PipetteOT2
from opentrons.hardware_control.instruments.ot3.pipette import Pipette as PipetteOT3
from opentrons.hardware_control.motion_utilities import deck_from_machine
from opentrons.hardware_control.ot3api import OT3API

from .types import (
    GantryLoad,
    PerPipetteAxisSettings,
    OT3Axis,
    OT3Mount,
    Point,
    CriticalPoint,
)

# TODO: use values from shared data, so we don't need to update here again
TIP_LENGTH_OVERLAP = 10.5
TIP_LENGTH_LOOKUP = {50: 57.9, 200: 58.35, 1000: 95.6}


@dataclass
class CalibrationSquare:
    """Calibration Square."""

    top_left_offset: Point
    width: float
    height: float
    depth: float


@dataclass
class CalibrationProbe:
    """Calibration Probe."""

    length: float
    diameter: float


# values are from "Robot Extents" sheet
CALIBRATION_SQUARE_OFFSET_EVT = Point(x=64, y=-43, z=-0.25)
CALIBRATION_SQUARE_EVT = CalibrationSquare(
    top_left_offset=CALIBRATION_SQUARE_OFFSET_EVT, width=20, height=20, depth=3
)
CALIBRATION_PROBE_EVT = CalibrationProbe(length=44.5, diameter=4.0)


def stop_server_ot3() -> None:
    """Stop opentrons-robot-server on the OT3."""
    print('Stopping "opentrons-robot-server"...')
    run(["systemctl", "stop", "opentrons-robot-server"])


def restart_canbus_ot3() -> None:
    """Restart opentrons-ot3-canbus on the OT3."""
    print('Restarting "opentrons-ot3-canbus"...')
    run(["systemctl", "restart", "opentrons-ot3-canbus"])


def stop_on_device_display_ot3() -> None:
    """Stop opentrons on-device-display on the OT3."""
    run(["systemctl", "stop", "opentrons-robot-app"])


def _create_fake_pipette_id(mount: OT3Mount, model: Optional[str]) -> Optional[str]:
    if model is None:
        return None
    items = model.split("_")
    assert len(items) == 3
    size = "P1K" if items[0] == "p1000" else "P50"
    channels = "S" if items[1] == "single" else "M"
    version = items[2].upper().replace(".", "")
    date = datetime.now().strftime("%y%m%d")
    unique_number = 1 if mount == OT3Mount.LEFT else 2
    return f"{size}{channels}{version}{date}A0{unique_number}"


def _create_attached_instruments_dict(
    pipette_left: Optional[str] = None,
    pipette_right: Optional[str] = None,
    gripper: Optional[str] = None,
) -> Dict[OT3Mount, Dict[str, Optional[str]]]:
    fake_id_left = _create_fake_pipette_id(OT3Mount.LEFT, pipette_left)
    fake_id_right = _create_fake_pipette_id(OT3Mount.RIGHT, pipette_right)
    fake_id_gripper = (
        "GRPV1020221101A02" if gripper else None
    )  # FIXME: EVT grippers all have same ID
    sim_pip_left = {"model": pipette_left, "id": fake_id_left}
    sim_pip_right = {"model": pipette_right, "id": fake_id_right}
    sim_gripper = {"model": gripper, "id": fake_id_gripper}
    return {
        OT3Mount.LEFT: sim_pip_left,
        OT3Mount.RIGHT: sim_pip_right,
        OT3Mount.GRIPPER: sim_gripper,
    }


async def build_async_ot3_hardware_api(
    is_simulating: Optional[bool] = False,
    use_defaults: Optional[bool] = True,
    pipette_left: Optional[str] = None,
    pipette_right: Optional[str] = None,
    gripper: Optional[str] = None,
) -> OT3API:
    """Built an OT3 Hardware API instance."""
    config = build_config_ot3({}) if use_defaults else load_ot3_config()
    kwargs = {"config": config}
    if is_simulating:
        builder = OT3API.build_hardware_simulator
        # TODO (andy s): add ability to simulate:
        #                - gripper
        #                - 96-channel
        #                - modules
        sim_pips = _create_attached_instruments_dict(
            pipette_left, pipette_right, gripper
        )
        kwargs["attached_instruments"] = sim_pips  # type: ignore[assignment]
    else:
        builder = OT3API.build_hardware_controller
        stop_server_ot3()
        restart_canbus_ot3()
    return await builder(**kwargs)  # type: ignore[arg-type]


def set_gantry_per_axis_setting_ot3(
    settings: PerPipetteAxisSettings, axis: OT3Axis, load: GantryLoad, value: float
) -> None:
    """Set a value in an OT3 Gantry's per-axis-settings."""
    axis_kind = OT3Axis.to_kind(axis)
    if load == GantryLoad.HIGH_THROUGHPUT:
        settings.high_throughput[axis_kind] = value
    else:
        settings.low_throughput[axis_kind] = value


def get_gantry_per_axis_setting_ot3(
    settings: PerPipetteAxisSettings, axis: OT3Axis, load: GantryLoad
) -> float:
    """Set a value in an OT3 Gantry's per-axis-settings."""
    axis_kind = OT3Axis.to_kind(axis)
    if load == GantryLoad.HIGH_THROUGHPUT:
        return settings.high_throughput[axis_kind]
    return settings.low_throughput[axis_kind]


def set_gantry_load_per_axis_current_settings_ot3(
    api: OT3API,
    axis: OT3Axis,
    load: Optional[GantryLoad] = None,
    hold_current: Optional[float] = None,
    run_current: Optional[float] = None,
) -> None:
    """Update an OT3 axis current settings."""
    if load is None:
        load = api.gantry_load
    if hold_current is not None:
        set_gantry_per_axis_setting_ot3(
            settings=api.config.current_settings.hold_current,
            axis=axis,
            load=load,
            value=hold_current,
        )
    if run_current is not None:
        set_gantry_per_axis_setting_ot3(
            settings=api.config.current_settings.run_current,
            axis=axis,
            load=load,
            value=run_current,
        )


def set_gantry_load_per_axis_motion_settings_ot3(
    api: OT3API,
    axis: OT3Axis,
    load: Optional[GantryLoad] = None,
    default_max_speed: Optional[float] = None,
    acceleration: Optional[float] = None,
    max_speed_discontinuity: Optional[float] = None,
    direction_change_speed_discontinuity: Optional[float] = None,
) -> None:
    """Update an OT3 axis motion settings."""
    if load is None:
        load = api.gantry_load
    if default_max_speed is not None:
        set_gantry_per_axis_setting_ot3(
            settings=api.config.motion_settings.default_max_speed,
            axis=axis,
            load=load,
            value=default_max_speed,
        )
    if acceleration is not None:
        set_gantry_per_axis_setting_ot3(
            settings=api.config.motion_settings.acceleration,
            axis=axis,
            load=load,
            value=acceleration,
        )
    if max_speed_discontinuity is not None:
        set_gantry_per_axis_setting_ot3(
            settings=api.config.motion_settings.max_speed_discontinuity,
            axis=axis,
            load=load,
            value=max_speed_discontinuity,
        )
    if direction_change_speed_discontinuity is not None:
        set_gantry_per_axis_setting_ot3(
            settings=api.config.motion_settings.direction_change_speed_discontinuity,
            axis=axis,
            load=load,
            value=direction_change_speed_discontinuity,
        )


@dataclass
class GantryLoadSettings:
    """Gantry Load Settings."""

    max_speed: float  # mm/sec
    acceleration: float  # mm/sec**2
    max_start_stop_speed: float  # mm/sec
    max_change_dir_speed: float  # mm/sec
    hold_current: float  # amps
    run_current: float  # amps


def get_gantry_load_per_axis_motion_settings_ot3(
    api: OT3API,
    axis: OT3Axis,
    load: Optional[GantryLoad] = None,
) -> GantryLoadSettings:
    """Get the gantry-load settings, per OT3Axis."""
    if load is None:
        load = api.gantry_load
    ax_kind = OT3Axis.to_kind(axis)
    m_cfg = api.config.motion_settings
    c_cfg = api.config.current_settings

    def _default_motion(a: str) -> float:
        try:
            return getattr(m_cfg, a)[load][ax_kind]
        except KeyError:
            return getattr(m_cfg, a)[GantryLoad.LOW_THROUGHPUT][ax_kind]

    def _default_current(a: str) -> float:
        try:
            return getattr(c_cfg, a)[load][ax_kind]
        except KeyError:
            return getattr(c_cfg, a)[GantryLoad.LOW_THROUGHPUT][ax_kind]

    return GantryLoadSettings(
        max_speed=_default_motion("default_max_speed"),
        acceleration=_default_motion("acceleration"),
        max_start_stop_speed=_default_motion("max_speed_discontinuity"),
        max_change_dir_speed=_default_motion("direction_change_speed_discontinuity"),
        hold_current=_default_current("hold_current"),
        run_current=_default_current("run_current"),
    )


async def set_gantry_load_per_axis_settings_ot3(
    api: OT3API,
    settings: Dict[OT3Axis, GantryLoadSettings],
    load: Optional[GantryLoad] = None,
) -> None:
    """Set motion/current settings, per-axis, per-gantry-load."""
    if load is None:
        load = api.gantry_load
    for ax, stg in settings.items():
        set_gantry_load_per_axis_motion_settings_ot3(
            api,
            ax,
            load,
            default_max_speed=stg.max_speed,
            acceleration=stg.acceleration,
            max_speed_discontinuity=stg.max_start_stop_speed,
            direction_change_speed_discontinuity=stg.max_change_dir_speed,
        )
        set_gantry_load_per_axis_current_settings_ot3(
            api, ax, load, hold_current=stg.hold_current, run_current=stg.run_current
        )
    if load == api.gantry_load:
        await api.set_gantry_load(gantry_load=load)


async def home_ot3(api: OT3API, axes: Optional[List[OT3Axis]] = None) -> None:
    """Home OT3 gantry."""
    default_home_speed = 10.0
    default_home_speed_xy = 40.0

    homing_speeds: Dict[OT3Axis, float] = {
        OT3Axis.X: default_home_speed_xy,
        OT3Axis.Y: default_home_speed_xy,
        OT3Axis.Z_L: default_home_speed,
        OT3Axis.Z_R: default_home_speed,
        OT3Axis.Z_G: default_home_speed,
        OT3Axis.P_L: default_home_speed,
        OT3Axis.P_R: default_home_speed,
    }

    # save our current script's settings
    cached_discontinuities: Dict[OT3Axis, float] = {
        ax: api.config.motion_settings.max_speed_discontinuity[api.gantry_load].get(
            OT3Axis.to_kind(ax), homing_speeds[ax]
        )
        for ax in homing_speeds
    }
    # overwrite current settings with API settings
    for ax, val in homing_speeds.items():
        set_gantry_load_per_axis_motion_settings_ot3(
            api, ax, max_speed_discontinuity=val
        )
    # actually home
    await api.home(axes=axes)
    # revert back to our script's settings
    for ax, val in cached_discontinuities.items():
        set_gantry_load_per_axis_motion_settings_ot3(
            api, ax, max_speed_discontinuity=val
        )


def _get_pipette_from_mount(api: OT3API, mount: OT3Mount) -> PipetteOT3:
    pipette = api.hardware_pipettes[mount.to_mount()]
    if pipette is None:
        raise RuntimeError(f"No pipette currently attaced to mount {mount}")
    return pipette


def get_plunger_positions_ot3(
    api: OT3API, mount: OT3Mount
) -> Tuple[float, float, float, float]:
    """Update plunger current."""
    pipette = _get_pipette_from_mount(api, mount)
    return (
        pipette.plunger_positions.top,
        pipette.plunger_positions.bottom,
        pipette.plunger_positions.blow_out,
        pipette.plunger_positions.drop_tip,
    )


async def update_pick_up_current(
    api: OT3API, mount: OT3Mount, current: float = 0.125
) -> None:
    """Update pick-up-tip current."""
    pipette = _get_pipette_from_mount(api, mount)
    config_model = pipette.pick_up_configurations
    config_model.current = current
    pipette.pick_up_configurations = config_model


async def update_pick_up_distance(
    api: OT3API, mount: OT3Mount, distance: float = 17.0
) -> None:
    """Update pick-up-tip current."""
    pipette = _get_pipette_from_mount(api, mount)
    config_model = pipette.pick_up_configurations
    config_model.distance = distance
    pipette.pick_up_configurations = config_model


async def move_plunger_absolute_ot3(
    api: OT3API,
    mount: OT3Mount,
    position: float,
    motor_current: Optional[float] = None,
    speed: Optional[float] = None,
) -> None:
    """Move OT3 plunger position to an absolute position."""
    if not api.hardware_pipettes[mount.to_mount()]:
        raise RuntimeError(f"No pipette found on mount: {mount}")
    plunger_axis = OT3Axis.of_main_tool_actuator(mount)
    _move_coro = api._move(
        target_position={plunger_axis: position},  # type: ignore[arg-type]
        speed=speed,
    )
    if motor_current is None:
        await _move_coro
    else:
        async with api._backend.restore_current():
            await api._backend.set_active_current(
                {OT3Axis.of_main_tool_actuator(mount): motor_current}  # type: ignore[dict-item]
            )
            await _move_coro


async def move_plunger_relative_ot3(
    api: OT3API,
    mount: OT3Mount,
    delta: float,
    motor_current: Optional[float] = None,
    speed: Optional[float] = None,
) -> None:
    """Move OT3 plunger position in a relative direction."""
    current_pos = await api.current_position_ot3(mount=mount)
    plunger_axis = OT3Axis.of_main_tool_actuator(mount)
    plunger_pos = current_pos[plunger_axis]
    return await move_plunger_absolute_ot3(
        api, mount, plunger_pos + delta, motor_current, speed
    )


async def move_gripper_jaw_relative_ot3(api: OT3API, delta: float) -> None:
    """Move the gripper jaw by a relative distance."""
    # FIXME: this should be in relative distances
    #        but the api isn't setup for reporting current position yet
    print("FIXME: Not using relative distances for gripper, using absolute...")
    await api.hold_jaw_width(int(delta))


def get_endstop_position_ot3(api: OT3API, mount: OT3Mount) -> Dict[OT3Axis, float]:
    """Get the endstop's position per mount."""
    transforms = api._transforms
    machine_pos_per_axis = api._backend.home_position()
    deck_pos_per_axis = deck_from_machine(
        machine_pos_per_axis,
        transforms.deck_calibration.attitude,
        transforms.carriage_offset,
    )
    mount_pos_per_axis = api._effector_pos_from_carriage_pos(
        mount, deck_pos_per_axis, None
    )
    return {ax: val for ax, val in mount_pos_per_axis.items()}


def get_gantry_homed_position_ot3(api: OT3API, mount: OT3Mount) -> Point:
    """Get the homed coordinate by mount."""
    axes_pos = get_endstop_position_ot3(api, mount)
    return Point(
        x=axes_pos[OT3Axis.X],
        y=axes_pos[OT3Axis.Y],
        z=axes_pos[OT3Axis.by_mount(mount)],
    )


class OT3JogTermination(Exception):
    """Jogging terminated."""

    pass


class OT3JogNoInput(Exception):
    """No jogging input from user."""

    pass


def _jog_read_user_input(terminator: str, home_key: str) -> Tuple[str, float, bool]:
    user_input = input(f'\tJog eg: x-10.5 (ENTER to repeat, "{terminator}" to stop): ')
    user_input = user_input.strip().replace(" ", "")
    if user_input == terminator:
        raise OT3JogTermination()
    if not user_input:
        raise OT3JogNoInput()
    if home_key in user_input:
        user_input = user_input.replace(home_key, "")
        do_home = True
        distance = 0.0
    else:
        do_home = False
        distance = float(user_input[1:])
    axis = user_input[0].upper()
    if axis not in "XYZPG":
        raise ValueError(f'Unexpected axis: "{axis}"')
    return axis, distance, do_home


async def _jog_axis_some_distance(
    api: OT3API, mount: OT3Mount, axis: str, distance: float
) -> None:
    if not axis or distance == 0.0:
        return
    elif axis == "G":
        await move_gripper_jaw_relative_ot3(api, distance)
    elif axis == "P":
        await move_plunger_relative_ot3(api, mount, distance)
    else:
        delta = Point(**{axis.lower(): distance})
        await api.move_rel(mount=mount, delta=delta)


async def _jog_print_current_position(
    api: OT3API, mount: OT3Mount, critical_point: Optional[CriticalPoint] = None
) -> None:
    z_axis = OT3Axis.by_mount(mount)
    instr_axis = OT3Axis.of_main_tool_actuator(mount)
    motors_pos = await api.current_position_ot3(
        mount=mount, critical_point=critical_point
    )
    enc_pos = await api.encoder_current_position_ot3(
        mount=mount, critical_point=critical_point
    )
    mx, my, mz, mp = [
        round(motors_pos[ax], 2) for ax in [OT3Axis.X, OT3Axis.Y, z_axis, instr_axis]
    ]
    ex, ey, ez, ep = [
        round(enc_pos[ax], 2) for ax in [OT3Axis.X, OT3Axis.Y, z_axis, instr_axis]
    ]
    print(f"\tDeck Coordinate: X={mx}, Y={my}, Z={mz}, Instr={mp}")
    print(f"\tEnc. Coordinate: X={ex}, Y={ey}, Z={ez}, Instr={ep}")


async def _jog_do_print_then_input_then_move(
    api: OT3API,
    mount: OT3Mount,
    critical_point: Optional[CriticalPoint],
    axis: str,
    distance: float,
    do_home: bool,
    display: Optional[bool] = True,
) -> Tuple[str, float, bool]:
    try:
        if display:
            await _jog_print_current_position(api, mount, critical_point)
        axis, distance, do_home = _jog_read_user_input(
            terminator="stop", home_key="home"
        )
    except OT3JogNoInput:
        pass
    if do_home:
        str_to_axes = {
            "X": OT3Axis.X,
            "Y": OT3Axis.Y,
            "Z": OT3Axis.by_mount(mount),
            "P": OT3Axis.of_main_tool_actuator(mount),
            "G": OT3Axis.G,
            "Q": OT3Axis.Q,
        }
        await api.home([str_to_axes[axis]])
    else:
        await _jog_axis_some_distance(api, mount, axis, distance)
    return axis, distance, do_home


async def jog_mount_ot3(
    api: OT3API,
    mount: OT3Mount,
    critical_point: Optional[CriticalPoint] = None,
    display: Optional[bool] = True,
) -> Dict[OT3Axis, float]:
    """Jog an OT3 mount's gantry XYZ and pipettes axes."""
    if api.is_simulator:
        return await api.current_position_ot3(
            mount=mount, critical_point=critical_point
        )
    axis: str = ""
    distance: float = 0.0
    do_home: bool = False
    print("jogging")
    while True:
        try:
            axis, distance, do_home = await _jog_do_print_then_input_then_move(
                api, mount, critical_point, axis, distance, do_home, display=display
            )
        except ValueError as e:
            print(e)
            continue
        except OT3JogTermination:
            print("done jogging")
            return await api.current_position_ot3(
                mount=mount, critical_point=critical_point
            )


async def move_to_arched_ot3(
    api: OT3API,
    mount: OT3Mount,
    abs_position: Point,
    speed: Optional[float] = None,
    safe_height: float = -100.0,
) -> None:
    """Move OT3 gantry in an arched path."""
    z_ax = OT3Axis.by_mount(mount)
    max_z = get_endstop_position_ot3(api, mount)[z_ax]
    here = await api.gantry_position(mount=mount, refresh=True)
    arch_z = min(max(here.z, abs_position.z, safe_height), max_z)
    points = [
        here._replace(z=arch_z),
        abs_position._replace(z=arch_z),
        abs_position,
    ]
    for p in points:
        await api.move_to(mount=mount, abs_position=p, speed=speed)


class SensorResponseBad(Exception):
    """Sensor Response is Bad."""

    pass


async def get_capacitance_ot3(api: OT3API, mount: OT3Mount) -> float:
    """Get the capacitance reading from the pipette."""
    if api.is_simulator:
        return 0.0
    node_id = sensor_node_for_mount(mount)
    # FIXME: allow SensorId to specify which sensor on the device to read from
    capacitive = sensor_types.CapacitiveSensor.build(SensorId.S0, node_id)
    s_driver = sensor_driver.SensorDriver()
    data = await s_driver.read(
        api._backend._messenger, capacitive, offset=False, timeout=1  # type: ignore[union-attr]
    )
    if data is None:
        raise SensorResponseBad("no response from sensor")
    return data.to_float()  # type: ignore[union-attr]


async def get_temperature_humidity_ot3(
    api: OT3API, mount: OT3Mount
) -> Tuple[float, float]:
    """Get the temperature/humidity reading from the pipette."""
    if api.is_simulator:
        return 25.0, 50.0
    node_id = sensor_node_for_mount(mount)
    # FIXME: allow SensorId to specify which sensor on the device to read from
    environment = sensor_types.EnvironmentSensor.build(SensorId.S0, node_id)
    s_driver = sensor_driver.SensorDriver()
    data = await s_driver.read(
        api._backend._messenger, environment, offset=False, timeout=1  # type: ignore[union-attr]
    )
    if data is None:
        raise SensorResponseBad("no response from sensor")
    return data.temperature.to_float(), data.humidity.to_float()  # type: ignore[union-attr]


async def get_pressure_ot3(api: OT3API, mount: OT3Mount) -> float:
    """Get the pressure reading from the pipette."""
    if api.is_simulator:
        return 0.0
    node_id = sensor_node_for_mount(mount)
    # FIXME: allow SensorId to specify which sensor on the device to read from
    pressure = sensor_types.PressureSensor.build(SensorId.S0, node_id)
    s_driver = sensor_driver.SensorDriver()
    data = await s_driver.read(
        api._backend._messenger, pressure, offset=False, timeout=1  # type: ignore[union-attr]
    )
    if data is None:
        raise SensorResponseBad("no response from sensor")
    return data.to_float()  # type: ignore[union-attr]


async def wait_for_stable_capacitance_ot3(
    api: OT3API,
    mount: OT3Mount,
    threshold_pf: float,
    duration: float,
    retries: int = 10,
) -> None:
    """Wait for the pipette capacitance to be stable."""
    if api.is_simulator:
        return
    data = list()

    async def _read() -> None:
        cap_val = await get_capacitance_ot3(api, mount)
        data.append(
            (
                time(),
                cap_val,
            )
        )

    def _data_duration() -> float:
        if len(data) < 2:
            return 0.0
        return data[-1][0] - data[0][0]

    def _data_stats() -> Tuple[float, float]:
        cap_data = [d[1] for d in data]
        avg = sum(cap_data) / len(cap_data)
        var = max(cap_data) - min(cap_data)
        return avg, var

    print(f"Waiting for {duration} seconds of stable capacitance, please wait...")
    while _data_duration() < duration:
        await _read()

    average, variance = _data_stats()
    print(
        f"Read {len(data)} samples in {_data_duration()} seconds "
        f"(average={average}, variance={variance})"
    )
    if variance > threshold_pf or variance == 0.0:
        if retries <= 0:
            raise RuntimeError("Unable to get stable capacitance reading")
        print("Unstable, repeating...")
        await wait_for_stable_capacitance_ot3(
            api, mount, threshold_pf, duration, retries - 1
        )


def get_pipette_offset_ot3(api: OT3API, mount: OT3Mount) -> Point:
    """Get pipette offset OT3."""
    pipette = api.hardware_pipettes[mount.to_mount()]
    assert pipette, f"No pipette found on mount: {mount}"
    return pipette._pipette_offset.offset + Point()


def set_pipette_offset_ot3(api: OT3API, mount: OT3Mount, offset: Point) -> None:
    """Set pipette offset OT3."""
    pipette = api.hardware_pipettes[mount.to_mount()]
    assert pipette, f"No pipette found on mount: {mount}"
    pipette._pipette_offset.offset = offset


def get_gripper_offset_ot3(api: OT3API) -> Point:
    """Get gripper offset OT3."""
    assert api.has_gripper, "No gripper found"
    return api._gripper_handler._gripper._calibration_offset.offset  # type: ignore[union-attr]


def set_gripper_offset_ot3(api: OT3API, offset: Point) -> None:
    """Set gripper offset OT3."""
    assert api.has_gripper, "No gripper found"
    api._gripper_handler._gripper._calibration_offset.offset = offset  # type: ignore[union-attr]


def get_slot_size() -> Point:
    """Get OT3 Slot Size."""
    deck = load_deck("ot3_standard", version=3)
    slots = deck["locations"]["orderedSlots"]
    bounding_box = slots[0]["boundingBox"]
    return Point(
        x=bounding_box["xDimension"],
        y=bounding_box["yDimension"],
        z=bounding_box["zDimension"],
    )


def get_default_tip_length(volume: int) -> float:
    """Get default tip length for specified volume of tip."""
    return TIP_LENGTH_LOOKUP[volume] - TIP_LENGTH_OVERLAP


def get_slot_bottom_left_position_ot3(slot: int) -> Point:
    """Get slot bottom-left position."""
    deck = load_deck("ot3_standard", version=3)
    slots = deck["locations"]["orderedSlots"]
    s = slots[slot - 1]
    assert s["id"] == str(slot)
    return Point(*s["position"])


def get_slot_top_left_position_ot3(slot: int) -> Point:
    """Get slot top-left position."""
    bottom_left = get_slot_bottom_left_position_ot3(slot)
    slot_size = get_slot_size()
    return bottom_left + Point(y=slot_size.y)


def get_theoretical_a1_position(slot: int, labware: str) -> Point:
    """Get the theoretical A1 position of a labware in a slot."""
    labware_def = load_labware(loadname=labware, version=1)
    dims = labware_def["dimensions"]
    well_a1 = labware_def["wells"]["A1"]
    a1_pos = Point(x=well_a1["x"], y=well_a1["y"], z=dims["zDimension"])
    slot_pos = get_slot_bottom_left_position_ot3(slot)
    y_shift_from_clips = (get_slot_size().y - dims["yDimension"]) * 0.5
    return slot_pos + a1_pos + Point(y=y_shift_from_clips)


def get_slot_calibration_square_position_ot3(slot: int) -> Point:
    """Get slot calibration block position."""
    slot_top_left = get_slot_top_left_position_ot3(slot)
    calib_sq_offset = CALIBRATION_SQUARE_EVT.top_left_offset
    return slot_top_left + calib_sq_offset


def get_pipette_serial_ot3(pipette: Union[PipetteOT2, PipetteOT3]) -> str:
    """Get pipette serial number."""
    model = pipette.model
    volume = model.split("_")[0].replace("p", "")
    volume = "1K" if volume == "1000" else volume
    channels = "S" if "single" in model else "M"
    version = model.split("v")[-1].strip().replace(".", "")
    assert pipette.pipette_id, f"no pipette_id found for pipette: {pipette}"
    if "P" in pipette.pipette_id:
        id = pipette.pipette_id[7:]  # P1KSV33yyyymmddAxx
    else:
        id = pipette.pipette_id
    return f"P{volume}{channels}V{version}{id}"
