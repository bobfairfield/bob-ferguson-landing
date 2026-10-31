# Sharing Library tools

Builds a leader's Sharing Library: personalized videos, the library page and the short link.
This folder starts with an underscore, so the site does not publish it.

- `participants.json` : every leader the library knows about (source for pages and videos)
- `series.json`, `build_library.py` : the page builder (`python _library-tools/build_library.py .`)
- `render/`, `assets/` : the video renderer and the shared video parts
- `scripts/add_leader.py`, `scripts/build_leader.py` : add one leader, render their videos
- `inbox/<slug>/` : optional tool files for a leader (checklist, tracker, two cards)

Run by `.github/workflows/leader-library.yml`. Videos for a leader are stored in that leader's own
`*-landing` repo under `library-videos/<series>/`, so this site stays under GitHub's size limit.
Needs the repository secret `LEADER_REPOS_TOKEN` (write access to the leaders' repos).
