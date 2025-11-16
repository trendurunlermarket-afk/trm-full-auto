import os, sys, shutil, re
from pathlib import Path
from dotenv import load_dotenv
import yaml
from utils.logger import log

def read_config() -> dict:
    cfg_path = Path('config/sync_config.yaml')
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}
    load_dotenv(override=False)
    tg = cfg.setdefault('telegram', {})
    tg.setdefault('api_id', os.getenv('TELEGRAM_API_ID', ''))
    tg.setdefault('api_hash', os.getenv('TELEGRAM_API_HASH', ''))
    tg.setdefault('bot_token', os.getenv('TELEGRAM_BOT_TOKEN', ''))
    tg.setdefault('channel', os.getenv('TELEGRAM_CHANNEL', ''))
    drv = cfg.setdefault('drive', {})
    drv.setdefault('parent_folder_id', os.getenv('DRIVE_PARENT_FOLDER_ID', ''))
    return cfg

def ensure_dirs(cfg: dict):
    p = cfg.get('paths', {})
    for key in ['source_root','telegram_downloads','mirror_root','drive_upload_root']:
        Path(p.get(key,"")).mkdir(parents=True, exist_ok=True)

def expand_placeholders(expr: str, paths: dict) -> str:
    if not isinstance(expr, str):
        return expr
    out = expr
    out = re.sub(r"\{paths\.([a-zA-Z0-9_]+)\}", lambda m: str(paths.get(m.group(1), "")), out)
    out = re.sub(r"\{paths\[([a-zA-Z0-9_]+)\]\}", lambda m: str(paths.get(m.group(1), "")), out)
    out = re.sub(r"\{([a-zA-Z0-9_]+)\}", lambda m: str(paths.get(m.group(1), m.group(0))), out)
    return out

def copy_with_rules(src, dst, exts, exclude=None):
    src_p = Path(src); dst_p = Path(dst)
    if not src_p.exists():
        return 0
    dst_p.mkdir(parents=True, exist_ok=True)
    copied = 0
    exts = [e.lower().lstrip('.') for e in (exts or [])]
    for root, _, files in os.walk(src_p):
        for name in files:
            if exclude and any(x in name for x in (exclude or [])):
                continue
            if exts and name.split('.')[-1].lower() not in exts:
                continue
            src_file = Path(root)/name
            rel = src_file.relative_to(src_p)
            target = dst_p/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_file, target)
                copied += 1
            except Exception as e:
                log('WARN', f'Copy fail: {src_file} -> {target}: {e}')
    return copied

def main():
    log('INFO', 'DERYA_SYNC_RUNNER starting...')
    cfg = read_config()
    ensure_dirs(cfg)
    dry = bool(cfg.get('dry_run', False))
    paths = cfg.get('paths', {})

    if cfg.get('enable_telegram', False):
        tg = cfg.get('telegram', {})
        if all([tg.get('api_id'), tg.get('api_hash'), tg.get('bot_token'), tg.get('channel')]):
            log('INFO', f"[Telegram] connect: channel={tg.get('channel')} limit={tg.get('limit',20)} (stub)")
        else:
            log('ERROR', '[Telegram] api_id/api_hash/bot_token/channel eksik. (.env veya config doldur)')

    total = 0
    for rule in cfg.get('rules', []):
        src = expand_placeholders(rule.get('from',''), paths)
        dst = expand_placeholders(rule.get('to',''), paths)
        exts = rule.get('include_ext', [])
        excl = rule.get('exclude_patterns', [])
        if dry:
            log('INFO', f"[DRY] {src} -> {dst}")
        else:
            n = copy_with_rules(src, dst, exts, exclude=excl)
            total += n
            log('INFO', f"Copied {n} files from {src} -> {dst} (dry_run={dry})")

    log('INFO', f"Finished. Total copied: {total}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
