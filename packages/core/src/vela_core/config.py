from datetime import date
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from yaml import YAMLError

ConfigModel = TypeVar("ConfigModel", bound=BaseModel)


class ConfigError(Exception):
    """Raised when a Vela configuration file cannot be loaded."""

    def __init__(self, message: str, *, path: Path) -> None:
        super().__init__(message)
        self.path = path


class ETFConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exchange: str
    symbol: str
    name: str
    category: str | None = None
    is_active: bool = True
    inception_date: date | None = None
    listing_date: date | None = None


class ETFPoolConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pool_id: str
    version: int
    description: str | None = None
    provider: str
    currency: str
    etfs: list[ETFConfig] = Field(min_length=1)

    @field_validator("etfs")
    @classmethod
    def validate_unique_etfs(cls, etfs: list[ETFConfig]) -> list[ETFConfig]:
        seen: set[tuple[str, str]] = set()
        for etf in etfs:
            key = (etf.exchange, etf.symbol)
            if key in seen:
                raise ValueError(f"duplicate ETF entry: {etf.exchange} {etf.symbol}")
            seen.add(key)
        return etfs

    @model_validator(mode="after")
    def validate_active_listing_dates(self) -> "ETFPoolConfig":
        missing = [
            f"{etf.exchange}:{etf.symbol}"
            for etf in self.etfs
            if etf.is_active and etf.listing_date is None
        ]
        if missing:
            raise ValueError("active ETF entries require listing_date: " + ", ".join(missing))
        return self


def load_etf_pool_config(path: str | Path) -> ETFPoolConfig:
    return load_yaml_config(path, ETFPoolConfig)


def load_yaml_config(path: str | Path, model_type: type[ConfigModel]) -> ConfigModel:
    config_path = Path(path)
    data = _load_yaml(config_path)
    try:
        return model_type.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(config_path, exc), path=config_path) from exc


def _load_yaml(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as file:
            return yaml.safe_load(file)
    except OSError as exc:
        raise ConfigError(f"Failed to read configuration file {path}: {exc}", path=path) from exc
    except YAMLError as exc:
        raise ConfigError(
            f"Failed to parse YAML configuration file {path}: {exc}",
            path=path,
        ) from exc


def _format_validation_error(path: Path, error: ValidationError) -> str:
    details = []
    for item in error.errors():
        field_path = _format_error_location(item["loc"])
        details.append(f"{field_path}: {item['msg']}")
    return f"Failed to validate configuration file {path}: {'; '.join(details)}"


def _format_error_location(location: tuple[int | str, ...]) -> str:
    if not location:
        return "<root>"
    return ".".join(str(part) for part in location)
