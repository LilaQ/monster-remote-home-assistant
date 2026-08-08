# Monster Remote for Home Assistant

Local, real-time Home Assistant control and workout telemetry for devices
running Monster Remote.

The integration talks only to Monster Helper on your local network. It never
needs cloud credentials.

## Highlights

- Local push updates over Server-Sent Events
- Automatic reconnect with a low-frequency snapshot fallback
- Current exercise, set, weight, resistance, heart rate and rowing telemetry
- Accepted-rep cable depth/side telemetry and a local H.264 mirror camera
- Session status, timestamps, reps, worked sets and volume
- Helper, Speediance and offset-profile compatibility diagnostics
- Native controls for weight, resistance, modes, rest and workout navigation
- Raw `monster_remote_event` and semantic `monster_remote_activity` events

## Requirements

- Monster Remote Premium
- Monster Helper **2.01.79 or newer** for rep depth and mirror camera
- Home Assistant and Monster Remote on the same local network

## Installation

### HACS

1. Open HACS → Integrations → Custom repositories.
2. Add `https://github.com/LilaQ/monster-remote-home-assistant` as an Integration.
3. Install **Monster Remote** and restart Home Assistant.
4. Go to Settings → Devices & services → Add integration → Monster Remote.
5. Enter the device IP address. Port `8765` normally does not need to be
   changed.

### Manual

Copy `custom_components/monster_remote` into Home Assistant's
`config/custom_components` directory and restart Home Assistant.

## Example: rest light

```yaml
automation:
  - alias: Monster Remote rest light
    triggers:
      - trigger: state
        entity_id: binary_sensor.gym_monster_rest_active
        to: "on"
    actions:
      - action: light.turn_on
        target:
          entity_id: light.gym
        data:
          rgb_color: [255, 155, 30]
```

## Example: announce the next exercise

```yaml
automation:
  - alias: Announce Monster Remote exercise
    triggers:
      - trigger: state
        entity_id: sensor.gym_monster_exercise
    conditions:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable'] }}"
    actions:
      - action: tts.speak
        target:
          entity_id: tts.home_assistant_cloud
        data:
          media_player_entity_id: media_player.gym
          message: "Next exercise: {{ trigger.to_state.state }}"
```

## Session timers

`sensor.session_started` and `sensor.rest_started` are timestamp sensors. Home
Assistant can calculate elapsed time locally from them, so Monster Helper does
not need to send a network update every second.

## GM mirror camera

`camera.gym_monster_mirror` exposes Helper's authenticated local H.264 stream
from `/mirror/stream`. It stays on the LAN and can be placed on a dashboard or
used by Home Assistant's stream/ffmpeg path. Starting/stopping the mirror still
uses the normal Monster Remote controls; the camera does not grant cloud access.

## Semantic activity events

Listen for `monster_remote_activity` and filter its `event_type`. Current event
types are:

- `session_started` / `session_finished`
- `exercise_changed`
- `rep_completed` / `set_completed`
- `rest_started` / `rest_finished`
- `workout_paused` / `workout_resumed`

Example:

```yaml
automation:
  - alias: Monster Remote set completed
    triggers:
      - trigger: event
        event_type: monster_remote_activity
        event_data:
          event_type: set_completed
    actions:
      - action: light.turn_on
        target:
          entity_id: light.gym
        data:
          brightness_pct: 35
```

## Safety

Home Assistant automations are convenience features. Network connectivity,
automations and third-party devices must never be treated as the primary safety
control for resistance or motor operation.
