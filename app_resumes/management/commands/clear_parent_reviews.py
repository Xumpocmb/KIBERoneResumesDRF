import os
from django.core.management.base import BaseCommand
from app_resumes.models import ParentReview


class Command(BaseCommand):
    help = "Удаление всех отзывов родителей из базы данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Подтвердить удаление всех отзывов родителей",
        )

    def handle(self, *args, **options):
        confirm = options.get("confirm", False)

        review_count = ParentReview.objects.count()

        self.stdout.write(f"Найдено {review_count} отзывов родителей в базе данных")

        if not confirm:
            self.stdout.write(self.style.WARNING("Для выполнения удаления используйте флаг --confirm"))
            return

        if review_count == 0:
            self.stdout.write(self.style.WARNING("Нет отзывов для удаления"))
            return

        ParentReview.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f"Успешно удалено {review_count} отзывов родителей из базы данных"))
