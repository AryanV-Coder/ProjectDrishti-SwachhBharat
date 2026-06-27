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
    monitoring_frames: int = 0     # Total frames spent in MONITORING — triggers time-based confirmation

    # Transition stability counters (debouncing — prevents jitter-driven false transitions)
    consecutive_distance_increases: int = 0  # Frames of sustained distance growth (ATTACHED → DETACHING guard)
    reattach_count: int = 0                   # Frames of sustained proximity in DETACHING (prevents premature reversion)

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

        # Memory of recently-lost garbage states (for ID reassignment on drops)
        # Each entry: {"state": GarbageState, "last_centroid": (cx,cy), "frames_since_lost": int}
        self.recently_lost: List[dict] = []

        # Per-person centroid history — used to detect whether a person was moving
        # before garbage appeared near them. Prevents false ATTACHED on sitting persons.
        self.person_history: Dict[int, deque] = {}

        # Load thresholds from config
        self.proximity_threshold = config.PROXIMITY_THRESHOLD
        self.separation_threshold = config.SEPARATION_THRESHOLD
        self.velocity_threshold = config.VELOCITY_THRESHOLD
        self.stationary_frames = config.STATIONARY_FRAMES
        self.moving_away_frames = config.PERSON_MOVING_AWAY_FRAMES
        self.monitoring_timeout = config.MONITORING_TIMEOUT_FRAMES
        self.dustbin_proximity = config.DUSTBIN_PROXIMITY
        self.state_memory_frames = config.GARBAGE_STATE_MEMORY_FRAMES

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

        # ── Update per-person movement history ───────────────────────────
        # Used by _person_was_moving() to gate UNTRACKED → ATTACHED.
        for pid, person_obj in tracked_persons.items():
            if pid not in self.person_history:
                self.person_history[pid] = deque(maxlen=config.PERSON_HISTORY_FRAMES)
            self.person_history[pid].append(person_obj.centroid)
        # Prune history for persons no longer in the scene
        for pid in [p for p in list(self.person_history) if p not in tracked_persons]:
            del self.person_history[pid]

        # Save states of garbage that just disappeared (for state inheritance)
        stale_ids = [gid for gid in self.garbage_states if gid not in active_garbage_ids]
        for gid in stale_ids:
            lost_state = self.garbage_states[gid]
            # Only remember if it had a meaningful state (was attached to someone)
            if lost_state.state != GarbageStateEnum.UNTRACKED and lost_state.associated_person_id is not None:
                last_centroid = lost_state.position_history[-1] if lost_state.position_history else None
                if last_centroid:
                    self.recently_lost.append({
                        "state": lost_state,
                        "last_centroid": last_centroid,
                        "frames_since_lost": 0,
                    })
                    if config.LOG_STATE_TRANSITIONS:
                        print(
                            f"[Littering] Garbage #{gid} lost from tracking — "
                            f"remembering state {lost_state.state.value} "
                            f"(person #{lost_state.associated_person_id})"
                        )
            del self.garbage_states[gid]

        # Age out old memories
        for mem in self.recently_lost:
            mem["frames_since_lost"] += 1
        self.recently_lost = [m for m in self.recently_lost if m["frames_since_lost"] <= self.state_memory_frames]

        # ── Continue monitoring recently-lost garbage still in MONITORING ─
        # When YOLO loses the garbage during MONITORING (occlusion, motion blur,
        # person walking over it), separation_count was frozen at 0. We continue
        # updating it using the person's live position vs the last known garbage
        # centroid. This is the primary fix for "0 events" on short videos.
        for mem in list(self.recently_lost):
            old_state = mem["state"]
            if old_state.state != GarbageStateEnum.MONITORING:
                continue
            assoc_pid = old_state.associated_person_id
            if assoc_pid not in tracked_persons:
                continue

            person = tracked_persons[assoc_pid]
            assoc_dist = euclidean_distance(mem["last_centroid"], person.centroid)
            _, sep_thresh = self._compute_thresholds(person.bbox)

            old_state.monitoring_frames += 1

            if assoc_dist > sep_thresh:
                old_state.separation_count += 1
            else:
                old_state.separation_count = max(0, old_state.separation_count - 1)

            # Two confirmation paths:
            #   A) Person walked far enough away (separation_count)
            #   B) Garbage sat on floor long enough without pickup (monitoring_frames)
            confirmed = (
                old_state.separation_count >= self.moving_away_frames
                or old_state.monitoring_frames >= self.monitoring_timeout
            )
            confirm_reason = (
                "person walked away"
                if old_state.separation_count >= self.moving_away_frames
                else "timeout"
            )

            if config.LOG_STATE_TRANSITIONS:
                print(
                    f"[Littering] Garbage #{old_state.garbage_id} (untracked, MONITORING): "
                    f"person #{assoc_pid} at {assoc_dist:.0f}px from last pos "
                    f"(sep>{sep_thresh:.0f}px, sep_count={old_state.separation_count}, "
                    f"mon_frames={old_state.monitoring_frames}/{self.monitoring_timeout})"
                )

            if confirmed:
                old_state.state = GarbageStateEnum.LITTERING_CONFIRMED
                event = LitteringEvent(
                    garbage_id=old_state.garbage_id,
                    person_id=assoc_pid,
                    timestamp=time.time(),
                    garbage_bbox=old_state.last_bbox,
                    person_last_bbox=person.bbox,
                    confidence=0.85,
                )
                new_events.append(event)
                self.confirmed_events.append(event)
                self.recently_lost.remove(mem)

                if config.LOG_STATE_TRANSITIONS:
                    print(
                        f"[Littering] Garbage #{old_state.garbage_id}: "
                        f"MONITORING \u2192 LITTERING_CONFIRMED (untracked, {confirm_reason}, "
                        f"person #{assoc_pid}, dist_to_last={assoc_dist:.0f}px)"
                    )

        for garbage_id, garbage_obj in tracked_garbage.items():
            # Initialize state if new
            if garbage_id not in self.garbage_states:
                # Check if this new garbage matches a recently-lost one
                inherited = self._try_inherit_state(garbage_id, garbage_obj, tracked_persons)
                if not inherited:
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

            # Compute distance to the *associated* person specifically.
            # Once attached to someone, we track their distance exclusively —
            # this prevents a stranger walking past from hijacking the state machine.
            assoc_distance = distance
            if (
                state.associated_person_id is not None
                and state.associated_person_id in tracked_persons
            ):
                assoc_distance = euclidean_distance(
                    garbage_obj.centroid,
                    tracked_persons[state.associated_person_id].centroid,
                )

            # Update history with assoc_distance so all transitions react to the right person
            state.distance_history.append(assoc_distance)
            state.position_history.append(garbage_obj.centroid)
            state.last_bbox = garbage_obj.bbox

            # Always store the associated person's *current* bbox for evidence.
            # Falls back to nearest person before association is established.
            evidence_pid = (
                state.associated_person_id
                if state.associated_person_id is not None
                and state.associated_person_id in tracked_persons
                else nearest_person_id
            )
            if evidence_pid is not None and evidence_pid in tracked_persons:
                state.person_last_bbox = tracked_persons[evidence_pid].bbox

            # Reference bbox for adaptive threshold computation
            ref_person_bbox = (
                tracked_persons[evidence_pid].bbox
                if evidence_pid is not None and evidence_pid in tracked_persons
                else None
            )

            # Run state machine transitions
            event = self._transition(state, nearest_person_id, distance, assoc_distance, ref_person_bbox, garbage_obj)
            if event:
                new_events.append(event)
                self.confirmed_events.append(event)

        return new_events

    def _transition(
        self,
        state: GarbageState,
        nearest_person_id: Optional[int],
        distance: float,
        assoc_distance: float,
        ref_person_bbox: Optional[Tuple[int, int, int, int]],
        garbage_obj: TrackedObject,
    ) -> Optional[LitteringEvent]:
        """
        Run state machine transition for a single garbage object.

        Args:
            state: Current GarbageState for this garbage object
            nearest_person_id: ID of the nearest person to the garbage this frame
            distance: Distance (px) to the nearest person
            assoc_distance: Distance (px) to the *associated* person specifically.
                            Equals `distance` until an association is established.
            ref_person_bbox: Bounding box of the reference person (for adaptive thresholds)
            garbage_obj: The tracked garbage object

        Returns:
            A LitteringEvent if littering is confirmed, else None.
        """
        prev_state = state.state

        # Compute adaptive thresholds based on the person's apparent size in frame.
        # This makes the system resolution-agnostic — 4K CCTV vs 720p webcam.
        proximity_threshold, separation_threshold = self._compute_thresholds(ref_person_bbox)

        # ── UNTRACKED → ATTACHED ─────────────────────────────────
        if state.state == GarbageStateEnum.UNTRACKED:
            if nearest_person_id is not None and distance < proximity_threshold:
                # Sitting-person guard: only attach if the person was recently
                # moving. A stationary person near pre-existing floor garbage
                # has not "picked it up" — attaching it would cause a false alarm.
                if self._person_was_moving(nearest_person_id):
                    state.state = GarbageStateEnum.ATTACHED
                    state.associated_person_id = nearest_person_id
                    state.stationary_count = 0
                    state.separation_count = 0
                    state.consecutive_distance_increases = 0
                    state.reattach_count = 0
                elif config.LOG_STATE_TRANSITIONS:
                    print(
                        f"[Littering] Garbage #{state.garbage_id}: "
                        f"UNTRACKED → ATTACHED blocked — "
                        f"person #{nearest_person_id} appears stationary (sitting guard)"
                    )

        # ── ATTACHED ─────────────────────────────────────────────
        elif state.state == GarbageStateEnum.ATTACHED:
            # Track consecutive frames where the associated person's distance is
            # increasing. A single-frame jitter must not trigger DETACHING.
            if len(state.distance_history) >= 2:
                if state.distance_history[-1] > state.distance_history[-2]:
                    state.consecutive_distance_increases += 1
                else:
                    state.consecutive_distance_increases = 0

            # Sustained separation: N consecutive frames of increasing distance
            if state.consecutive_distance_increases >= 3:
                state.state = GarbageStateEnum.DETACHING
                state.consecutive_distance_increases = 0

            # Hard separation: associated person is clearly far away (no need to wait)
            if assoc_distance > separation_threshold:
                state.state = GarbageStateEnum.DETACHING
                state.consecutive_distance_increases = 0

        # ── DETACHING ────────────────────────────────────────────
        elif state.state == GarbageStateEnum.DETACHING:
            velocity = self._compute_velocity(state.position_history)

            if velocity < self.velocity_threshold:
                state.stationary_count += 1
            else:
                # Soft reset: one velocity spike (YOLO bbox jitter on stationary garbage)
                # does not undo accumulated stillness.
                state.stationary_count = max(0, state.stationary_count - 1)

            # MONITORING takes priority over re-attachment.
            # Stationary garbage — even at the person's feet — is more likely dropped
            # than held. Checking reattach only matters if garbage hasn't settled yet.
            if state.stationary_count >= self.stationary_frames:
                state.state = GarbageStateEnum.MONITORING
                state.separation_count = 0
                state.reattach_count = 0
            else:
                # Re-attachment guard: only revert if garbage is actively MOVING back
                # toward the person (e.g. they picked it up).
                # Stationary garbage near the person's feet must NOT reattach —
                # that is the exact scenario for unreported littering (v1.mp4 bug).
                is_moving = velocity >= self.velocity_threshold
                if is_moving and assoc_distance < proximity_threshold:
                    state.reattach_count += 1
                else:
                    state.reattach_count = max(0, state.reattach_count - 1)

                if state.reattach_count >= 3:
                    state.state = GarbageStateEnum.ATTACHED
                    state.stationary_count = 0
                    state.reattach_count = 0
                    state.consecutive_distance_increases = 0

        # ── MONITORING → LITTERING_CONFIRMED ──────────────────────
        elif state.state == GarbageStateEnum.MONITORING:
            state.monitoring_frames += 1

            # If garbage is picked up and moving again → cancel monitoring, return to DETACHING
            velocity = self._compute_velocity(state.position_history)
            if velocity >= self.velocity_threshold:
                state.state = GarbageStateEnum.DETACHING
                state.stationary_count = 0
                state.monitoring_frames = 0
            else:
                # Path A: person walked far enough away
                if assoc_distance > separation_threshold:
                    state.separation_count += 1
                else:
                    # Person came back (possibly picking it up) — soft decrement
                    state.separation_count = max(0, state.separation_count - 1)

                # Path B: garbage sat on floor long enough without pickup (timeout)
                confirmed = (
                    state.separation_count >= self.moving_away_frames
                    or state.monitoring_frames >= self.monitoring_timeout
                )
                confirm_reason = (
                    "person walked away"
                    if state.separation_count >= self.moving_away_frames
                    else "timeout"
                )

                if confirmed:
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
                        print(
                            f"[Littering] Garbage #{state.garbage_id}: "
                            f"MONITORING → LITTERING_CONFIRMED ({confirm_reason}, "
                            f"mon_frames={state.monitoring_frames}, "
                            f"assoc_dist={assoc_distance:.0f}px)"
                        )

                    return event


        # Log state transition
        if config.LOG_STATE_TRANSITIONS and state.state != prev_state:
            person_h = (
                ref_person_bbox[3] - ref_person_bbox[1] if ref_person_bbox else "?"
            )
            print(
                f"[Littering] Garbage #{state.garbage_id}: "
                f"{prev_state.value} \u2192 {state.state.value} "
                f"(person #{state.associated_person_id}, "
                f"assoc_dist={assoc_distance:.0f}px, "
                f"person_h={person_h}px, "
                f"prox\u2264{proximity_threshold:.0f}px, sep>{separation_threshold:.0f}px)"
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

    def _person_was_moving(self, person_id: int) -> bool:
        """
        Returns True if the person was actively moving in recent frames.

        Used to gate UNTRACKED → ATTACHED. The key insight:
          - A person who was WALKING and just dropped garbage → high velocity history
          - A person who was SITTING near pre-existing garbage → near-zero velocity history

        Newly-tracked persons (< 2 frames of history) are assumed to be moving,
        because they likely just walked into frame.

        Args:
            person_id: ID of the person to check.

        Returns:
            True if the person should be considered as potentially carrying garbage.
        """
        history = self.person_history.get(person_id)
        if history is None or len(history) < 2:
            # Not enough history — assume walking (just entered frame)
            return True

        recent = list(history)
        total_dist = sum(
            euclidean_distance(recent[i - 1], recent[i])
            for i in range(1, len(recent))
        )
        avg_velocity = total_dist / (len(recent) - 1)
        return avg_velocity >= self.velocity_threshold

    def _compute_thresholds(
        self, person_bbox: Optional[Tuple[int, int, int, int]]
    ) -> Tuple[float, float]:
        """
        Compute proximity and separation thresholds normalized to the person's
        bounding box height. Makes the system resolution-agnostic.

        For a person 600px tall on a 4K CCTV feed:
            proximity  = 0.40 × 600 = 240 px
            separation = 0.55 × 600 = 330 px

        For the same person 200px tall on a wide-angle feed:
            proximity  = 0.40 × 200 = 80 px
            separation = 0.55 × 200 = 110 px

        Both represent the same real-world distances.

        Args:
            person_bbox: (x1, y1, x2, y2) of the reference person, or None.

        Returns:
            (proximity_threshold, separation_threshold) in pixels.
        """
        if person_bbox is not None:
            person_height = max(person_bbox[3] - person_bbox[1], 1)
            return (
                person_height * config.PROXIMITY_SCALE,
                person_height * config.SEPARATION_SCALE,
            )
        # Fallback to static pixel values when no person bbox is available
        return self.proximity_threshold, self.separation_threshold

    def _try_inherit_state(
        self,
        new_garbage_id: int,
        garbage_obj: TrackedObject,
        tracked_persons: Dict[int, TrackedObject],
    ) -> bool:
        """
        Check if a newly-appeared garbage object matches a recently-lost one.
        If so, inherit the old state (this handles YOLO losing detection during drops).
        
        Match criteria:
        - The lost garbage was attached to a person
        - The new garbage appeared near that same person OR near the old position
        """
        if not self.recently_lost:
            return False

        best_match = None
        best_dist = float("inf")

        for mem in self.recently_lost:
            old_state = mem["state"]
            old_centroid = mem["last_centroid"]
            old_person_id = old_state.associated_person_id

            # Distance between new garbage and old garbage's last position
            dist_to_old = euclidean_distance(garbage_obj.centroid, old_centroid)

            # Also check if new garbage is near the same person
            near_same_person = False
            if old_person_id is not None and old_person_id in tracked_persons:
                person_centroid = tracked_persons[old_person_id].centroid
                dist_to_person = euclidean_distance(garbage_obj.centroid, person_centroid)
                # Use a wider radius (3x) so thrown garbage that lands far still matches
                near_same_person = dist_to_person < self.proximity_threshold * 3

            # Match if close to old position OR near the same person
            if dist_to_old < config.GARBAGE_MAX_TRACKING_DISTANCE or near_same_person:
                if dist_to_old < best_dist:
                    best_dist = dist_to_old
                    best_match = mem

        if best_match:
            old_state = best_match["state"]

            # Create new state inheriting from the old one
            new_state = GarbageState(garbage_id=new_garbage_id)
            new_state.associated_person_id = old_state.associated_person_id
            new_state.person_last_bbox = old_state.person_last_bbox

            # If the old garbage was ATTACHED or DETACHING, the new one starts as DETACHING
            # (the drop just happened — the garbage separated from the person)
            if old_state.state in (GarbageStateEnum.ATTACHED, GarbageStateEnum.DETACHING):
                new_state.state = GarbageStateEnum.DETACHING
                new_state.stationary_count = old_state.stationary_count
            elif old_state.state == GarbageStateEnum.MONITORING:
                new_state.state = GarbageStateEnum.MONITORING
                new_state.separation_count = old_state.separation_count
            else:
                new_state.state = old_state.state

            self.garbage_states[new_garbage_id] = new_state
            self.recently_lost.remove(best_match)

            if config.LOG_STATE_TRANSITIONS:
                print(
                    f"[Littering] Garbage #{new_garbage_id} inherited state from "
                    f"lost Garbage #{old_state.garbage_id}: {new_state.state.value} "
                    f"(person #{new_state.associated_person_id})"
                )
            return True

        return False

    def get_active_states(self) -> Dict[int, str]:
        """Return current states for all tracked garbage (for display)."""
        return {gid: gs.state.value for gid, gs in self.garbage_states.items()}

    def reset(self):
        """Clear all states."""
        self.garbage_states.clear()
        self.confirmed_events.clear()
        self.recently_lost.clear()
        self.person_history.clear()
