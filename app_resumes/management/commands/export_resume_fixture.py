import os
from django.core.management.base import BaseCommand
from django.core import serializers
from app_resumes.models import Resume


class Command(BaseCommand):
    help = "Экспорт резюме в JSON-фикстуру"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="resume_fixture.json",
            help="Имя файла для сохранения фикстуры (по умолчанию: resume_fixture.json)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Ограничить количество экспортируемых записей",
        )

    def handle(self, *args, **options):
        output_file = options.get("output")
        limit = options.get("limit")

        if limit:
            resumes = Resume.objects.all()[:limit]
            self.stdout.write(f"Экспорт {limit} резюме в {output_file}")
        else:
            resumes = Resume.objects.all()
            self.stdout.write(f"Экспорт всех резюме ({resumes.count()} шт.) в {output_file}")

        # Экспорт данных в формат JSON
        data = serializers.serialize("json", resumes, indent=4)

        # Запись в файл
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(data)

        self.stdout.write(self.style.SUCCESS(f"Успешно экспортировано {len(resumes)} резюме в {output_file}"))
