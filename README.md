# Monster Remote for Home Assistant

Local, real-time Home Assistant control and workout telemetry for Speediance
Gym Monster devices running Monster Remote.

The integration talks only to Monster Helper on your local network. It never
needs Speediance cloud credentials and knows nothing about Dart offsets or
`watch_requests` profiles.

## Highlights

- Local push updates over Server-Sent Events
- Automatic reconnect with a low-frequency snapshot fallback
- Current exercise, set, weight, resistance, heart rate and rowing telemetry
- Native controls for weight, resistance, modes, rest and workout navigation
- A `monster_remote_event` event for advanced automations

The data path is deliberately split:

```text
watch_requests → Monster Helper → Home Assistant integration
```

`watch_requests` remains focused on safe, version-profiled access to the
Speediance app. Monster Helper owns the stable local API. Home Assistant owns
automations, dashboards, announcements and scenes.

## Requirements

- Monster Remote Premium
- Monster Helper **2.01.46 or newer**
- Home Assistant and the Gym Monster on the same local network

## Installation

### HACS

1. Open HACS → Integrations → Custom repositories.
2. Add `https://github.com/LilaQ/monster-remote-home-assistant` as an Integration.
3. Install **Monster Remote** and restart Home Assistant.
4. Go to Settings → Devices & services → Add integration → Monster Remote.
5. Enter the Gym Monster IP address. Port `8765` and the pre-filled Helper
   secret normally do not need to be changed.

### Manual

Copy `custom_components/monster_remote` into Home Assistant's
`config/custom_components` directory and restart Home Assistant.

## Example: rest light

```yaml
automation:
  - alias: Gym Monster rest light
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
  - alias: Announce Gym Monster exercise
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

## Safety

Home Assistant automations are convenience features. Network connectivity,
automations and third-party devices must never be treated as the primary safety
control for resistance or motor operation.
