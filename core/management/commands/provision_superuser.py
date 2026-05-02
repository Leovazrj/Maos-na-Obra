from django.core.management.base import BaseCommand

from accounts.models import User

DEFAULT_SUPERUSER_EMAIL = 'leovazrj@gmail.com'
DEFAULT_SUPERUSER_NAME = 'leovazrj'


class Command(BaseCommand):
    help = 'Cria ou atualiza um superusuário a partir de variáveis de ambiente.'

    def handle(self, *args, **options):
        email = DEFAULT_SUPERUSER_EMAIL
        name = DEFAULT_SUPERUSER_NAME

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            self.stdout.write(f'Nenhum usuário encontrado com o e-mail {email}. Ignorando.')
            return

        updated = False
        if user.name != name:
            user.name = name
            updated = True
        if user.is_active is not True:
            user.is_active = True
            updated = True
        if user.is_staff is not True:
            user.is_staff = True
            updated = True
        if user.is_superuser is not True:
            user.is_superuser = True
            updated = True

        if updated:
            user.save(update_fields=['name', 'is_active', 'is_staff', 'is_superuser'])

        self.stdout.write(
            self.style.SUCCESS(f'Superusuário promovido: {user.email}')
        )
