# TeamSnap Data Schemas (Reverse Engineered)

This document serves as the source of truth for "Known Available Data" from TeamSnap.
**DO NOT HALLUCINATE FIELDS NOT LISTED HERE.**

## Team Object

*Source: Raw JSON capture (Dec 2025)*

| Field Name | Type | Example | Description |
|------------|------|---------|-------------|
| `id` | int | `7024664` | Unique Team ID |
| `name` | str | `"Mavericks"` | Team Name (may/may not have year) |
| `sport_id` | int | `2` | **2 = Soccer** |
| `league_name` | str | `"Cherry Hill Soccer Club"` | |
| `division_name` | str | `"CHSC Boys Travel "` | |
| `season_name` | str | `""` | Often empty string |
| `time_zone` | str | `"Eastern Time (US & Canada)"` | Human readable TZ |
| `time_zone_iana_name`| str | `"America/New_York"` | Code TZ |
| `plan_id` | int | `56` | |
| `created_at` | iso-date| `"2020-08-06T20:56:08Z"` | |
| `updated_at` | iso-date| `"2023-09-26T13:18:30Z"` | |
| `is_retired` | bool | `false` | |
| `is_in_league` | bool | `true` | |
| `location_postal_code`| str | `"08034"` | |
| `location_country` | str | `"United States"` | |
| `member_limit` | int | `4000` | |
| `roster_limit` | int | `4000` | |
| `player_member_count` | int | `16` | |
| `type` | str | `"team"` | |

**Confirmed Missing/Hallucinated Fields:**

* ❌ `year_name` (Does not exist. Use regex on `name` or look at `division_name`)

---

## Game/Event Object

*Source: Verified working code (Dec 2025)*

| Field Name | Type | Notes |
|------------|------|-------|
| `id` | int | Event ID |
| `start_date` | iso-date | |
| `opponent_name` | str | |
| `location_name` | str | |
| `is_game_host` | bool | Determines Home/Away (True=Home) |
| `points_for` | ? | (Likely exists, unseen) |
| `points_against` | ? | (Likely exists, unseen) |

---

## Member Object

*Source: Raw JSON capture (User Provided, Dec 2025)*

| Field Name | Type | Example | Notes |
|------------|------|---------|-------|
| `id` | int | `88384366` | Member ID |
| `type` | str | `"member"` | |
| `user_id` | int | `16566344` | TeamSnap User ID (links to login) |
| `team_id` | int | `7024664` | |
| `first_name` | str | `"Austin"` | |
| `last_name` | str | `"Morse"` | |
| `email_addresses` | list[str] | `["e...e@yahoo.com"]` | **Valid List of Strings** (Not list of dicts in this case!) |
| `jersey_number` | str | `"19"` | String, requires parsing |
| `is_coach` | bool | `false` | |
| `is_owner` | bool | `false` | |
| `is_manager` | bool | `false` | |
| `is_activated` | bool | `true` | |
| `created_at` | iso-date| `"2020-08-06..."` | |
| `updated_at` | iso-date| `"2025-10-07..."` | |
| `birthday` | str | `""` | Often empty string |
| `address_zip` | null | | |
| `phone_numbers` | list | `[]` | |
