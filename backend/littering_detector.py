"""
Littering Detection — Core Logic Module.

Uses a state machine per garbage object to infer littering events
from spatial + temporal changes in person-garbage relationships.

States:
    UNTRACKED → ATTACHED → DETACHING → MONITORING → LITTERING_CONFIRMED
"""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import time

from tracker import TrackedObject
from spatial_analyzer import euclidean_distance, find_nearest_person, is_near_dustbin
import config


class GarbageStateEnum(Enum):
    """Possible states for a tracked garbage object."""
    UNTRACKED = "UNTRACKED"
    ATTACHED = "ATTACHED"
    DETACHING = "DETACHING"
    MONITORING = "MONITORING"
    LITTERING_CONFIRMED = "LITTERING_CONFIRMED"


@dataclass
class GarbageState:
    """Tracks the temporal state of a single garbage object."""
    garbage_id: int
    state: GarbageStateEnum = GarbageStateEnum.UNTRACKED
    associated_person_id: Optional[int] = None

    # History buffers
    distance_history: deque = field(default_factory=lambda: deque(maxlen=config.BUFFER_SIZE))
    position_history: deque = field(default_factory=lambda: deque(maxlen=config.BUFFER_SIZE))

    # Counters
    stationary_count: int = 0
    separation_count: int = 0

    # Metadata
    first_seen_time: float = field(default_factory=time.time)
    last_bbox: Optional[Tuple[int, int, int, int]] = None
    person_last_bbox: Optional[Tuple[int, int, int, int]] = None


@dataclass
class LitteringEvent:
    """Represents a confirmed littering event."""
    garbage_id: int
    person_id: int
    timestamp: float
    garbage_bbox: Tuple[int, int, int, int]
    person_last_bbox: Optional[Tuple[int, int, int, int]]
    confidence: float

    def __str__(self):
        return (
            f"🚨 LITTERING DETECTED | Person #{self.person_id} | "
            f"Garbage #{self.garbage_id} | "
            f"Confidence: {self.confidence:.2f} | "
            f"Time: {time.strftime('%H:%M:%S', time.localtime(self.timestamp))}"
        )


class LitteringDetector:
    """
    Core littering inference engine.
    
    Maintains a state machine per garbage object and transitions based on
    spatial + temporal relationships with tracked persons.
    """

    def __init__(self):
        self.garbage_states: Dict[int, GarbageState] = {}
        self.confirmed_events: List[LitteringEvent] = []

        # Load thresholds from config
        self.proximity_threshold = config.PROXIMITY_THRESHOLD
        self.separation_threshold = config.SEPARATION_THRESHOLD
        self.velocity_threshold = config.VELOCITY_THRESHOLD
        self.stationary_frames = config.STATIONARY_FRAMES
        self.moving_away_frames = config.PERSON_MOVING_AWAY_FRAMES
        self.dustbin_proximity = config.DUSTBIN_PROXIMITY

    def update(
        self,
        tracked_persons: Dict[int, TrackedObject],
        tracked_garbage: Dict[int, TrackedObject],
        tracked_dustbins: Dict[int, TrackedObject],
    ) -> List[LitteringEvent]:
        """
        Process one frame of tracked objects and return any new littering events.
        
        Args:
            tracked_persons: Currently tracked persons {id: TrackedObject}
            tracked_garbage: Currently tracked garbage {id: TrackedObject}
            tracked_dustbins: Currently tracked dustbins {id: TrackedObject}
            
        Returns:
            List of new LitteringEvent objects detected this frame
        """
        new_events = []
        active_garbage_ids = set(tracked_garbage.keys())

        # Clean up states for garbage that's no longer tracked
        stale_ids = [gid for gid in self.garbage_states if gid not in active_garbage_ids]
        for gid in stale_ids:
            del self.garbage_states[gid]

        # Process each garbage object
        for garbage_id, garbage_obj in tracked_garbage.items():
            # Initialize state if new
            if garbage_id not in self.garbage_states:
                self.garbage_states[garbage_id] = GarbageState(garbage_id=garbage_id)

            state = self.garbage_states[garbage_id]

            # Skip if already confirmed (don't re-trigger)
            if state.state == GarbageStateEnum.LITTERING_CONFIRMED:
                continue

            # Skip if garbage is near a dustbin (legitimate disposal)
            if is_near_dustbin(garbage_obj.centroid, tracked_dustbins, self.dustbin_proximity):
                state.state = GarbageStateEnum.UNTRACKED
                state.associated_person_id = None
                state.stationary_count = 0
                state.separation_count = 0
                continue

            # Find nearest person
            nearest_person_id, distance = find_nearest_person(
                garbage_obj.centroid, tracked_persons
            )

            # Update history
            state.distance_history.append(distance)
            state.position_history.append(garbage_obj.centroid)
            state.last_bbox = garbage_obj.bbox

            # Store person bbox for evidence
            if nearest_person_id is not None and nearest_person_id in tracked_persons:
                state.person_last_bbox = tracked_persons[nearest_person_id].bbox

            # Run state machine transitions
            event = self._transition(state, nearest_person_id, distance, garbage_obj)
            if event:
                new_events.append(event)
                self.confirmed_events.append(event)

        return new_events

    def _transition(
        self,
        state: GarbageState,
        nearest_person_id: Optional[int],
        distance: float,
        garbage_obj: TrackedObject,
    ) -> Optional[LitteringEvent]:
        """
        Run state machine transition for a single garbage object.
        Returns a LitteringEvent if littering is confirmed.
        """
        prev_state = state.state

        # ── UNTRACKED → ATTACHED ─────────────────────────────────
        if state.state == GarbageStateEnum.UNTRACKED:
            if nearest_person_id is not None and distance < self.proximity_threshold:
                state.state = GarbageStateEnum.ATTACHED
                state.associated_person_id = nearest_person_id
                state.stationary_count = 0
                state.separation_count = 0

        # ── ATTACHED → DETACHING ─────────────────────────────────
        elif state.state == GarbageStateEnum.ATTACHED:
            if len(state.distance_history) >= 2:
                # Check if distance is increasing (person moving away)
                if state.distance_history[-1] > state.distance_history[-2]:
                    state.state = GarbageStateEnum.DETACHING
            
            # If person disappears or garbage moves far, re-evaluate
            if distance > self.separation_threshold:
                state.state = GarbageStateEnum.DETACHING

        # ── DETACHING → MONITORING ────────────────────────────────
        elif state.state == GarbageStateEnum.DETACHING:
            velocity = self._compute_velocity(state.position_history)

            if velocity < self.velocity_threshold:
                state.stationary_count += 1
            else:
                state.stationary_count = 0

            # If garbage becomes stationary, start monitoring
            if state.stationary_count >= self.stationary_frames:
                state.state = GarbageStateEnum.MONITORING
                state.separation_count = 0

            # If garbage goes back near person, revert to attached
            if distance < self.proximity_threshold:
                state.state = GarbageStateEnum.ATTACHED
                state.stationary_count = 0

        # ── MONITORING → LITTERING_CONFIRMED ──────────────────────
        elif state.state == GarbageStateEnum.MONITORING:
            # Person must be far enough away for enough frames
            if distance > self.separation_threshold:
                state.separation_count += 1
            else:
                # Person came back — could be picking it up
                state.separation_count = max(0, state.separation_count - 1)

            # If person still far away for N frames, confirm littering
            if state.separation_count >= self.moving_away_frames:
                state.state = GarbageStateEnum.LITTERING_CONFIRMED

                event = LitteringEvent(
                    garbage_id=state.garbage_id,
                    person_id=state.associated_person_id,
                    timestamp=time.time(),
                    garbage_bbox=garbage_obj.bbox,
                    person_last_bbox=state.person_last_bbox,
                    confidence=garbage_obj.confidence,
                )

                if config.LOG_STATE_TRANSITIONS:
                    print(str(event))

                return event

            # If garbage starts moving again, go back to detaching
            velocity = self._compute_velocity(state.position_history)
            if velocity >= self.velocity_threshold:
                state.state = GarbageStateEnum.DETACHING
                state.stationary_count = 0

        # Log state transition
        if config.LOG_STATE_TRANSITIONS and state.state != prev_state:
            print(
                f"[Littering] Garbage #{state.garbage_id}: "
                f"{prev_state.value} → {state.state.value} "
                f"(person #{state.associated_person_id}, dist={distance:.0f}px)"
            )

        return None

    def _compute_velocity(self, positions: deque) -> float:
        """
        Compute average velocity (px/frame) from recent positions.
        Uses last 3 positions for smoothing.
        """
        if len(positions) < 2:
            return 0.0

        # Use last 3 positions for a smoothed velocity
        recent = list(positions)[-3:]
        total_dist = 0.0
        for i in range(1, len(recent)):
            total_dist += euclidean_distance(recent[i - 1], recent[i])

        return total_dist / (len(recent) - 1)

    def get_active_states(self) -> Dict[int, str]:
        """Return current states for all tracked garbage (for display)."""
        return {gid: gs.state.value for gid, gs in self.garbage_states.items()}

    def reset(self):
        """Clear all states."""
        self.garbage_states.clear()
        self.confirmed_events.clear()
