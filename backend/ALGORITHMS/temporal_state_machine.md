# Temporal State Machine (Littering Inference)

A single frame cannot determine intent. To distinguish between someone holding garbage versus someone littering, the system uses a finite state machine that tracks the temporal relationship between a person and a garbage object over multiple frames.

## States and Transition Logic

| State | Condition to Enter | Meaning |
|---|---|---|
| `UNTRACKED` | Default state | Garbage detected but not yet associated with any person |
| `ATTACHED` | Garbage centroid is within `PROXIMITY_THRESHOLD` of a person | A person is carrying the garbage |
| `DETACHING` | Distance between person and garbage is increasing | The person may have dropped the garbage |
| `MONITORING` | Garbage velocity < `VELOCITY_THRESHOLD` for N frames | Garbage has become stationary on the ground |
| `LITTERING_CONFIRMED` | Person remains beyond `SEPARATION_THRESHOLD` for N frames | The person has walked away — littering confirmed |

## State Inheritance Mechanism
The system implements a state inheritance mechanism to address YOLO detection gaps. When YOLO temporarily loses detection of garbage during the drop action (due to motion blur or shape change), and a new garbage ID appears near the same person shortly after, the old state is transferred to the new ID. This prevents the state machine from resetting to `UNTRACKED` during the critical drop moment.
