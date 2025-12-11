import os
from django.core.management.base import BaseCommand
from app_resumes.models import Resume


class Command(BaseCommand):
    help = "Удаление всех резюме из базы данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Подтвердить удаление всех резюме",
        )

    def handle(self, *args, **options):
        confirm = options.get("confirm", False)

        resume_count = Resume.objects.count()

        self.stdout.write(f"Найдено {resume_count} резюме в базе данных")

        if not confirm:
            self.stdout.write(self.style.WARNING("Для выполнения удаления используйте флаг --confirm"))
            return

        if resume_count == 0:
            self.stdout.write(self.style.WARNING("Нет резюме для удаления"))
            return

        Resume.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Успешно удалено {resume_count} резюме из базы данных"))
