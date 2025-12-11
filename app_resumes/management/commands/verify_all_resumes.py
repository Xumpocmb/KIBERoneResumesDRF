import os
from django.core.management.base import BaseCommand
from app_resumes.models import Resume


class Command(BaseCommand):
    help = "Отмечает все резюме как проверенные"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать что будет обновлено без сохранения в БД",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        # Получаем все резюме
        all_resumes = Resume.objects.all()

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Пробный запуск: будет отмечено как проверенных {all_resumes.count()} резюме"))
        else:
            # Обновляем все резюме, устанавливая is_verified = True
            updated_count = all_resumes.update(is_verified=True)

            self.stdout.write(self.style.SUCCESS(f"Успешно отмечено как проверенных {updated_count} резюме!"))
