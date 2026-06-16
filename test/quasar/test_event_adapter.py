"""Tests for the QUASAR-to-SimQN event adapter."""

from pathlib import Path

from qns.simulator import Event, Simulator

from quasar.events import EventRecord, EventType, SimQNEventAdapter


def _record() -> EventRecord:
    return EventRecord(
        event_type=EventType.LINK_DROP,
        time=0.25,
        endpoints=("sat-1", "gs-a"),
        reason="demo record",
    )


def test_to_callback_returns_callable_wrapper():
    adapter = SimQNEventAdapter()
    wrapper = adapter.to_callback(_record(), lambda record: None)

    assert callable(wrapper)


def test_callback_wrapper_receives_same_event_record():
    adapter = SimQNEventAdapter()
    record = _record()
    received = []

    wrapper = adapter.to_callback(record, received.append)
    wrapper()

    assert received == [record]
    assert received[0] is record


def test_to_event_returns_simqn_event_with_quasar_name():
    adapter = SimQNEventAdapter()
    simulator = Simulator(0, 1, accuracy=1000)

    event = adapter.to_event(_record(), lambda record: None, simulator)

    assert isinstance(event, Event)
    assert event.name == "QUASAR:LINK_DROP"


def test_to_event_uses_record_time_as_simqn_time():
    adapter = SimQNEventAdapter()
    simulator = Simulator(0, 1, accuracy=1000)

    event = adapter.to_event(_record(), lambda record: None, simulator)

    assert event.t == simulator.time(sec=0.25)
    assert event.t.sec == 0.25


def test_event_invoke_triggers_callback_with_original_record():
    adapter = SimQNEventAdapter()
    simulator = Simulator(0, 1, accuracy=1000)
    record = _record()
    received = []

    event = adapter.to_event(record, received.append, simulator)
    event.invoke()

    assert received == [record]
    assert received[0] is record


def test_schedule_adds_event_to_simulator_pool_and_returns_event():
    adapter = SimQNEventAdapter()
    simulator = Simulator(0, 1, accuracy=1000)
    record = _record()

    event = adapter.schedule(simulator, record, lambda record: None)

    assert isinstance(event, Event)
    assert simulator.total_events == 1


def test_adapter_source_has_no_detection_routing_or_run_loop_logic():
    source = Path("quasar/events/adapter.py").read_text(encoding="utf-8")

    assert "detect_events" not in source
    assert "ThresholdCrossingDetector" not in source
    assert "SDRouter" not in source
    assert "OOSDSPRouter" not in source
    assert "OOSMPRRouter" not in source
    assert "OOSEASRRouter" not in source
    assert "compute_route" not in source
    assert "def run(" not in source
    assert "while" not in source
    assert "polling" not in source
    assert "100 ms" not in source
    assert "route recomputation" not in source
    assert "GRAPH_UPDATE" not in source
