# MISSION: The Kanto Championship Campaign

> [!IMPORTANT]
> **MCP Interface**: This server runs on a streamlined, deterministic 5-tool visual interface.
> Direct Game Boy hardware simulation, 4× crisp nearest-neighbor visuals (`screen.png`), and zero-latency tilemap ASCII text extraction (`screen_text`) replace fragile macro scripts and collision maps.

---

## Tactical Interface (The 5 Core Tools)

| Tool | Purpose | Arguments | Key Returns |
| :--- | :--- | :--- | :--- |
| **`get_state()`** | Primary sensory tool. Clean 4× upscaled screenshot (`640x576`) + ground-truth tilemap text + telemetry. | None | `image_path`, `screen_text`, `map_id`, `map_name`, `position` `[x, y]`, `in_battle`, `dialogue_active`, `menu_active` |
| **`step(direction, count)`** | Verified cardinal movement across the overworld. Halts on obstacles, battles, warps, or dialogue. | `direction` (`"up"`, `"down"`, `"left"`, `"right"`), `count` (1–10, default 1) | `steps_completed`, `final_position`, `final_map`, `interrupted_by` (`"hit_obstacle"`, `"battle_started"`, `"map_transition"`, `"dialogue_started"`, or `null`) |
| **`press(buttons, delay_frames)`** | Precise button execution for menus, naming, combat, and interacting with objects/NPCs directly in front of you. | `buttons` (e.g. `["a"]`, `["down", "a"]`, `["start"]`), `delay_frames` (default 15) | `presses`, updated `screen_text`, `in_battle`, `dialogue_active`, `menu_active` |
| **`advance_dialogue(max_pages)`** | Fast-forwards through multi-page speech and cutscenes. Captures every page into an ASCII transcript. Halts on prompts or closure. | `max_pages` (1–10, default 5) | `pages` (list of transcript pages), `status` (`"dialogue_closed"` or `"prompt_detected"`) |
| **`save_game(name)` / `load_game(name)`** | Reliable emulator state checkpointing and recovery. | `name` (e.g. `"before_brock"`, `"route_1"`) | Confirmation string |

---

## Standard Operating Procedure

1. **Observe Before Acting**:
   - Call `get_state()` to inspect visual terrain, menus, dialogue boxes, and ground-truth `screen_text`.
   - The Game Boy handles world collision. If an obstacle, ledge, or wall blocks you, `step` halts immediately with `"hit_obstacle"`.
2. **Interactions**:
   - To talk to NPCs, heal at Pokémon Centers, shop at Poké Marts, or inspect objects (signs, PCs, items, Gym statues), step directly adjacent facing the target and call `press(["a"])`.
3. **Dialogue & Cutscenes**:
   - Whenever `dialogue_active` is `true`, call `advance_dialogue(max_pages=5)`.
   - If `status` is `"prompt_detected"` (e.g. YES/NO prompts, item choices, nicknames), check `screen_text` with `get_state()` and decide your action with `press(buttons)`.
4. **Combat & Party Management**:
   - Combat is executed directly via `press`:
     - Attack: `press(["a", "a"])` selects `FIGHT` and uses Move 1.
     - Move Selection: `press(["a", "<dir>", "a"])` chooses alternative moves.
     - Items / Potions: Open `ITEM` to restore HP during tough battles.
     - Running: `press(["right", "down", "a"])` flees wild encounters when conserving HP.
   - Heal regularly at Pokémon Centers (`press(["a"])` at the front desk nurse) to avoid blacking out.
5. **Checkpoints**:
   - Save frequently at key milestones and before every Gym Leader with `save_game("name")`.

---

## Campaign Objective

**Ultimate Goal**: Conquer all 8 Kanto Gyms, traverse Victory Road, defeat the Elite Four and the Champion (Rival), and enter the Hall of Fame. Do not stop at Viridian City.

---

## Campaign Roadmap & Key Milestones

### Milestone 0: New Game & Pallet Town Departure
- **Intro & Naming**: Advance Oak's intro, select names (`BLUE` / `RED`), clear speech into bedroom (`Player's House 2F`, Map 38, Pos `[3, 6]`).
- **House Exit**: Move right to `[5, 6]`, up to `[5, 1]`, right onto stairs to 1F. Down hallway to `[7, 7]`, left to `[3, 7]`, down door into Pallet Town (Map 0).
- **Oak's Lab**: Walk north to grass to trigger Oak. Choose your starter Pokémon (Charmander, Squirtle, or Bulbasaur). Defeat Rival in the lab battle.
- **Route 1**: Travel north through Route 1 to Viridian City.

### Milestone 1: Oak's Parcel & The Pokédex
- **Viridian Poké Mart**: Talk to the clerk to receive **Oak's Parcel**.
- **Return to Pallet Town**: Deliver the parcel to Professor Oak in his lab to receive the **Pokédex** and Poké Balls.
- **Rival's House**: Speak with Daisy (Rival's sister) to receive the **Town Map**.

### Milestone 2: The Boulder Badge (Pewter City)
- **Viridian Forest**: Head north from Viridian City through the gatehouse into Viridian Forest. Navigate bug catchers and reach Pewter City.
- **Pewter Gym**: Defeat Gym Leader **Brock** (Rock-type) for the **Boulder Badge** and TM34 (Bide).

### Milestone 3: The Cascade Badge (Cerulean City)
- **Route 3 & Mt. Moon**: Head east from Pewter City across Route 3, buy Magikarp if desired, traverse Mt. Moon, defeat Team Rocket grunts, and claim a fossil.
- **Cerulean City & Nugget Bridge**: Defeat Rival on Route 24, conquer the 5 trainers of Nugget Bridge, and visit Bill at his Sea Cottage on Route 25 to receive the **S.S. Ticket**.
- **Cerulean Gym**: Defeat Gym Leader **Misty** (Water-type) for the **Cascade Badge** and TM11 (BubbleBeam).

### Milestone 4: The Thunder Badge (Vermilion City)
- **Route 5 & Underground Path**: Head south from Cerulean City to Vermilion City.
- **S.S. Anne**: Board the luxury cruise ship, battle Rival, and speak with the seasick Captain to receive **HM01 (Cut)**. Teach Cut to a compatible team member.
- **Vermilion Gym**: Cut the slender tree, solve the trash can puzzle, and defeat Gym Leader **Lt. Surge** (Electric-type) for the **Thunder Badge**.

### Milestone 5: The Rainbow & Soul Badges (Celadon & Fuchsia)
- **Rock Tunnel**: Travel east through Route 9 and darkness of Rock Tunnel (or use Flash) to Lavender Town.
- **Celadon City**: Head west to Celadon City. Obtain the Coin Case, explore the Department Store, infiltrate Team Rocket's Game Corner Hideout to defeat Giovanni and obtain the **Silph Scope**.
- **Celadon Gym**: Defeat Gym Leader **Erika** (Grass-type) for the **Rainbow Badge**.
- **Pokémon Tower**: Return to Lavender Town, ascend Pokémon Tower using the Silph Scope, rescue Mr. Fuji, and receive the **Poké Flute**.
- **Cycling Road & Fuchsia City**: Wake Snorlax with the Poké Flute on Route 16 or 12. Head down Cycling Road (Route 17) to Fuchsia City.
- **Safari Zone**: Retrieve the Gold Teeth and receive **HM03 (Surf)** and **HM04 (Strength)**. Deliver Gold Teeth to the Warden.
- **Fuchsia Gym**: Defeat Gym Leader **Koga** (Poison-type) for the **Soul Badge**.

### Milestone 6: The Marsh & Volcano Badges (Saffron & Cinnabar)
- **Silph Co. & Saffron City**: Give Tea/Drink to the Saffron guards. Liberate the 11-floor Silph Co. headquarters from Team Rocket, receive the Master Ball from the President, and defeat Rival and Giovanni.
- **Saffron Gym**: Navigate the teleport pads and defeat Gym Leader **Sabrina** (Psychic-type) for the **Marsh Badge**.
- **Sea Routes 19–20 & Cinnabar Island**: Surf south from Fuchsia or Pallet Town to Cinnabar Island.
- **Pokémon Mansion**: Explore the burnt mansion to locate the Secret Key.
- **Cinnabar Gym**: Unlock the gym, answer quiz machines or battle trainers, and defeat Gym Leader **Blaine** (Fire-type) for the **Volcano Badge**.

### Milestone 7: The Earth Badge (Viridian Gym)
- **Return to Viridian**: The locked Viridian Gym is now open.
- **Viridian Gym**: Navigate spinner tiles and defeat Gym Leader **Giovanni** (Ground-type) for the 8th and final **Earth Badge**.

### Milestone 8: Route 22, Victory Road & The Pokémon League
- **Route 22 & 23 Badge Check**: Head west from Viridian City, defeat Rival on Route 22, and pass through the 8 Badge Check gates on Route 23.
- **Victory Road**: Traverse the cavern using Strength on boulders to depress switches and open barriers. Exit to the **Indigo Plateau**.
- **Final Preparation**: Heal your team, stock up on Full Restores and Revives at the Indigo Plateau Mart, and save your game (`save_game("indigo_plateau_entry")`).
- **The Elite Four & Champion**:
  1. **Lorelei** (Ice / Water)
  2. **Bruno** (Fighting / Rock)
  3. **Agatha** (Ghost / Poison)
  4. **Lance** (Dragon)
  5. **Champion (Rival)**: Defeat your Rival in the ultimate battle.
- **Hall of Fame**: Follow Professor Oak into the Hall of Fame chamber to register your team and complete the game!
