# Mãos na Obra

## Execução local

1. Criar e ativar o ambiente virtual.
2. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Aplicar migrations:
   ```bash
   python manage.py migrate
   ```
4. Criar superusuário:
   ```bash
   python manage.py createsuperuser
   ```
5. Rodar o servidor:
   ```bash
   python manage.py runserver
   ```
6. Acessar o sistema em `http://127.0.0.1:8000/`.

Fluxo básico:
- Página pública em `/`
- Login em `/conta/login/`
- Painel em `/dashboard/`
- Admin em `/admin/`

## Docker

1. Subir os serviços:
   ```bash
   docker compose up --build
   ```
2. Em outra janela, aplicar migrations se necessário:
   ```bash
   docker compose exec web python manage.py migrate
   ```
3. Criar superusuário:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

O container usa SQLite local e mantém a estrutura do projeto sem adicionar banco externo.
