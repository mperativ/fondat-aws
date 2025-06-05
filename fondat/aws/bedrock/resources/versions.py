"""Resource for managing agent versions."""

from collections.abc import Iterable

from fondat.aws.client import Config
from fondat.security import Policy

from .generic_resources import GenericVersionResource

__all__ = ["VersionsResource"]


class VersionsResource(GenericVersionResource):
    """
    Resource for managing agent versions.
    This is a wrapper around GenericVersionResource that maintains the original API.
    """

    def __init__(
        self,
        agent_id: str,
        *,
        config_agent: Config | None = None,
        policies: Iterable[Policy] | None = None,
        cache_size: int = 100,
        cache_expire: int | float = 300,
    ):
        super().__init__(
            agent_id,
            id_field="agentId",
            list_method="list_agent_versions",
            get_method="get_agent_version",
            items_key="agentVersionSummaries",
            config=config_agent,
            policies=policies,
            cache_size=cache_size,
            cache_expire=cache_expire,
        )
