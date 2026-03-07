"""Column mapping configuration — load, store, and detect bill types."""

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger("pharmgmt.parsing")

MAPPINGS_DIR = Path(__file__).parent / "mappings"


@dataclass
class MappingConfig:
    """Configuration for mapping a specific bill type to canonical schema."""

    bill_type: str
    display_name: str
    detect_keywords: list[str] = field(default_factory=list)
    header_aliases: dict[str, list[str]] = field(default_factory=dict)
    skip_patterns: list[str] = field(default_factory=list)
    date_columns: list[str] = field(default_factory=list)
    money_columns: list[str] = field(default_factory=list)
    qty_columns: list[str] = field(default_factory=list)


def load_mapping(yaml_path: str | Path) -> MappingConfig:
    """Load a single mapping config from a YAML file.

    Args:
        yaml_path: Path to the YAML config file

    Returns:
        MappingConfig instance
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return MappingConfig(
        bill_type=data["bill_type"],
        display_name=data.get("display_name", data["bill_type"]),
        detect_keywords=data.get("detect_keywords", []),
        header_aliases=data.get("header_aliases", {}),
        skip_patterns=data.get("skip_patterns", []),
        date_columns=data.get("date_columns", []),
        money_columns=data.get("money_columns", []),
        qty_columns=data.get("qty_columns", []),
    )


def load_all_mappings(mappings_dir: str | Path | None = None) -> list[MappingConfig]:
    """Load all mapping configs from the mappings directory.

    Args:
        mappings_dir: Directory containing YAML mapping files (default: built-in)

    Returns:
        List of MappingConfig instances
    """
    if mappings_dir is None:
        mappings_dir = MAPPINGS_DIR

    mappings_dir = Path(mappings_dir)
    configs = []

    for yaml_file in sorted(mappings_dir.glob("*.yaml")):
        try:
            config = load_mapping(yaml_file)
            configs.append(config)
            logger.debug("Loaded mapping: %s from %s", config.bill_type, yaml_file.name)
        except Exception as e:
            logger.warning("Failed to load mapping %s: %s", yaml_file.name, e)

    logger.info("Loaded %d mapping configs", len(configs))
    return configs


def detect_bill_type(
    text: str,
    table_headers: list[str] | None = None,
    configs: list[MappingConfig] | None = None,
) -> MappingConfig | None:
    """Auto-detect bill type from PDF text and/or table headers.

    Scans text for detect_keywords. Returns the config with the most keyword matches.

    Args:
        text: Full text extracted from the PDF
        table_headers: Optional list of column header strings from the first table
        configs: Optional pre-loaded configs (loaded automatically if None)

    Returns:
        Best matching MappingConfig, or None if no match
    """
    if configs is None:
        configs = load_all_mappings()

    if not configs:
        return None

    text_lower = text.lower() if text else ""
    headers_lower = " ".join(h.lower() for h in table_headers) if table_headers else ""
    combined = f"{text_lower} {headers_lower}"

    best_config = None
    best_score = 0

    for config in configs:
        score = 0
        for keyword in config.detect_keywords:
            if keyword.lower() in combined:
                score += 1

        if score > best_score:
            best_score = score
            best_config = config

    if best_config and best_score > 0:
        logger.info(
            "Detected bill type: %s (score: %d/%d keywords)",
            best_config.bill_type, best_score, len(best_config.detect_keywords),
        )
        return best_config

    logger.warning("Could not detect bill type from text")
    return None
