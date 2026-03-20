from __future__ import annotations


def split_new_ids(discovered_ids: list[str], known_ids: list[str]) -> list[str]:
    known = set(known_ids)
    return [job_id for job_id in discovered_ids if job_id not in known]
