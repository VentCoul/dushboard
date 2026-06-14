# Dushboard — персональний дашборд

Flask + HTMX + Tailwind. Вкладки: Продуктивність (Obsidian + звички), Віджети
(погода/крипта/GitHub/календар/пошта), Моніторинг VPS, AI (заглушка).

## Запуск локально

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # заповни DASHBOARD_PASSWORD і SECRET_KEY
.venv/bin/python app.py     # http://localhost:5000  (на macOS порт 5000 зайнятий AirPlay — див. нижче)
```

> **macOS:** порт 5000 займає AirPlay Receiver. Або вимкни його в System Settings → General
> → AirDrop & Handoff, або запускай на іншому порту:
> `.venv/bin/python -c "from app import app; app.run(port=5050, debug=True)"`

Логін — пароль із `DASHBOARD_PASSWORD`.

## Етап 0 — підключити Obsidian (потрібно для вкладки задач)

1. В Obsidian встанови плагін **Obsidian Git**, увімкни авто-commit + auto-push,
   вкажи приватний репозиторій (GitHub/Gitea).
2. На машині з дашбордом: `git clone <repo> data/vault`
3. У `.env`: `VAULT_PATH=data/vault`, `VAULT_PROJECTS_DIR=Projects`, `VAULT_GIT_ENABLED=1`.

Задачі — це звичайні markdown-чекбокси `- [ ]` у файлах папки `Projects/`. Дашборд їх
читає, toggle і додавання пишуться у `.md` та комітяться назад.

## Деплой на VPS (Hetzner)

```bash
# на сервері, у /root/dushboard
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # заповни
cp deploy/dushboard.service /etc/systemd/system/
systemctl enable --now dushboard
cp deploy/nginx.conf /etc/nginx/sites-available/dushboard
ln -s /etc/nginx/sites-available/dushboard /etc/nginx/sites-enabled/
certbot --nginx -d <твій-домен>
```
