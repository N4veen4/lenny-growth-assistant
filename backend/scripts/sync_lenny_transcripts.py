"""
Script to synchronize and parse real podcast transcripts from the official
Lenny's Newsletter & Podcast GitHub archive into structured RAG ingestion format.

Source repository: https://github.com/LennysNewsletter/lennys-newsletterpodcastdata
"""

import os
import re
import json
import glob
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_transcripts")

def parse_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter keys from markdown file."""
    metadata = {}
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return metadata
    
    fm_text = fm_match.group(1)
    for line in fm_text.splitlines():
        line = line.strip()
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            metadata[key] = val
    return metadata

def parse_transcript_markdown(filepath: str, max_sections_per_podcast: int = 8) -> List[Dict[str, Any]]:
    """
    Parses a single podcast transcript markdown file into structured sections
    with speaker names, timestamps, genuine episode URLs, and content.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    meta = parse_frontmatter(text)
    title = meta.get("title", os.path.splitext(os.path.basename(filepath))[0].replace("-", " ").title())
    guest = meta.get("guest", "Lenny Rachitsky")
    post_url = meta.get("post_url", f"https://www.lennyspodcast.com/{os.path.splitext(os.path.basename(filepath))[0]}")
    if not post_url.startswith("http"):
        post_url = f"https://www.lennyspodcast.com/{post_url.lstrip('/')}"

    # Remove frontmatter
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)

    # Match dialogue turns: **Speaker** (timestamp):\nContent...
    turn_pattern = re.compile(r"\*\*([^*]+)\*\*\s*\(([^)]+)\):\s*\n", re.MULTILINE)
    matches = list(turn_pattern.finditer(body))
    
    records = []
    base_id = os.path.splitext(os.path.basename(filepath))[0]

    if matches:
        chunks = []
        for i, match in enumerate(matches):
            speaker = match.group(1).strip()
            timestamp = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            speech = body[start_pos:end_pos].strip()
            
            # Clean dialogue text
            speech = re.sub(r"\s+", " ", speech)
            if len(speech) > 60:  # Only meaningful statements
                chunks.append({
                    "speaker": speaker,
                    "timestamp": timestamp,
                    "speech": speech
                })
        
        # Group adjacent turns into cohesive conversational context blocks (~600-1400 chars)
        grouped = []
        cur_speaker = guest
        cur_time = "00:00:00"
        cur_text = []
        cur_len = 0

        for chunk in chunks:
            # Prefer guest speaker if present in block
            if guest.lower() in chunk["speaker"].lower():
                cur_speaker = chunk["speaker"]
                cur_time = chunk["timestamp"]

            dialogue_line = f"{chunk['speaker']} ({chunk['timestamp']}): {chunk['speech']}"
            cur_text.append(dialogue_line)
            cur_len += len(dialogue_line)

            if cur_len >= 900:
                block_content = "\n\n".join(cur_text)
                grouped.append({
                    "speaker": cur_speaker,
                    "timestamp": cur_time,
                    "content": block_content
                })
                cur_text = []
                cur_len = 0
                cur_speaker = guest

        if cur_text:
            grouped.append({
                "speaker": cur_speaker,
                "timestamp": cur_time,
                "content": "\n\n".join(cur_text)
            })

        # Select evenly distributed sections throughout the episode to cover the full discussion
        if len(grouped) > max_sections_per_podcast:
            step = len(grouped) // max_sections_per_podcast
            selected = [grouped[i * step] for i in range(max_sections_per_podcast)]
        else:
            selected = grouped

        for idx, item in enumerate(selected):
            records.append({
                "id": f"{base_id}_sec_{idx + 1}",
                "episode_title": title,
                "url": post_url,
                "speaker": item["speaker"],
                "timestamp": item["timestamp"],
                "content": item["content"]
            })
    else:
        # Fallback for plain text paragraphs if no bold speaker pattern
        paras = [p.strip() for p in body.split("\n\n") if len(p.strip()) > 100]
        for idx, para in enumerate(paras[:max_sections_per_podcast]):
            records.append({
                "id": f"{base_id}_para_{idx + 1}",
                "episode_title": title,
                "url": post_url,
                "speaker": guest,
                "timestamp": "00:00:00",
                "content": para
            })

    return records

def sync_all_podcasts(raw_repo_dir: str, output_file: str, max_sections_per_podcast: int = 6):
    podcasts_dir = os.path.join(raw_repo_dir, "podcasts")
    if not os.path.exists(podcasts_dir):
        raise FileNotFoundError(f"Directory not found: {podcasts_dir}")

    md_files = sorted(glob.glob(os.path.join(podcasts_dir, "*.md")))
    logger.info("Found %d podcast transcript markdown files in '%s'", len(md_files), podcasts_dir)

    all_records = []
    for filepath in md_files:
        try:
            records = parse_transcript_markdown(filepath, max_sections_per_podcast=max_sections_per_podcast)
            all_records.extend(records)
        except Exception as e:
            logger.warning("Error parsing %s: %s", filepath, e)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    logger.info("Successfully generated %d structured transcript sections across %d episodes to '%s'",
                len(all_records), len(md_files), output_file)
    return len(all_records)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_repo = os.path.join(base_dir, "data", "raw_transcripts_repo")
    dest_json = os.path.join(base_dir, "data", "transcripts", "lenny_podcasts_archive.json")
    sync_all_podcasts(raw_repo, dest_json, max_sections_per_podcast=6)
