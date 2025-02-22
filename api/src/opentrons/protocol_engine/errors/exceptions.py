"""Protocol engine exceptions."""


class ProtocolEngineError(RuntimeError):
    """Base Protocol Engine error class."""


class UnexpectedProtocolError(ProtocolEngineError):
    """Raised when an unexpected error occurs.

    This error is indicative of a software bug. If it happens, it means an
    exception was raised somewhere in the stack and it was not properly caught
    and wrapped.
    """

    def __init__(self, original_error: Exception) -> None:
        """Initialize an UnexpectedProtocolError with an original error."""
        super().__init__(str(original_error))
        self.original_error: Exception = original_error


# TODO(mc, 2020-10-18): differentiate between pipette missing vs incorrect.
# By comparison, loadModule uses ModuleAlreadyPresentError and ModuleNotAttachedError.
class FailedToLoadPipetteError(ProtocolEngineError):
    """Raised when a LoadPipette command fails.

    This failure may be caused by:
    - An incorrect pipette already attached to the mount
    - A missing pipette on the requested mount
    """


# TODO(mc, 2020-10-18): differentiate between pipette missing vs incorrect
class PipetteNotAttachedError(ProtocolEngineError):
    """Raised when an operation's required pipette is not attached."""


class TipNotAttachedError(ProtocolEngineError):
    """Raised when an operation's required pipette tip is not attached."""


class TipAttachedError(ProtocolEngineError):
    """Raised when a tip shouldn't be attached, but is."""


class CommandDoesNotExistError(ProtocolEngineError):
    """Raised when referencing a command that does not exist."""


class PipetteTipInfoNotFoundError(ProtocolEngineError):
    """Raised when fetching information (like tiprack id) of attached tip."""


class LabwareNotLoadedError(ProtocolEngineError):
    """Raised when referencing a labware that has not been loaded."""


class LabwareNotLoadedOnModuleError(ProtocolEngineError):
    """Raised when referencing a labware on a module that has not been loaded."""


class LabwareNotOnDeckError(ProtocolEngineError):
    """Raised when a labware can't be used because it's off-deck."""


class LiquidDoesNotExistError(ProtocolEngineError):
    """Raised when referencing a liquid that has not been loaded."""


class LabwareDefinitionDoesNotExistError(ProtocolEngineError):
    """Raised when referencing a labware definition that does not exist."""


class LabwareOffsetDoesNotExistError(ProtocolEngineError):
    """Raised when referencing a labware offset that does not exist."""


class LabwareIsNotTipRackError(ProtocolEngineError):
    """Raised when trying to use a regular labware as a tip rack."""


class LabwareIsTipRackError(ProtocolEngineError):
    """Raised when trying to use a command not allowed on tip rack."""


class TouchTipDisabledError(ProtocolEngineError):
    """Raised when touch tip is used on well with touchTipDisabled quirk."""


class WellDoesNotExistError(ProtocolEngineError):
    """Raised when referencing a well that does not exist."""


class PipetteNotLoadedError(ProtocolEngineError):
    """Raised when referencing a pipette that has not been loaded."""


class ModuleNotLoadedError(ProtocolEngineError):
    """Raised when referencing a module that has not been loaded."""


class ModuleNotOnDeckError(ProtocolEngineError):
    """Raised when trying to use a module that is loaded off the deck."""


class SlotDoesNotExistError(ProtocolEngineError):
    """Raised when referencing a deck slot that does not exist."""


# TODO(mc, 2020-11-06): flesh out with structured data to replicate
# existing LabwareHeightError
class FailedToPlanMoveError(ProtocolEngineError):
    """Raised when a requested movement could not be planned."""


class MustHomeError(ProtocolEngineError):
    """Raised when motors must be homed due to unknown current position."""


class SetupCommandNotAllowedError(ProtocolEngineError):
    """Raised when adding a setup command to a non-idle/non-paused engine."""


class PauseNotAllowedError(ProtocolEngineError):
    """Raised when attempting to pause a run that is not running."""


class RunStoppedError(ProtocolEngineError):
    """Raised when attempting to interact with a stopped engine."""


class ModuleNotAttachedError(ProtocolEngineError):
    """Raised when a requested module is not attached."""


class ModuleAlreadyPresentError(ProtocolEngineError):
    """Raised when a module is already present in a requested location."""


class WrongModuleTypeError(ProtocolEngineError):
    """Raised when performing a module action on the wrong kind of module."""


class ThermocyclerNotOpenError(ProtocolEngineError):
    """Raised when trying to move to a labware that's in a closed Thermocycler."""


class RobotDoorOpenError(ProtocolEngineError):
    """Raised when executing a protocol command when a robot door is open."""


class PipetteMovementRestrictedByHeaterShakerError(ProtocolEngineError):
    """Raised when trying to move to labware that's restricted by a module."""


class HeaterShakerLabwareLatchNotOpenError(ProtocolEngineError):
    """Raised when Heater-Shaker latch is not open when it is expected to be so."""


class EngageHeightOutOfRangeError(ProtocolEngineError):
    """Raised when a Magnetic Module engage height is out of bounds."""


class NoMagnetEngageHeightError(ProtocolEngineError):
    """Raised if a Magnetic Module engage height is missing."""


class NoTargetTemperatureSetError(ProtocolEngineError):
    """Raised when awaiting temperature when no target was set."""


class InvalidTargetTemperatureError(ProtocolEngineError):
    """Raised when attempting to set an invalid target temperature."""


class InvalidBlockVolumeError(ProtocolEngineError):
    """Raised when attempting to set an invalid block max volume."""


class InvalidTargetSpeedError(ProtocolEngineError):
    """Raised when attempting to set an invalid target speed."""


class CannotPerformModuleAction(ProtocolEngineError):
    """Raised when trying to perform an illegal hardware module action."""


class ProtocolCommandFailedError(ProtocolEngineError):
    """Raised if a fatal command execution error has occurred."""


class HardwareNotSupportedError(ProtocolEngineError):
    """Raised when executing a command on the wrong hardware."""


class GripperNotAttachedError(ProtocolEngineError):
    """Raised when executing a gripper action without an attached gripper."""


class LabwareMovementNotAllowedError(ProtocolEngineError):
    """Raised when attempting an illegal labware movement."""


class LocationIsOccupiedError(ProtocolEngineError):
    """Raised when attempting to place labware in a non-empty location."""


class FirmwareUpdateRequired(ProtocolEngineError):
    """Raised when the firmware needs to be updated."""


class PipetteNotReadyToAspirateError(ProtocolEngineError):
    """Raised when the pipette is not ready to aspirate."""
