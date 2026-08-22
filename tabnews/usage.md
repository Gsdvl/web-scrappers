# Documentação do Script

## Dados Coletados

* **Usuários:** 
  * `user_id`: Identificador único do usuário.
  * `username`: Nome de usuário.

* **Posts:** 
  * `id`: Identificador único do post.
  * `title`: Título da publicação.
  * `body`: Conteúdo/texto do post.
  * `created_at` / `updated_at` / `published_at`: Datas de criação, atualização e publicação.
  * `user_id`: ID do autor.
  * `tabcoins`: Pontuação/reputação do post.

* **Comentários:** 
  * `id`: Identificador único do comentário.
  * `user_id`: ID de quem comentou.
  * `post_id`: ID do post que recebeu o comentário (`parent_id`).
  * `body`: Texto do comentário.

## Funcionamento do argparse

O `argparse` permite configurar parâmetros diretamente pelo terminal ao executar o script:
* `-p` / `--pages`: Quantidade de páginas a serem coletadas (padrão: 50).
* `-n` / `--per-page`: Quantidade de itens por página (padrão: 100).

Exemplo de uso: `python script.py -p 10 -n 50`
"""
