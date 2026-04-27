from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


@dataclass(slots=True)
class PolicyProfile:
    name: str
    path: Path | None
    provider_rules: dict[str, dict[str, object]]
    merge_rules: dict[str, object]
    replay_defaults: dict[str, object]
    raw: dict[str, object]

    def provider_enabled(self, provider: str, default: bool = True) -> bool:
        rule = self.provider_rules.get(provider) or {}
        value = rule.get('enabled', default)
        return bool(value)

    def provider_value(self, provider: str, key: str, default: object = None) -> object:
        rule = self.provider_rules.get(provider) or {}
        return rule.get(key, default)

    def merge_value(self, key: str, default: object = None) -> object:
        return self.merge_rules.get(key, default)


@dataclass(slots=True)
class Settings:
    imap_host: str | None
    imap_port: int
    imap_username: str | None
    imap_password: str | None
    imap_mailbox: str
    sqlite_path: Path
    log_level: str
    workspace_root: Path
    config_source: str
    imap_account: str | None
    crossref_mailto: str | None
    openalex_email: str | None
    semantic_scholar_api_key: str | None
    unpaywall_email: str | None
    policy_profile: PolicyProfile


def _skill_env_path() -> Path:
    return Path.home() / ".config" / "imap-smtp-email" / ".env"


def _load_external_imap_skill_env(account: str | None = None) -> dict[str, str]:
    path = _skill_env_path()
    if not path.exists():
        return {}
    raw = dotenv_values(path)
    prefix = f"{account.upper()}_" if account else ""
    result: dict[str, str] = {}
    if raw.get(f"{prefix}IMAP_HOST"):
        result["IMAP_HOST"] = str(raw[f"{prefix}IMAP_HOST"])
    if raw.get(f"{prefix}IMAP_PORT"):
        result["IMAP_PORT"] = str(raw[f"{prefix}IMAP_PORT"])
    if raw.get(f"{prefix}IMAP_USER"):
        result["IMAP_USERNAME"] = str(raw[f"{prefix}IMAP_USER"])
    if raw.get(f"{prefix}IMAP_PASS"):
        result["IMAP_PASSWORD"] = str(raw[f"{prefix}IMAP_PASS"])
    if raw.get(f"{prefix}IMAP_MAILBOX"):
        result["IMAP_MAILBOX"] = str(raw[f"{prefix}IMAP_MAILBOX"])
    return result


def _default_policy_profile() -> PolicyProfile:
    raw = {
        'profile_name': 'builtin_default',
        'provider_rules': {
            'crossref': {'enabled': True, 'title_payload_reuse_enabled': True},
            'openalex': {'enabled': True, 'doi_batch_enabled': True, 'title_payload_reuse_enabled': True},
            'semanticscholar': {'enabled': True, 'title_payload_reuse_enabled': True},
            'pubmed': {'enabled': True, 'fallback_only_for_core_fields': True},
            'europepmc': {'enabled': True, 'trigger_mode': 'narrowed_biomedical_fallback'},
            'arxiv': {'enabled': True, 'trigger_mode': 'arxiv_native_only'},
        },
        'merge_rules': {
            'pubmed_title_doi_suppression': True,
            'normalized_only_fallback': False,
        },
        'replay_defaults': {
            'stages': ['enrich', 'merge', 'dedup'],
        },
    }
    return PolicyProfile(
        name=str(raw['profile_name']),
        path=None,
        provider_rules=dict(raw['provider_rules']),
        merge_rules=dict(raw['merge_rules']),
        replay_defaults=dict(raw['replay_defaults']),
        raw=raw,
    )


def _load_policy_profile(path_value: str | None) -> PolicyProfile:
    default_profile = _default_policy_profile()
    if not path_value:
        return default_profile

    path = Path(path_value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f'policy profile not found: {path}')

    try:
        import yaml
    except Exception as exc:  # pragma: no cover, depends on runtime packaging
        raise RuntimeError('PyYAML is required when MGAP_POLICY_PROFILE is set') from exc

    raw = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    provider_rules = dict(default_profile.provider_rules)
    for provider, rule in (raw.get('provider_rules') or {}).items():
        merged_rule = dict(provider_rules.get(provider) or {})
        merged_rule.update(rule or {})
        provider_rules[str(provider)] = merged_rule

    merge_rules = dict(default_profile.merge_rules)
    merge_rules.update((raw.get('merge_rules') or {}))

    replay_defaults = dict(default_profile.replay_defaults)
    replay_defaults.update((raw.get('replay_defaults') or {}))

    return PolicyProfile(
        name=str(raw.get('profile_name') or path.stem),
        path=path,
        provider_rules=provider_rules,
        merge_rules=merge_rules,
        replay_defaults=replay_defaults,
        raw=raw,
    )


def load_settings() -> Settings:
    load_dotenv()
    workspace_root = Path(__file__).resolve().parents[2]
    requested_account = os.getenv("IMAP_ACCOUNT")
    external_imap_env = _load_external_imap_skill_env(requested_account)

    imap_host = os.getenv("IMAP_HOST") or external_imap_env.get("IMAP_HOST")
    imap_port = int(os.getenv("IMAP_PORT") or external_imap_env.get("IMAP_PORT") or "993")
    imap_username = os.getenv("IMAP_USERNAME") or external_imap_env.get("IMAP_USERNAME")
    imap_password = os.getenv("IMAP_PASSWORD") or external_imap_env.get("IMAP_PASSWORD")
    imap_mailbox = os.getenv("IMAP_MAILBOX") or external_imap_env.get("IMAP_MAILBOX") or "INBOX"
    policy_profile = _load_policy_profile(os.getenv('MGAP_POLICY_PROFILE'))

    if os.getenv("IMAP_HOST") or os.getenv("IMAP_USERNAME") or os.getenv("IMAP_PASSWORD"):
        config_source = "project_env"
    elif external_imap_env:
        config_source = "imap_skill_env"
    else:
        config_source = "defaults_only"

    sqlite_path = Path(os.getenv("SQLITE_PATH", workspace_root / "data" / "mgap.db"))
    return Settings(
        imap_host=imap_host,
        imap_port=imap_port,
        imap_username=imap_username,
        imap_password=imap_password,
        imap_mailbox=imap_mailbox,
        sqlite_path=sqlite_path,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        workspace_root=workspace_root,
        config_source=config_source,
        imap_account=requested_account,
        crossref_mailto=os.getenv('CROSSREF_MAILTO'),
        openalex_email=os.getenv('OPENALEX_EMAIL'),
        semantic_scholar_api_key=os.getenv('SEMANTIC_SCHOLAR_API_KEY'),
        unpaywall_email=os.getenv('UNPAYWALL_EMAIL'),
        policy_profile=policy_profile,
    )
