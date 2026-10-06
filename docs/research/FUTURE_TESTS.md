# Future tests — generated library assets

Status: **Parked; not started.** Recorded 2026-10-06. These optional investigations follow the current CPU/save qualification work. They do not change the active B008 gate or the feasibility score.

Use synthetic MP3s, covers, library fixtures, and playlists on designated disposable media. Qualify file creation, permitted paths, bounds, and interrupted publication before modifying generated library assets. Existing music and original covers remain protected inputs; any library replacement is a separately authorized experiment.

## F01 — directory discovery

**Goal:** Determine whether a core can discover MP3 files in a directory using a supported interface.

**Method:** First research directory enumeration available to the core and distinguish runtime from boot-time mechanisms. If no suitable interface exists, compare a host-generated manifest. Later test empty/nested directories, filename encoding/length, large collections, missing files, and discovery interrupted by restart.

**Corrections:** None; investigation has not started.

**Result details:** Pending. File-slot read/write support alone does not establish directory discovery. Record the supported mechanism and limits before implementing a scanner.

## F02 — library generation and replacement

**Goal:** Build or update a Tau-compatible library index from discovered files while preserving a usable previous index.

**Method:** Pin the library schema and identity rules; generate a separate candidate from synthetic inputs; independently validate all records and paths. Explore replacement/recovery using available supported operations, including partial updates, cancellation, full media, and interruptions.

**Corrections:** None; investigation has not started.

**Result details:** Pending. Compatibility, publication strategy, and recovery across related files require their own evidence. Initial save-file results do not qualify library editing.

## F03 — optimized cover images

**Goal:** Generate smaller derived cover images suitable for Tau's actual display/cache formats.

**Method:** Establish source-image and output-format requirements, then decode/resize/encode one synthetic cover in isolation. Compare output with an independent decoder; measure CPU time, memory, quality, output size, and later playback impact. Include oversized/malformed images and interrupted output creation.

**Corrections:** None; investigation has not started.

**Result details:** Pending. Original covers are preserved; generated images use separate output files. File writing does not establish image-processing feasibility or performance.

## F04 — playlist creation

**Goal:** Create playlist files that Tau loads correctly and that refer to the intended tracks.

**Method:** Start with one small playlist and a pinned supported format; create it in an allowed namespace, independently inspect its bytes, and reload in Tau. Extend to empty/large lists, relative paths, non-ASCII names, missing/duplicate tracks, name collisions, and interrupted creation/update.

**Corrections:** None; investigation has not started.

**Result details:** Pending. File creation, parser compatibility, path rules, and partial-file rejection are unqualified for this feature.

## Suggested future sequence

After prerequisites are qualified, start with a small playlist, then library candidate generation, then one derived cover. Establish directory-discovery feasibility before promising an automatic whole-directory workflow. All four features remain optional and parked until selected for development.
