# X Clone — Rede Social Monolítica & RESTful (Django + DRF + PostgreSQL + Bootstrap 5)

Bem-vindo à documentação técnica e guia de arquitetura do **X Clone**. Este projeto implementa uma réplica de alta fidelidade (~90% da interface desktop atual do X) utilizando **Python**, **Django 5**, **Django REST Framework (DRF)**, **PostgreSQL**, **Templates Django Monolíticos** com **Bootstrap 5.3** e gerência de dependências via **Poetry**.

---

## 1. Visão Geral da Arquitetura e Paradigmas OOP (DRY)

O projeto foi desenhado aplicando rigorosamente **Programação Orientada a Objetos (OOP)** e o princípio **DRY (*Don't Repeat Yourself*)**:

1. **Herança e Polimorfismo em Models (`TimeStampedModel`)**:
   - Todos os modelos do sistema (`CustomUser`, `Follow`, `Post`, `Like`, `Comment`) herdam de `apps.core.models.TimeStampedModel`, compartilhando chave primária `UUIDField` (prevenindo *ID Enumeration Attacks*) e auditoria automática (`created_at`, `updated_at`).
2. **Encapsulamento de Regras de Domínio em Managers e QuerySets**:
   - `CustomUserManager`: centraliza a normalização de `@username` e `email`, validação e hash seguro de senhas (`set_password`).
   - `PostQuerySet`: implementa `.with_interaction_metrics(user)` (eliminando o problema de *N+1 queries* via `select_related`, `prefetch_related`, `Count` e `Exists`) e `.following_feed_for(user)`, garantindo no nível do ORM que **o feed de notícias exiba exclusivamente postagens de contas seguidas**.
3. **Composição em Serializers e ViewSets**:
   - `ProfileUpdateSerializer`: permite atualização parcial (`PATCH`) onde `display_name`, `avatar`, `bio` e `new_password` possuem `required=False`, garantindo que **nenhuma alteração seja obrigatória**.
   - `IsAuthorOrReadOnly`: permissão reutilizável que protege mutações e exclusões em todo o ecossistema REST.

---

## 2. Desenho Conceitual dos Modelos (Backend MER / DER)

```
+-------------------------------------------------------------------------+
|                     apps.core.models.TimeStampedModel                   |
|                              <<abstract>>                               |
+-------------------------------------------------------------------------+
| + id: UUIDField (PK, default=uuid4)                                     |
| + created_at: DateTimeField (auto_now_add=True, indexed)                |
| + updated_at: DateTimeField (auto_now=True)                             |
+-------------------------------------------------------------------------+
       ^                           ^                          ^
       | herda                     | herda                    | herda
       |                           |                          |
+-------------------------------+  |  +-----------------------------------+
|   accounts.CustomUser         |  |  |           posts.Post              |
+-------------------------------+  |  +-----------------------------------+
| + username: CharField (UNQ)   |  |  | + author: FK(CustomUser)          |
| + email: EmailField (UNQ)     |  |  | + content: CharField(280)         |
| + display_name: CharField(80) |  |  | + image: ImageField (nullable)    |
| + bio: CharField(160)         |  |  +-----------------------------------+
| + avatar: ImageField(null)    |  |  | + toggle_like(user): (bool, int)  |
| + password: CharField(Hash)   |  |  +-----------------------------------+
+-------------------------------+  |            | 1                | 1
| + follow(target_user)         |  |            |                  |
| + unfollow(target_user)       |  |            | 0..*             | 0..*
| + is_following(target_user)   |  |  +--------------------+  +-----------------------+
+-------------------------------+  |  |     posts.Like     |  |     posts.Comment     |
       | 1             | 1         |  +--------------------+  +-----------------------+
       | follower      | following |  | + user: FK(User)   |  | + post: FK(Post)      |
       | 0..*          | 0..*      |  | + post: FK(Post)   |  | + author: FK(User)    |
+-------------------------------+  |  | [UNQ(user, post)]  |  | + content: Char(280)  |
|        accounts.Follow        |--+  +--------------------+  +-----------------------+
+-------------------------------+
| + follower: FK(CustomUser)    |
| + following: FK(CustomUser)   |
| [UNQ(follower, following)]    |
| [CHK(follower != following)]  |
+-------------------------------+
```

---

## 3. Estrutura de Diretórios do Projeto

```text
x_clone/
├── pyproject.toml                  # Orquestração de dependências e scripts pelo Poetry
├── .env.example                    # Variáveis de ambiente (PostgreSQL, Secret Key, Debug)
├── Dockerfile                      # Containerização de produção com Python 3.11 + Gunicorn
├── docker-compose.yml              # Orquestração local/produção: Web (Django) + DB (PostgreSQL 16)
├── manage.py                       # Entrypoint CLI do Django
├── README.md                       # Documentação completa de arquitetura, API, testes e deploy
├── config/                         # Configurações globais do projeto
│   ├── __init__.py
│   ├── settings.py                 # Configuração PostgreSQL, DRF, SimpleJWT, Segurança e Apps
│   ├── urls.py                     # Roteamento unificado: API REST (/api/v1/) + Web Monolítica (/)
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/                       # Módulo base DRY (sem repetição de código)
│   │   ├── models.py               # TimeStampedModel (UUID PK + created_at + updated_at)
│   │   ├── permissions.py          # IsAuthorOrReadOnly
│   │   └── validators.py           # Validação segura de tamanho (<=5MB) e extensão de imagens
│   ├── accounts/                   # Domínio de Autenticação, Perfil e Grafo Social
│   │   ├── managers.py             # CustomUserManager orientado a objetos
│   │   ├── models.py               # CustomUser e Follow (com UniqueConstraint e CheckConstraint)
│   │   ├── serializers.py          # UserRegistrationSerializer, ProfileUpdateSerializer, UserPublicSerializer
│   │   ├── views.py                # RegisterAPIView, SessionLoginAPIView, UserViewSet (/me, /follow, /followers, /following)
│   │   ├── urls.py
│   │   └── tests.py                # Testes de cadastro, login, perfil opcional e relacionamentos
│   ├── posts/                      # Domínio de Postagens, Feed de Seguidos e Interações
│   │   ├── querysets.py            # PostQuerySet (.following_feed_for e .with_interaction_metrics)
│   │   ├── models.py               # Post, Like e Comment
│   │   ├── serializers.py          # PostSerializer e CommentSerializer
│   │   ├── views.py                # PostViewSet (/feed, /like, /comments)
│   │   └── tests.py                # Testes do filtro estrito do feed, curtidas, comentários e permissões
│   └── web/                        # Frontend Monolítico com Class-Based Views
│       ├── views.py                # AuthPageView, HomeFeedView, UserProfileView
│       ├── urls.py
│       └── tests.py                # Testes de renderização dos templates Django + Bootstrap 5
├── templates/                      # Templates Django Monolíticos (90%+ fidelidade ao X Desktop)
│   ├── base.html                   # Layout em 3 colunas do X Desktop (Sidebar, Feed 600px, Right Rail)
│   ├── auth/
│   │   └── login_register.html     # Tela de Login e Cadastro
│   ├── feed/
│   │   └── index.html              # Timeline de Seguidos e Composer de Postagem
│   ├── profile/
│   │   └── detail.html             # Página de Perfil com abas Postagens, Seguidores e Seguindo
│   └── partials/
│       ├── post_card.html          # Componente reutilizável de Postagem (Curtir e Comentar)
│       └── edit_profile_modal.html # Modal de Edição Opcional (Foto, Nome, Bio, Senha)
└── static/
    ├── css/
    │   └── x_theme.css             # Variáveis e classes customizadas do tema escuro (#000000 / #1d9bf0)
    └── js/
        └── app.js                  # Cliente JS orientado a objetos (XCloneApiClient) com CSRF
```

---

## 4. Endpoints da API REST (`/api/v1/`)

| Método | Endpoint | Descrição | Autenticação |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register/` | Cria uma nova conta de usuário com validação de senha | Pública |
| `POST` | `/api/v1/auth/login/` | Autentica usuário via sessão segura (CSRF) | Pública |
| `POST` | `/api/v1/auth/logout/` | Encerra a sessão ativa | Autenticado |
| `POST` | `/api/v1/token/` | Obtém par de tokens JWT (`access` e `refresh`) | Pública |
| `GET` | `/api/v1/users/me/` | Retorna os dados do perfil autenticado | Autenticado |
| `PATCH` | `/api/v1/users/me/` | Atualiza opcionalmente foto (`avatar`), `display_name`, `bio` ou `new_password` | Autenticado |
| `POST` | `/api/v1/users/<username>/follow/` | Passa a seguir `@username` | Autenticado |
| `DELETE` | `/api/v1/users/<username>/follow/` | Deixa de seguir `@username` | Autenticado |
| `GET` | `/api/v1/users/<username>/followers/` | Lista todos os seguidores de `@username` | Autenticado |
| `GET` | `/api/v1/users/<username>/following/` | Lista todas as contas que `@username` segue | Autenticado |
| `GET` | `/api/v1/posts/feed/` | **Feed de Notícias**: retorna postagens apenas das contas seguidas | Autenticado |
| `POST` | `/api/v1/posts/` | Cria uma nova postagem (até 280 caracteres + imagem opcional) | Autenticado |
| `POST` | `/api/v1/posts/<uuid>/like/` | Alterna curtida (*like/unlike*) na postagem | Autenticado |
| `GET/POST` | `/api/v1/posts/<uuid>/comments/` | Lista ou publica um comentário na postagem | Autenticado |

---

## 5. Como Executar Localmente com Poetry e PostgreSQL

```bash
# 1. Clone o repositório e acesse a pasta
cd x_clone

# 2. Copie o arquivo de variáveis de ambiente
cp .env.example .env

# 3. Instale as dependências com o Poetry
poetry install

# 4. Suba o banco PostgreSQL (via Docker ou instância local) e aplique as migrações
poetry run python manage.py makemigrations
poetry run python manage.py migrate

# 5. Execute a suíte completa de testes (Backend + Frontend com cobertura)
poetry run pytest

# 6. Inicie o servidor de desenvolvimento
poetry run python manage.py runserver
```

---

## 6. Estratégias e Propostas de Deploy em Produção

1. **Containerização Padronizada (Docker + Gunicorn + Nginx/WhiteNoise)**:
   - O projeto já inclui `Dockerfile` e `docker-compose.yml` prontos para produção utilizando `python:3.11-slim`, `poetry` e `gunicorn` com 3 workers WSGI.
2. **PaaS Modernas (Render, Railway ou Fly.io) — Recomendado para MVP Ágil**:
   - Conecte o repositório Git diretamente ao **Render** ou **Railway**, provisionando um banco gerenciado **PostgreSQL 16** com backups diários e variáveis `DATABASE_URL` e `SECRET_KEY` injetadas no ambiente.
3. **Arquitetura Cloud Escalável (AWS ECS/Fargate ou GCP Cloud Run)**:
   - **Compute**: Imagens Docker executadas em **Google Cloud Run** ou **AWS ECS Fargate** com auto-scaling horizontal baseado em CPU/requisições.
   - **Banco de Dados**: **Amazon RDS for PostgreSQL** ou **Cloud SQL** em sub-rede privada com *Connection Pooling* via **PgBouncer**.
   - **Arquivos Estáticos e Mídia (Avatares e Imagens de Posts)**: Estáticos servidos via **WhiteNoise / CloudFront CDN** e uploads de mídia (`MEDIA_ROOT`) armazenados em **Amazon S3** ou **Cloudflare R2** usando `django-storages`.
   - **CI/CD**: Pipeline no **GitHub Actions** executando `poetry run ruff check .` e `poetry run pytest` a cada Pull Request antes do deploy automático.
