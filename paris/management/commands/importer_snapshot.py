"""Importe un snapshot JSON (Zanalyze Engine ou export local)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from paris.snapshot import importer_snapshot

DEFAULT_ENGINE_URL = (
    'https://raw.githubusercontent.com/Stevy64/Zanalyze-Engine/main/exports/matchs.json'
)


class Command(BaseCommand):
    help = (
        'Importe un snapshot v1 (matchs + analyses). '
        'Source : fichier local, --url, ou ZANALYZ_SNAPSHOT_URL '
        '(Zanalyze Engine / GitHub Actions).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default='exports/matchs.json',
            help='Fichier JSON snapshot local',
        )
        parser.add_argument(
            '--url',
            default='',
            help='URL HTTPS du snapshot (ex. raw.githubusercontent.com)',
        )
        parser.add_argument(
            '--recalculer',
            action='store_true',
            help='Après import, relance calculer_analyses (moteur local).',
        )

    def handle(self, *args, **opts):
        url = (opts.get('url') or os.environ.get('ZANALYZ_SNAPSHOT_URL') or '').strip()
        if url:
            data = self._depuis_url(url)
        else:
            data = self._depuis_fichier(opts['source'])

        stats = importer_snapshot(data)
        self.stdout.write(self.style.SUCCESS(
            'Import snapshot OK : '
            + ', '.join(f'{k}={v}' for k, v in stats.items())
        ))

        if opts['recalculer']:
            from django.core.management import call_command
            self.stdout.write('Recalcul des analyses (moteur local)…')
            call_command('calculer_analyses')

    def _depuis_fichier(self, source: str) -> dict:
        chemin = Path(source)
        if not chemin.is_absolute():
            chemin = Path(settings.BASE_DIR) / chemin
        if not chemin.exists():
            raise CommandError(
                f'Fichier introuvable : {chemin}\n'
                'Passe --url vers le snapshot Zanalyze Engine, ou copie exports/matchs.json.'
            )
        try:
            return json.loads(chemin.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise CommandError(f'JSON illisible : {exc}') from exc

    def _depuis_url(self, url: str) -> dict:
        self.stdout.write(f'Téléchargement {url} …')
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Zanalyze-importer/1.0', 'Accept': 'application/json'},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode('utf-8')
        except urllib.error.URLError as exc:
            raise CommandError(
                f'Impossible de télécharger le snapshot ({exc}). '
                f'Essaie l’URL par défaut : {DEFAULT_ENGINE_URL}'
            ) from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CommandError(f'JSON illisible depuis l’URL : {exc}') from exc
