# Production SQLite Safeguards & Recovery Protocol

## 1. Problem Statement
When running Laravel with an SQLite database file (`database/database.sqlite`) on a VPS, executing `php artisan optimize` or `php artisan config:cache` serializes configurations into `bootstrap/cache/config.php`.
Subsequent test execution (`php artisan test`) with PHPUnit's `RefreshDatabase` trait loads the cached production database path instead of the in-memory `:memory:` database specified in `phpunit.xml`.
This causes `migrate:fresh` to wipe the production SQLite file, destroying user accounts, reports, and uploaded records.

## 2. Triple-Layer Prevention Architecture

### Layer 1: Test Environment Hard Kill-Switch (`tests/TestCase.php`)
```php
namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    protected function setUp(): void
    {
        parent::setUp();

        $db = config('database.connections.sqlite.database');
        if (config('database.default') === 'sqlite' && $db !== ':memory:' && ! str_ends_with((string) $db, ':memory:')) {
            throw new \RuntimeException("BAHAYA: Pengujian dilarang berjalan pada database fisik ({$db})! Hapus cache config terlebih dahulu.");
        }
    }
}
```

### Layer 2: Laravel Destructive Command Blocker (`app/Providers/AppServiceProvider.php`)
```php
use Illuminate\Support\Facades\DB;

public function boot(): void
{
    DB::prohibitDestructiveCommands($this->app->isProduction());
}
```

### Layer 3: Automated Hourly Backup Script & Crontab
Script path: `/home/ubuntu/backups/backup-pwa-bruder.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/home/ubuntu/backups/pwa-bruder-muda"
PROJECT_DIR="/home/ubuntu/PWA_Bruder-Muda"
DB_FILE="${PROJECT_DIR}/database/database.sqlite"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "${BACKUP_DIR}/daily"
mkdir -p "${BACKUP_DIR}/hourly"

if [ -f "${DB_FILE}" ]; then
    cp "${DB_FILE}" "${BACKUP_DIR}/hourly/database_${TIMESTAMP}.sqlite"
    cp "${DB_FILE}" "${BACKUP_DIR}/database_latest.sqlite"
    
    DAY_STAMP=$(date +"%Y%m%d")
    if [ ! -f "${BACKUP_DIR}/daily/database_${DAY_STAMP}.sqlite" ]; then
        cp "${DB_FILE}" "${BACKUP_DIR}/daily/database_${DAY_STAMP}.sqlite"
    fi
fi

# Retention: 48 hours for hourly backups, 30 days for daily backups
find "${BACKUP_DIR}/hourly" -name "database_*.sqlite" -type f -mmin +2880 -delete 2>/dev/null || true
find "${BACKUP_DIR}/daily" -name "database_*.sqlite" -type f -mtime +30 -delete 2>/dev/null || true
```

Crontab entry:
```cron
0 * * * * /home/ubuntu/backups/backup-pwa-bruder.sh > /dev/null 2>&1
```

## 3. Recovery Procedure
If the production database is ever corrupted or emptied:
1. Stop the application server: `kill $(pgrep -f "artisan serve")`
2. Inspect latest backup: `ls -lh /home/ubuntu/backups/pwa-bruder-muda/hourly/`
3. Restore from latest snapshot:
   ```bash
   cp /home/ubuntu/backups/pwa-bruder-muda/database_latest.sqlite /home/ubuntu/PWA_Bruder-Muda/database/database.sqlite
   ```
4. Verify integrity:
   ```bash
   python3 -c "import sqlite3; conn = sqlite3.connect('/home/ubuntu/PWA_Bruder-Muda/database/database.sqlite'); print('Users:', conn.cursor().execute('SELECT count(*) FROM users').fetchone()[0])"
   ```
5. Restart application service:
   ```bash
   cd /home/ubuntu/PWA_Bruder-Muda && php artisan serve --host=127.0.0.1 --port=8022
   ```
