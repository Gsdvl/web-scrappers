import argparse
import os
import time
from datetime import datetime
import pandas as pd
import requests

API_URL = "https://www.tabnews.com.br/api/v1"


def parse_arguments():
    """Configura e le os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Scraper de posts e comentarios do TabNews."
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=50,
        help="Quantidade de paginas para raspar (padrao: 50)"
    )
    parser.add_argument(
        "-n", "--per-page",
        type=int,
        default=100,
        help="Quantidade de itens por pagina (padrao: 100)"
    )
    return parser.parse_args()


def request_with_retry(url: str, params: dict = None, max_retries: int = 3):
    """Executa a requisicao tratando rate-limiting (429)."""
    for tentativa in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                tempo_espera = (tentativa + 1) * 1.5
                print(f"Rate limit em {url}. Pausando por {tempo_espera}s...")
                time.sleep(tempo_espera)
            else:
                return response
        except requests.RequestException as exc:
            print(f"Erro de rede em {url}: {exc}")
            time.sleep(1)
    return None


def fetch_api_data(endpoint: str, params: dict = None, errors_log: list = None):
    """Auxiliar generico para requisicoes na API."""
    url = f"{API_URL}/{endpoint}"
    response = request_with_retry(url, params=params)

    if response and response.status_code == 200:
        return response.json()

    status = response.status_code if response else "Sem resposta"
    error_msg = f"Erro em {endpoint}: Status {status}"
    print(error_msg)
    if errors_log is not None:
        errors_log.append(error_msg)
    return None


def scrape_all_data(num_pages: int, per_page: int, errors_log: list):
    """Coleta o conteudo bruto das paginas, posts e comentarios."""
    raw_posts = []
    raw_comments = []

    print(f"Iniciando coleta de {num_pages} paginas ({per_page} itens/pagina)...")

    for page in range(1, num_pages + 1):
        params = {"page": page, "per_page": per_page, "strategy": "new"}
        page_items = fetch_api_data("contents", params, errors_log)

        if not page_items:
            print(f"Interrompendo coleta na pagina {page}.")
            break

        for item in page_items:
            username = item.get("owner_username")
            slug = item.get("slug")

            post_body = fetch_api_data(f"contents/{username}/{slug}", errors_log=errors_log)
            if post_body:
                raw_posts.append(post_body)

            comments = fetch_api_data(f"contents/{username}/{slug}/children", errors_log=errors_log)
            if comments and isinstance(comments, list):
                raw_comments.extend(comments)

    return raw_posts, raw_comments


def process_data(raw_posts: list, raw_comments: list):
    """Transforma os dados brutos nos DataFrames finais."""
    users = []
    posts = []
    comments = []

    for item in raw_posts:
        if not isinstance(item, dict):
            continue

        users.append({
            "user_id": item.get("owner_id"),
            "username": item.get("owner_username")
        })

        posts.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "body": item.get("body"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "published_at": item.get("published_at"),
            "user_id": item.get("owner_id"),
            "tabcoins": item.get("tabcoins")
        })

    for item in raw_comments:
        if not isinstance(item, dict):
            continue

        comments.append({
            "id": item.get("id"),
            "user_id": item.get("owner_id"),
            "post_id": item.get("parent_id"),
            "body": item.get("body")
        })

    users_df = pd.DataFrame(users).drop_duplicates(subset=["user_id"])
    posts_df = pd.DataFrame(posts).drop_duplicates(subset=["id"])
    comments_df = pd.DataFrame(comments).drop_duplicates(subset=["id"])

    return users_df, posts_df, comments_df


def save_results(users_df, posts_df, comments_df, errors_log):
    """Cria os diretorios e exporta os arquivos CSV e logs."""
    output_dir = "outputs/csv_data"
    os.makedirs(output_dir, exist_ok=True)

    users_df.to_csv(f"{output_dir}/users_data.csv", index=False, encoding="utf-8")
    posts_df.to_csv(f"{output_dir}/posts_data.csv", index=False, encoding="utf-8")
    comments_df.to_csv(f"{output_dir}/comments_data.csv", index=False, encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"outputs/scrapping-errors-report-{timestamp}.txt", "w", encoding="utf-8") as f:
        for line in errors_log:
            f.write(f"{line}\n")

    print("\nColeta concluida com sucesso.")
    print(f"Usuarios unicos: {len(users_df)}")
    print(f"Posts unicos: {len(posts_df)}")
    print(f"Comentarios unicos: {len(comments_df)}")


def main():
    args = parse_arguments()
    errors_log = []

    raw_posts, raw_comments = scrape_all_data(
        num_pages=args.pages,
        per_page=args.per_page,
        errors_log=errors_log
    )

    users_df, posts_df, comments_df = process_data(raw_posts, raw_comments)
    save_results(users_df, posts_df, comments_df, errors_log)


if __name__ == "__main__":
    main()