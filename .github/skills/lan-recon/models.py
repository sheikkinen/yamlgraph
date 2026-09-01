"""Pydantic schema for LAN host inventory (FR-945).

REQ-YG-635. Boundary contract: `LanHostInventory` is the single typed
parse of the inventory.ps1 JSON output; no untyped dict crosses the
boundary. Every command's success or failure is represented by a typed
field; `errors` collects per-field diagnostics rather than silently
omitting data.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class CpuInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    cores: int
    logical_processors: int
    max_clock_mhz: int


class GpuInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    adapter_ram_bytes: int | None = None
    driver_version: str | None = None


class DiskInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drive: str
    free_bytes: int
    used_bytes: int


class WslInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_distribution: str | None = None
    default_version: int | None = None
    raw: str


class ServiceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    status: str
    start_type: str


class PortInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_address: str
    local_port: int
    process_name: str | None = None


class FieldError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    message: str


class LanHostInventory(BaseModel):
    """Frozen inventory schema returned by inventory.ps1 via recon.py.

    Every field is required; when a Windows command cannot supply data,
    an entry is added to `errors` and the field carries an explicit
    empty/None value. No silent omission.
    """

    model_config = ConfigDict(extra="forbid")

    requested_target: str
    resolved_address: IPvAnyAddress
    computer_name: str
    os_version: str
    manufacturer: str
    model: str
    total_memory_bytes: int
    logical_processors: int
    cpu: CpuInfo
    gpus: list[GpuInfo] = Field(default_factory=list)
    disks: list[DiskInfo] = Field(default_factory=list)
    python_native: str | None = None
    py_launcher: list[str] = Field(default_factory=list)
    wsl: WslInfo | None = None
    openssh_server_state: Literal["Installed", "NotPresent", "Unknown"]
    sshd_service: ServiceInfo | None = None
    lm_studio_cli_present: bool
    lm_studio_service: ServiceInfo | None = None
    listening_ports: list[PortInfo] = Field(default_factory=list)
    admin: bool
    remote_management_users_member: bool
    probe_started_at: datetime
    probe_ended_at: datetime
    errors: list[FieldError] = Field(default_factory=list)
