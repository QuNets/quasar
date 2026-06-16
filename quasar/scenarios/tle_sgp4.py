"""TLE/SGP4 scenario source placeholder for QUASAR."""

from __future__ import annotations

from typing import Iterable, Tuple

from quasar.satellite.models import GroundStation, LinkState
from quasar.scenarios.base import ScenarioFrame

try:
    from sgp4.api import Satrec
except ImportError:  # pragma: no cover - exercised through monkeypatch tests
    Satrec = None


class TLESGP4Source:
    """Reserve the CandidateLinkSource interface for TLE/SGP4 data.

    Stage 9A keeps full propagation out of scope. The optional ``sgp4``
    dependency is not required unless this source is used.
    """

    def __init__(
        self,
        tle_lines: Iterable[str] = (),
        ground_stations: Iterable[GroundStation] = (),
    ) -> None:
        self.tle_lines = tuple(tle_lines)
        self.ground_stations = tuple(ground_stations)

    def frame_at(self, time: float) -> ScenarioFrame:
        """Return a TLE-driven frame when full propagation is implemented."""

        if time < 0:
            raise ValueError("time must be non-negative")
        self._require_sgp4()
        raise NotImplementedError(
            "TLESGP4Source reserves the scenario interface; full TLE/SGP4 "
            "propagation is not implemented in Stage 9A."
        )

    def candidate_links_at(self, time: float) -> Tuple[LinkState, ...]:
        """Return candidate links for a simulation time."""

        return self.frame_at(time).candidate_links

    @staticmethod
    def _require_sgp4() -> None:
        if Satrec is None:
            raise ImportError(
                "TLESGP4Source requires the optional 'sgp4' package. "
                "Install sgp4 to use TLE-based propagation."
            )
