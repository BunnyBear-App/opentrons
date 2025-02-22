from .types import OT3Mount


class OutOfBoundsMove(RuntimeError):
    def __init__(self, message: str):
        self.message = message
        super().__init__()

    def __str__(self) -> str:
        return f"OutOfBoundsMove: {self.message}"

    def __repr__(self) -> str:
        return f"<{str(self.__class__)}: {self.message}>"


class ExecutionCancelledError(RuntimeError):
    pass


class MustHomeError(RuntimeError):
    pass


class NoTipAttachedError(RuntimeError):
    pass


class TipAttachedError(RuntimeError):
    pass


class InvalidMoveError(ValueError):
    pass


class GripperNotAttachedError(Exception):
    """An error raised if a gripper is accessed that is not attached."""

    pass


class FirmwareUpdateRequired(RuntimeError):
    """An error raised when the firmware of the submodules needs to be updated."""

    pass


class InvalidPipetteName(KeyError):
    """Raised for an invalid pipette."""

    def __init__(self, name: int, mount: OT3Mount) -> None:
        self.name = name
        self.mount = mount

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: name={self.name} mount={self.mount}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: Pipette name key {self.name} on mount {self.mount.name} is not valid"


class InvalidPipetteModel(KeyError):
    """Raised for a pipette with an unknown model."""

    def __init__(self, name: str, model: str, mount: OT3Mount) -> None:
        self.name = name
        self.model = model
        self.mount = mount

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: name={self.name}, model={self.model}, mount={self.mount}>"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.name} on {self.mount.name} has an unknown model {self.model}"
